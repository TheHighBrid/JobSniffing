import json
from pathlib import Path
from app.adapters.discovery.ashby import normalize_ashby
from app.adapters.discovery.greenhouse import normalize_greenhouse
from app.adapters.discovery.lever import normalize_lever

FIXTURES = Path(__file__).parents[1] / "fixtures" / "ats"


def test_greenhouse_fixture_normalizes_to_contract():
    payload = json.loads((FIXTURES / "greenhouse" / "jobs.json").read_text())
    [job] = normalize_greenhouse(payload, "example")
    assert job.source == "greenhouse"
    assert job.external_id == "101"
    assert job.apply_url


def test_lever_fixture_normalizes_to_contract():
    payload = json.loads((FIXTURES / "lever" / "postings.json").read_text())
    [job] = normalize_lever(payload, "example")
    assert job.source == "lever"
    assert job.location == "Remote"


def test_ashby_fixture_normalizes_to_contract():
    payload = json.loads((FIXTURES / "ashby" / "jobs.json").read_text())
    [job] = normalize_ashby(payload, "example")
    assert job.source == "ashby"
    assert "FastAPI" in job.title
