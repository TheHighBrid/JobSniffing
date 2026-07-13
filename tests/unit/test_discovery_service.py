import pytest
from app.domain.schemas import DiscoveryRequest
from app.services.discovery_service import DiscoveryError, discover, provider_request


def test_provider_url_is_fixed():
    url, params = provider_request(DiscoveryRequest(provider="greenhouse", identifier="example-board"))
    assert url == "https://boards-api.greenhouse.io/v1/boards/example-board/jobs"
    assert params == {"content": "true"}


def test_invalid_identifier_rejected_before_network():
    with pytest.raises(DiscoveryError):
        provider_request(DiscoveryRequest(provider="lever", identifier="https://evil.example/path"))


def test_discover_filters_without_network():
    payload = [
        {"id":"1","text":"Fraud Analyst","categories":{"location":"Remote Canada"},"hostedUrl":"https://example.com/1","descriptionPlain":"AML"},
        {"id":"2","text":"Designer","categories":{"location":"Montreal"},"hostedUrl":"https://example.com/2","descriptionPlain":"Brand"},
    ]
    request = DiscoveryRequest(provider="lever", identifier="example", query="fraud", location="Remote")
    assert [job.external_id for job in discover(request, fetcher=lambda _u, _p: payload)] == ["1"]
