import os
from collections.abc import Callable
from typing import Any

import httpx

from app.adapters.discovery.ashby import normalize_ashby
from app.adapters.discovery.greenhouse import normalize_greenhouse
from app.adapters.discovery.lever import normalize_lever
from app.domain.schemas import DiscoveryScanRequest, JobPostingIn


class DiscoveryError(RuntimeError):
    pass


URL_BUILDERS: dict[str, Callable[[str], str]] = {
    "greenhouse": lambda board: f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true",
    "lever": lambda board: f"https://api.lever.co/v0/postings/{board}?mode=json",
    "ashby": lambda board: f"https://api.ashbyhq.com/posting-api/job-board/{board}",
}


def _normalize(request: DiscoveryScanRequest, payload: Any) -> list[JobPostingIn]:
    company = request.company or request.board
    if request.source == "greenhouse":
        if not isinstance(payload, dict):
            raise DiscoveryError("Greenhouse returned a non-object payload")
        jobs = normalize_greenhouse(payload, company)
    elif request.source == "lever":
        if not isinstance(payload, list):
            raise DiscoveryError("Lever returned a non-list payload")
        jobs = normalize_lever(payload, company)
    else:
        if not isinstance(payload, dict):
            raise DiscoveryError("Ashby returned a non-object payload")
        jobs = normalize_ashby(payload, company)
    return jobs


def fetch_jobs(
    request: DiscoveryScanRequest,
    *,
    transport: httpx.BaseTransport | None = None,
) -> list[JobPostingIn]:
    timeout = float(os.getenv("DISCOVERY_TIMEOUT_SECONDS", "20"))
    url = URL_BUILDERS[request.source](request.board)
    try:
        with httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            transport=transport,
            headers={"User-Agent": "JobSniffing/0.2 (+local job discovery)"},
        ) as client:
            response = client.get(url)
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise DiscoveryError(f"{request.source} discovery failed: {exc}") from exc
    try:
        return _normalize(request, payload)
    except (ValueError, TypeError) as exc:
        raise DiscoveryError(f"{request.source} payload could not be normalized: {exc}") from exc
