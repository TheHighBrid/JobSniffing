pytest = __import__("pytest")
fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
from app.main import app


def test_job_can_be_created_and_moved_to_shortlist(tmp_path, monkeypatch):
    monkeypatch.setenv("JOBSNIFFING_DB", str(tmp_path / "test.sqlite3"))
    client = TestClient(app)
    response = client.post("/api/jobs", json={
        "source": "manual", "external_id": "1", "title": "Android FastAPI Engineer",
        "company": "Example", "location": "Remote", "apply_url": "https://example.com/apply",
        "description": "Python SQLite backend"
    })
    assert response.status_code == 200
    job_id = response.json()["id"]
    assert client.post(f"/api/jobs/{job_id}/status", json={"status": "shortlisted"}).status_code == 200
    jobs = client.get("/api/jobs").json()
    assert jobs[0]["status"] == "shortlisted"
