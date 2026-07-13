import json
from pathlib import Path
from app.adapters.discovery.ashby import normalize_ashby
from app.adapters.discovery.greenhouse import normalize_greenhouse
from app.adapters.discovery.lever import normalize_lever

FIXTURES = Path(__file__).parents[1] / "fixtures" / "ats"


def test_greenhouse_contract():
    [job] = normalize_greenhouse(json.loads((FIXTURES / "greenhouse/jobs.json").read_text()), "example")
    assert job.source == "greenhouse" and job.external_id == "101" and "<p>" not in job.description


def test_lever_contract():
    [job] = normalize_lever(json.loads((FIXTURES / "lever/postings.json").read_text()), "Example")
    assert job.source == "lever" and job.location == "Remote Canada"


def test_ashby_contract():
    [job] = normalize_ashby(json.loads((FIXTURES / "ashby/jobs.json").read_text()), "Example")
    assert job.source == "ashby" and "AML" in job.title
