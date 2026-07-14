from fastapi.testclient import TestClient
from app.main import app


def payload():
    return {"source":"manual","external_id":"1","title":"Bilingual Fraud Investigator","company":"Example Bank","location":"Ottawa","apply_url":"https://example.com/apply","description":"AML KYC banking investigation"}


def test_job_flow_uses_temporary_database(tmp_path, monkeypatch):
    database = tmp_path / "test.sqlite3"; monkeypatch.setenv("JOBSNIFFING_DB", str(database))
    with TestClient(app) as client:
        response = client.post("/api/jobs", json=payload()); assert response.status_code == 201
        job_id = response.json()["id"]
        assert client.post(f"/api/jobs/{job_id}/status", json={"status":"shortlisted"}).status_code == 200
        assert client.get("/api/jobs").json()[0]["status"] == "shortlisted"
    assert database.exists()


def test_validation_transition_and_unknown_errors(tmp_path, monkeypatch):
    monkeypatch.setenv("JOBSNIFFING_DB", str(tmp_path / "test.sqlite3"))
    with TestClient(app) as client:
        bad = payload(); bad["apply_url"] = "not-a-url"; assert client.post("/api/jobs", json=bad).status_code == 422
        job_id = client.post("/api/jobs", json=payload()).json()["id"]
        assert client.post(f"/api/jobs/{job_id}/status", json={"status":"submitted"}).status_code == 409
        assert client.post("/api/jobs/999/status", json={"status":"shortlisted"}).status_code == 404


def test_blank_status_filter_means_all_statuses(tmp_path, monkeypatch):
    monkeypatch.setenv("JOBSNIFFING_DB", str(tmp_path / "test.sqlite3"))
    with TestClient(app) as client:
        assert client.post("/api/jobs", json=payload()).status_code == 201
        page = client.get("/?q=&status=&min_score=0")
        assert page.status_code == 200
        assert "Bilingual Fraud Investigator" in page.text
        jobs = client.get("/api/jobs?status=")
        assert jobs.status_code == 200
        assert len(jobs.json()) == 1
        assert client.get("/?status=not-a-status").status_code == 422


def test_settings_export_static_delete_and_health(tmp_path, monkeypatch):
    database = tmp_path / "test.sqlite3"; monkeypatch.setenv("JOBSNIFFING_DB", str(database)); monkeypatch.chdir(tmp_path)
    with TestClient(app) as client:
        job_id = client.post("/api/jobs", json=payload()).json()["id"]
        settings = {"preferred_terms":{"investigator":30},"excluded_terms":[],"blacklisted_companies":[],"minimum_score":10}
        assert client.put("/api/settings/scoring", json=settings).status_code == 200
        assert client.get("/api/jobs").json()[0]["score"] == 60
        assert "Bilingual Fraud Investigator" in client.get("/api/jobs/export.csv").text
        assert client.get("/").status_code == 200 and "--accent" in client.get("/static/styles.css").text
        health = client.get("/health").json(); assert health["jobs"] == 1 and health["database"] == str(database)
        assert client.delete(f"/api/jobs/{job_id}").status_code == 204
        assert client.get(f"/api/jobs/{job_id}").status_code == 404


def test_automation_settings_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("JOBSNIFFING_DB", str(tmp_path / "test.sqlite3"))
    with TestClient(app) as client:
        assert client.get("/api/settings/automation").json()["mode"] == "manual"
        response = client.put("/api/settings/automation", json={"mode":"assisted","daily_cap":3,"min_delay_seconds":15})
        assert response.status_code == 200
        assert response.json() == {"mode":"assisted","daily_cap":3,"min_delay_seconds":15}
        health = client.get("/health").json()
        assert health["automation"] == "assisted" and health["automation_daily_cap"] == 3
