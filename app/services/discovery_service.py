from __future__ import annotations

import re
from collections.abc import Callable
from urllib.parse import quote

import httpx

from app.adapters.discovery.ashby import normalize_ashby
from app.adapters.discovery.greenhouse import normalize_greenhouse
from app.adapters.discovery.lever import normalize_lever
from app.domain.schemas import DiscoveryRequest, JobPostingIn

FetchJson = Callable[[str, dict[str, str] | None], object]
_IDENTIFIER = re.compile(r"^[A-Za-z0-9_-]+$")


class DiscoveryError(RuntimeError):
    pass


def fetch_json(url: str, params: dict[str, str] | None = None) -> object:
    try:
        with httpx.Client(
            timeout=20,
            follow_redirects=True,
            headers={"User-Agent": "JobSniffing/0.2"},
        ) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            if len(response.content) > 10_000_000:
                raise DiscoveryError("Provider response exceeded 10 MB")
            return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise DiscoveryError(f"Discovery request failed: {exc}") from exc


def provider_request(request: DiscoveryRequest) -> tuple[str, dict[str, str] | None]:
    identifier = request.identifier.strip()
    if not _IDENTIFIER.fullmatch(identifier):
        raise DiscoveryError(
            "identifier may contain only letters, numbers, underscores, and hyphens"
        )
    identifier = quote(identifier, safe="")
    if request.provider == "greenhouse":
        return (
            f"https://boards-api.greenhouse.io/v1/boards/{identifier}/jobs",
            {"content": "true"},
        )
    if request.provider == "lever":
        return f"https://api.lever.co/v0/postings/{identifier}", {"mode": "json"}
    return f"https://api.ashbyhq.com/posting-api/job-board/{identifier}", None


def discover(
    request: DiscoveryRequest,
    fetcher: FetchJson = fetch_json,
) -> list[JobPostingIn]:
    url, params = provider_request(request)
    payload = fetcher(url, params)
    company = request.company or request.identifier
    try:
        if request.provider == "greenhouse" and isinstance(payload, dict):
            jobs = normalize_greenhouse(payload, request.identifier, company)
        elif request.provider == "lever" and isinstance(payload, list):
            jobs = normalize_lever(payload, company)
        elif request.provider == "ashby" and isinstance(payload, dict):
            jobs = normalize_ashby(payload, company)
        else:
            raise DiscoveryError(f"{request.provider} returned an unexpected payload")
    except (KeyError, TypeError, ValueError) as exc:
        raise DiscoveryError(
            f"{request.provider} returned an invalid payload: {exc}"
        ) from exc

    query = request.query.strip().lower()
    location = request.location.strip().lower()
    result: list[JobPostingIn] = []
    for job in jobs:
        if query and query not in f"{job.title} {job.company} {job.description}".lower():
            continue
        if location and location not in job.location.lower():
            continue
        result.append(job)
        if len(result) >= request.limit:
            break
    return result
