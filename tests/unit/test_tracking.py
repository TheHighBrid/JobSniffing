from app.db.sqlite import init_db, session
from app.domain.enums import ApplicationStatus
from app.domain.schemas import JobPostingIn, ScoringSettings
from app.services.settings_service import save_scoring_settings
from app.services.tracking_service import change_status, list_jobs, rescore_all, upsert_job


def make_job(external_id="1", title="Fraud Analyst"):
    return JobPostingIn(source="manual", external_id=external_id, title=title, company="Example Bank", location="Ottawa", apply_url=f"https://example.com/{external_id}", description="AML KYC compliance")


def test_upsert_deduplicates_and_preserves_status(tmp_path):
    path = tmp_path / "db.sqlite3"; init_db(path)
    with session(path) as conn:
        job_id = upsert_job(conn, make_job())
        change_status(conn, job_id, ApplicationStatus.SHORTLISTED)
        assert upsert_job(conn, make_job(title="Senior Fraud Analyst")) == job_id
        [row] = list_jobs(conn)
        assert row["title"] == "Senior Fraud Analyst" and row["status"] == "shortlisted"


def test_settings_rescore_existing_jobs(tmp_path):
    path = tmp_path / "db.sqlite3"; init_db(path)
    with session(path) as conn:
        upsert_job(conn, make_job(title="Python Engineer"))
        settings = ScoringSettings(preferred_terms={"python": 25}, excluded_terms=[], blacklisted_companies=[], minimum_score=0)
        save_scoring_settings(conn, settings)
        assert rescore_all(conn, settings) == 1
        assert list_jobs(conn)[0]["score"] == 50


def test_filters(tmp_path):
    path = tmp_path / "db.sqlite3"; init_db(path)
    with session(path) as conn:
        upsert_job(conn, make_job("1", "Fraud Analyst")); upsert_job(conn, make_job("2", "Retail Associate"))
        rows = list_jobs(conn, query="Fraud", min_score=10)
        assert len(rows) == 1 and rows[0]["external_id"] == "1"
