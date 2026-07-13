from fastapi.testclient import TestClient

from app.main import app


def sample_job(external_id: str = "1") -> dict[str, str]:
    return {
        "source": "manual",
        "external_id": external_id,
        "title": "Android FastAPI Engineer",
        "company": "Example",
        "location": "Remote",
        "apply_url": "https://example.com/apply",
        "description": "Python SQLite backend",
    }


def test_job_can_be_created_filtered_and_moved_to_shortlist(tmp_path, monkeypatch):
    monkeypatch.setenv("JOBSNIFFING_DB", str(tmp_path / "test.sqlite3"))
    with TestClient(app) as client:
        response = client.post("/api/jobs", json=sample_job())
        assert response.status_code == 201
        job_id = response.json()["id"]
        assert response.json()["status"] == "scored"

        changed = client.post(
            f"/api/jobs/{job_id}/status",
            json={"status": "shortlisted", "notes": "Strong fit"},
        )
        assert changed.status_code == 200
        assert changed.json()["notes"] == "Strong fit"

        jobs = client.get("/api/jobs?status=shortlisted&min_score=1").json()
        assert len(jobs) == 1
        assert jobs[0]["status"] == "shortlisted"


def test_invalid_payload_is_422_and_unknown_job_is_404(tmp_path, monkeypatch):
    monkeypatch.setenv("JOBSNIFFING_DB", str(tmp_path / "test.sqlite3"))
    with TestClient(app) as client:
        assert client.post("/api/jobs", json={"title": "missing fields"}).status_code == 422
        assert client.get("/api/jobs/999").status_code == 404


def test_invalid_transition_is_conflict(tmp_path, monkeypatch):
    monkeypatch.setenv("JOBSNIFFING_DB", str(tmp_path / "test.sqlite3"))
    with TestClient(app) as client:
        job_id = client.post("/api/jobs", json=sample_job()).json()["id"]
        response = client.post(
            f"/api/jobs/{job_id}/status",
            json={"status": "submitted"},
        )
        assert response.status_code == 409


def test_upsert_does_not_reset_review_status(tmp_path, monkeypatch):
    monkeypatch.setenv("JOBSNIFFING_DB", str(tmp_path / "test.sqlite3"))
    with TestClient(app) as client:
        job_id = client.post("/api/jobs", json=sample_job()).json()["id"]
        client.post(f"/api/jobs/{job_id}/status", json={"status": "shortlisted"})
        updated = sample_job()
        updated["title"] = "Updated Android FastAPI Engineer"
        response = client.post("/api/jobs", json=updated)
        assert response.json()["status"] == "shortlisted"


def test_root_page_works_outside_repository_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("JOBSNIFFING_DB", str(tmp_path / "test.sqlite3"))
    monkeypatch.chdir(tmp_path)
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "JobSniffing" in response.text


def test_discovery_board_rejects_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("JOBSNIFFING_DB", str(tmp_path / "test.sqlite3"))
    with TestClient(app) as client:
        response = client.post(
            "/api/discovery/scan",
            json={"source": "greenhouse", "board": "../other"},
        )
        assert response.status_code == 422
