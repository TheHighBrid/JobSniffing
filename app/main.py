from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import sqlite3

from app.db.sqlite import init_db, session
from app.domain.enums import ApplicationStatus
from app.domain.schemas import JobPostingIn, StatusChange
from app.services.tracking_service import change_status, list_jobs, upsert_job

app = FastAPI(title="JobSniffing", version="0.1.0")
app.mount("/static", StaticFiles(directory="app/web/static"), name="static")
templates = Jinja2Templates(directory="app/web/templates")


def get_conn():
    init_db()
    with session() as conn:
        yield conn


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "local-first", "automation": "disabled-by-default"}


@app.post("/api/jobs")
def create_job(job: dict, conn: sqlite3.Connection = Depends(get_conn)) -> dict[str, int]:
    return {"id": upsert_job(conn, JobPostingIn(**job) if isinstance(job, dict) else job)}


@app.get("/api/jobs")
def api_jobs(conn: sqlite3.Connection = Depends(get_conn)):
    return [dict(row) for row in list_jobs(conn)]


@app.post("/api/jobs/{job_id}/status")
def api_change_status(job_id: int, change: dict, conn: sqlite3.Connection = Depends(get_conn)):
    try:
        status_change = StatusChange(status=ApplicationStatus(change["status"]), notes=change.get("notes", ""))
        change_status(conn, job_id, status_change.status, status_change.notes)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "status": status_change.status}


@app.get("/", response_class=HTMLResponse)
def index(request: Request, conn: sqlite3.Connection = Depends(get_conn)):
    return templates.TemplateResponse("index.html", {"request": request, "jobs": list_jobs(conn), "statuses": list(ApplicationStatus)})
