from __future__ import annotations

import csv
import io
import sqlite3
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import APP_VERSION, PROJECT_ROOT, get_db_path
from app.db.sqlite import init_db, session
from app.domain.enums import ApplicationStatus
from app.domain.schemas import AutomationSettings, DiscoveryRequest, JobImportRequest, JobPostingIn, ScoringSettings, StatusChange
from app.domain.state_machine import ALLOWED_TRANSITIONS
from app.services.discovery_service import DiscoveryError, discover
from app.services.settings_service import load_automation_settings, load_scoring_settings, save_automation_settings, save_scoring_settings
from app.services.tracking_service import bulk_upsert, change_status, delete_job, get_job, list_jobs, log_run, rescore_all, stats, upsert_job


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="JobSniffing", version=APP_VERSION, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=PROJECT_ROOT / "app/web/static"), name="static")
templates = Jinja2Templates(directory=PROJECT_ROOT / "app/web/templates")


def get_conn():
    init_db()
    with session() as conn:
        yield conn


def parse_optional_status(value: str | None) -> ApplicationStatus | None:
    """Treat a missing or blank query value as no status filter."""
    if value is None or not value.strip():
        return None
    try:
        return ApplicationStatus(value)
    except ValueError as exc:
        allowed = ", ".join(status.value for status in ApplicationStatus)
        raise HTTPException(422, f"Invalid status '{value}'. Expected one of: {allowed}") from exc


@app.get("/health")
def health(conn: sqlite3.Connection = Depends(get_conn)):
    automation = load_automation_settings(conn)
    return {"status": "ok", "version": APP_VERSION, "mode": "local-first", "automation": automation.mode.value, "automation_daily_cap": automation.daily_cap, "database": str(get_db_path()), "jobs": stats(conn)["total"], "providers": ["greenhouse", "lever", "ashby"]}


@app.post("/api/jobs", status_code=201)
def create_job(job: JobPostingIn, conn: sqlite3.Connection = Depends(get_conn)):
    return {"id": upsert_job(conn, job)}


@app.post("/api/jobs/import", status_code=201)
def import_jobs(payload: JobImportRequest, conn: sqlite3.Connection = Depends(get_conn)):
    ids = bulk_upsert(conn, payload.jobs)
    log_run(conn, "import", f"Imported {len(ids)} jobs")
    return {"imported": len(ids), "ids": ids}


@app.get("/api/jobs")
def api_jobs(status_value: str | None = Query(None, alias="status"), q: str = Query("", max_length=200), min_score: int = Query(0, ge=0, le=100), limit: int = Query(250, ge=1, le=1000), conn: sqlite3.Connection = Depends(get_conn)):
    job_status = parse_optional_status(status_value)
    return [dict(row) for row in list_jobs(conn, status=job_status, query=q, min_score=min_score, limit=limit)]


@app.get("/api/jobs/export.csv")
def export_jobs(conn: sqlite3.Connection = Depends(get_conn)):
    output = io.StringIO()
    fields = ["id", "source", "external_id", "title", "company", "location", "apply_url", "score", "status", "notes", "created_at", "updated_at"]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in list_jobs(conn, limit=100000):
        writer.writerow(dict(row))
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=jobsniffing-export.csv"})


@app.get("/api/jobs/{job_id}")
def api_job(job_id: int, conn: sqlite3.Connection = Depends(get_conn)):
    row = get_job(conn, job_id)
    if row is None:
        raise HTTPException(404, f"Unknown job id {job_id}")
    return dict(row)


@app.delete("/api/jobs/{job_id}", status_code=204)
def api_delete(job_id: int, conn: sqlite3.Connection = Depends(get_conn)):
    if not delete_job(conn, job_id):
        raise HTTPException(404, f"Unknown job id {job_id}")
    return Response(status_code=204)


@app.post("/api/jobs/{job_id}/status")
def api_status(job_id: int, change: StatusChange, conn: sqlite3.Connection = Depends(get_conn)):
    try:
        change_status(conn, job_id, change.status, change.notes)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"ok": True, "status": change.status.value}


@app.post("/api/discovery")
def api_discovery(request: DiscoveryRequest, conn: sqlite3.Connection = Depends(get_conn)):
    try:
        jobs = discover(request)
    except DiscoveryError as exc:
        raise HTTPException(502, str(exc)) from exc
    ids = bulk_upsert(conn, jobs)
    log_run(conn, "discovery", f"{request.provider}:{request.identifier} stored {len(ids)} jobs")
    return {"provider": request.provider, "identifier": request.identifier, "discovered": len(jobs), "stored": len(ids), "ids": ids}


@app.get("/api/settings/scoring", response_model=ScoringSettings)
def get_settings(conn: sqlite3.Connection = Depends(get_conn)):
    return load_scoring_settings(conn)


@app.put("/api/settings/scoring", response_model=ScoringSettings)
def put_settings(settings: ScoringSettings, conn: sqlite3.Connection = Depends(get_conn)):
    save_scoring_settings(conn, settings)
    rescore_all(conn, settings)
    return settings


@app.get("/api/settings/automation", response_model=AutomationSettings)
def get_automation_settings(conn: sqlite3.Connection = Depends(get_conn)):
    return load_automation_settings(conn)


@app.put("/api/settings/automation", response_model=AutomationSettings)
def put_automation_settings(settings: AutomationSettings, conn: sqlite3.Connection = Depends(get_conn)):
    save_automation_settings(conn, settings)
    log_run(conn, "automation-settings", f"Mode set to {settings.mode.value}; cap={settings.daily_cap}; delay={settings.min_delay_seconds}s")
    return settings


@app.post("/api/jobs/rescore")
def rescore(conn: sqlite3.Connection = Depends(get_conn)):
    return {"rescored": rescore_all(conn)}


@app.get("/api/stats")
def api_stats(conn: sqlite3.Connection = Depends(get_conn)):
    return stats(conn)


@app.get("/", response_class=HTMLResponse)
def index(request: Request, status_value: str | None = Query(None, alias="status"), q: str = Query("", max_length=200), min_score: int | None = Query(None, ge=0, le=100), conn: sqlite3.Connection = Depends(get_conn)):
    job_status = parse_optional_status(status_value)
    settings = load_scoring_settings(conn)
    resolved_min = settings.minimum_score if min_score is None else min_score
    transitions = {s.value: [t.value for t in sorted(targets, key=lambda item: item.value)] for s, targets in ALLOWED_TRANSITIONS.items()}
    return templates.TemplateResponse(request=request, name="index.html", context={"jobs": list_jobs(conn, status=job_status, query=q, min_score=resolved_min, limit=500), "stats": stats(conn), "statuses": list(ApplicationStatus), "selected_status": job_status.value if job_status else "", "query": q, "min_score": resolved_min, "transitions": transitions, "automation": load_automation_settings(conn), "version": APP_VERSION})
