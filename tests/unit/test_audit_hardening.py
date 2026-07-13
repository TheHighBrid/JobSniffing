import pytest

from app.adapters.discovery.ashby import normalize_ashby
from app.adapters.discovery.greenhouse import normalize_greenhouse
from app.adapters.discovery.lever import normalize_lever
from app.db.sqlite import init_db, session
from app.domain.enums import ApplicationStatus
from app.domain.schemas import DiscoveryRequest, JobPostingIn, ScoringSettings
from app.services.discovery_service import DiscoveryError, discover
from app.services.settings_service import save_scoring_settings
from app.services.tracking_service import change_status, get_job, rescore_all, upsert_job


def make_job(company: str = "Example Bank") -> JobPostingIn:
    return JobPostingIn(
        source="manual",
        external_id="1",
        title="Fraud Analyst",
        company=company,
        location="Ottawa",
        apply_url="https://example.com/apply",
        description="AML KYC compliance",
    )


def blacklist_settings() -> ScoringSettings:
    return ScoringSettings(
        preferred_terms={"fraud": 20},
        excluded_terms=[],
        blacklisted_companies=["example bank"],
        minimum_score=0,
    )


def test_rescore_applies_new_company_blacklist(tmp_path):
    path = tmp_path / "db.sqlite3"
    init_db(path)
    with session(path) as conn:
        job_id = upsert_job(conn, make_job())
        settings = blacklist_settings()
        save_scoring_settings(conn, settings)
        assert rescore_all(conn, settings) == 1
        assert get_job(conn, job_id)["status"] == ApplicationStatus.BLOCKED.value


def test_duplicate_upsert_applies_blacklist_without_resetting_submitted(tmp_path):
    path = tmp_path / "db.sqlite3"
    init_db(path)
    with session(path) as conn:
        job_id = upsert_job(conn, make_job())
        assert upsert_job(conn, make_job(), blacklist_settings()) == job_id
        assert get_job(conn, job_id)["status"] == ApplicationStatus.BLOCKED.value

    path2 = tmp_path / "submitted.sqlite3"
    init_db(path2)
    with session(path2) as conn:
        job_id = upsert_job(conn, make_job())
        change_status(conn, job_id, ApplicationStatus.SHORTLISTED)
        change_status(conn, job_id, ApplicationStatus.APPROVED)
        change_status(conn, job_id, ApplicationStatus.QUEUED)
        change_status(conn, job_id, ApplicationStatus.FILLING)
        change_status(conn, job_id, ApplicationStatus.SUBMITTED)
        rescore_all(conn, blacklist_settings())
        assert get_job(conn, job_id)["status"] == ApplicationStatus.SUBMITTED.value


def test_adapters_skip_malformed_entries_and_keep_valid_entries():
    greenhouse = normalize_greenhouse(
        {
            "jobs": [
                {"title": "Missing ID", "absolute_url": "https://example.com/missing"},
                {"id": 2, "title": "Bad URL", "absolute_url": "not-a-url"},
                {"id": 3, "title": "Valid", "absolute_url": "https://example.com/3"},
            ]
        },
        "example",
    )
    lever = normalize_lever(
        [
            {"text": "Missing ID", "hostedUrl": "https://example.com/missing"},
            {"id": "2", "text": "Bad URL", "hostedUrl": "not-a-url"},
            {"id": "3", "text": "Valid", "hostedUrl": "https://example.com/3"},
        ],
        "Example",
    )
    ashby = normalize_ashby(
        {
            "jobs": [
                {"title": "Missing ID", "jobUrl": "https://example.com/missing"},
                {"id": "2", "title": "Bad URL", "jobUrl": "not-a-url"},
                {"id": "3", "title": "Valid", "jobUrl": "https://example.com/3"},
            ]
        },
        "Example",
    )
    assert [job.external_id for job in greenhouse] == ["3"]
    assert [job.external_id for job in lever] == ["3"]
    assert [job.external_id for job in ashby] == ["3"]


def test_invalid_provider_shape_is_wrapped_as_discovery_error():
    request = DiscoveryRequest(provider="greenhouse", identifier="example")
    with pytest.raises(DiscoveryError, match="invalid payload"):
        discover(request, fetcher=lambda _url, _params: {"jobs": "not-a-list"})
