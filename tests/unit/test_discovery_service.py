import httpx

from app.domain.schemas import DiscoveryScanRequest
from app.services.discovery_service import DiscoveryError, fetch_jobs


def test_greenhouse_discovery_uses_official_shape():
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).startswith("https://boards-api.greenhouse.io/")
        return httpx.Response(
            200,
            json={
                "jobs": [
                    {
                        "id": 7,
                        "title": "Python Engineer",
                        "absolute_url": "https://example.com/7",
                        "location": {"name": "Remote"},
                        "content": "FastAPI",
                    }
                ]
            },
        )

    [job] = fetch_jobs(
        DiscoveryScanRequest(source="greenhouse", board="example"),
        transport=httpx.MockTransport(handler),
    )
    assert job.external_id == "7"


def test_discovery_wraps_http_errors():
    transport = httpx.MockTransport(lambda request: httpx.Response(500))
    try:
        fetch_jobs(
            DiscoveryScanRequest(source="lever", board="example"),
            transport=transport,
        )
    except DiscoveryError as exc:
        assert "lever discovery failed" in str(exc)
    else:
        raise AssertionError("Expected DiscoveryError")
