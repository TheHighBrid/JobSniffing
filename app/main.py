import sqlite3
from collections.abc import Iterator
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.db.sqlite import init_db, session
from app.domain.enums import ApplicationStatus
from app.domain.schemas import (
    DiscoveryScanRequest,
    DiscoveryScanResult,
    JobPostingIn,
    JobPostingResponse,
    StatusChange,
)
from app.domain.state_machine import ALLOWED_TRANSITIONS
from app.services.discovery_service import DiscoveryError, fetch_jobs
from app.services.tracking_service import (
    InvalidTransitionError,
    JobNotFoundError,
    change_status,
    get_job,
    list_jobs,
    log_run,
    upsert_job,
)

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="JobSniffing",
    version="0.2.0",
    description="Local-first job discovery and review queue for Android/Termux.",
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "web" / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "web" / "templates")


def get_conn() -> Iterator[sqlite3.Connection]:
    init_db()
    with session() as conn:
        yield conn


def row_to_job(row: sqlite3.Row) -> JobPostingResponse:
    return JobPostingResponse(**dict(row))


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "mode": "local-first",
        "automation": "manual-review-only",
        "version": app.version,
    }


@app.post(
    "/api/jobs",
    response_model=JobPostingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_job(
    job: JobPostingIn,
    conn: sqlite3.Connection = Depends(get_conn),
) -> JobPostingResponse:
    job_id = upsert_job(conn, job)
    return row_to_job(get_job(conn, job_id))


@app.get("/api/jobs", response_model=list[JobPostingResponse])
def api_jobs(
    job_status: ApplicationStatus | None = Query(default=None, alias="status"),
    min_score: int = Query(default=0, ge=0, le=100),
    limit: int = Query(default=200, ge=1, le=1000),
    conn: sqlite3.Connection = Depends(get_conn),
) -> list[JobPostingResponse]:
    return [
        row_to_job(row)
        for row in list_jobs(conn, status=job_status, min_score=min_score, limit=limit)
    ]


@app.get("/api/jobs/{job_id}", response_model=JobPostingResponse)
def api_job(
    job_id: int,
    conn: sqlite3.Connection = Depends(get_conn),
) -> JobPostingResponse:
    try:
        return row_to_job(get_job(conn, job_id))
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/jobs/{job_id}/status", response_model=JobPostingResponse)
def api_change_status(
    job_id: int,
    change: StatusChange,
    conn: sqlite3.Connection = Depends(get_conn),
) -> JobPostingResponse:
    try:
        row = change_status(conn, job_id, change.status, change.notes)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return row_to_job(row)


@app.post("/api/discovery/scan", response_model=DiscoveryScanResult)
def scan_discovery_source(
    scan: DiscoveryScanRequest,
    conn: sqlite3.Connection = Depends(get_conn),
) -> DiscoveryScanResult:
    try:
        jobs = fetch_jobs(scan)
    except DiscoveryError as exc:
        log_run(conn, "discovery_error", str(exc))
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    for job in jobs:
        upsert_job(conn, job)
    log_run(
        conn,
        "discovery_scan",
        f"source={scan.source} board={scan.board} jobs={len(jobs)}",
    )
    return DiscoveryScanResult(
        source=scan.source,
        board=scan.board,
        fetched=len(jobs),
        upserted=len(jobs),
    )


@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    conn: sqlite3.Connection = Depends(get_conn),
):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "jobs": list_jobs(conn),
            "statuses": list(ApplicationStatus),
            "allowed_transitions": {
                current.value: sorted(targets, key=lambda item: item.value)
                for current, targets in ALLOWED_TRANSITIONS.items()
            },
        },
    )
