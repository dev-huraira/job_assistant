import uuid
from contextlib import asynccontextmanager


from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.security import require_api_key

from app.core.logging_config import request_id_var
from app.core.observability import request_context_middleware, setup_tracing

from app.core.config import get_settings
from app.core.database import get_db, init_db
from app.core.guardrails import GuardrailError, validate_cv_text, validate_jd_text
from app.core.logging_config import get_logger, setup_logging
from app.core.rate_limit import rate_limit_applications
from app.graph.workflow import build_graph, build_postgres_checkpointer
from app.schemas.api import ApplicationResponse
from app.services.cv_parser import MAX_FILE_SIZE_BYTES, CVParsingError, extract_cv_text
from app.services.run_store import (
    create_run,
    get_run_by_thread_id,
    set_run_status,
    update_run_from_state,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once at startup (before yield) and once at shutdown (after yield)."""
    setup_logging()
    setup_tracing()
    logger.info("Starting up: initializing database and graph...")

    init_db()

    settings = get_settings()
    if not settings.api_key:
        logger.warning("API_KEY is not set: the API is open to anyone who can reach it")
    checkpointer, pool = build_postgres_checkpointer(settings.database_url)
    app.state.graph = build_graph(checkpointer=checkpointer)
    app.state.pool = pool

    logger.info("Startup complete.")
    yield

    logger.info("Shutting down: closing database connections...")
    pool.close()
    logger.info("Shutdown complete.")


app = FastAPI(title="Job Application Assistant", lifespan=lifespan)
app.middleware("http")(request_context_middleware)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    """Readiness: the server is up AND can reach the database."""
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Readiness check failed")
        raise HTTPException(status_code=503, detail="Database unavailable")
    return {"status": "ready"}


@app.post(
    "/applications",
    response_model=ApplicationResponse,
    dependencies=[Depends(require_api_key), Depends(rate_limit_applications)],
)
def create_application(
    cv_file: UploadFile = File(...),
    jd_text: str = Form(...),
    db: Session = Depends(get_db),
):
    """Upload a CV + paste a job description. Runs the full pipeline
    (including any automatic revisions) and pauses at the approval
    checkpoint, returning the result so far."""
    # Read at most MAX+1 bytes so a huge upload can't exhaust server memory
    cv_bytes = cv_file.file.read(MAX_FILE_SIZE_BYTES + 1)

    try:
        cv_text = extract_cv_text(cv_file.filename or "", cv_bytes)
        cv_text = validate_cv_text(cv_text)
        jd_text = validate_jd_text(jd_text)
    except (CVParsingError, GuardrailError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    thread_id = str(uuid.uuid4())
    create_run(db, thread_id=thread_id, cv_text=cv_text, jd_text=jd_text)

    config = {
        "configurable": {"thread_id": thread_id},
        "run_name": "job_application",
        "tags": ["job-assistant", "create"],
        "metadata": {"thread_id": thread_id, "request_id": request_id_var.get()},
    }

    initial_state = {"cv_text": cv_text, "jd_text": jd_text, "revision_count": 0}

    logger.info("Starting graph run for thread_id=%s", thread_id)
    try:
        final_state = app.state.graph.invoke(initial_state, config=config)
    except Exception:
        logger.exception("Graph run failed for thread_id=%s", thread_id)
        set_run_status(db, thread_id, "failed")
        raise HTTPException(
            status_code=503,
            detail="The AI service is temporarily unavailable. Please try again in a minute.",
        )

    run = update_run_from_state(db, thread_id, final_state)
    return ApplicationResponse.model_validate(run)


@app.get(
    "/applications/{thread_id}",
    response_model=ApplicationResponse,
    dependencies=[Depends(require_api_key)],
)
def get_application(thread_id: str, db: Session = Depends(get_db)):
    """Check the current status of an application run."""
    run = get_run_by_thread_id(db, thread_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return ApplicationResponse.model_validate(run)


@app.post(
    "/applications/{thread_id}/approve",
    response_model=ApplicationResponse,
    dependencies=[Depends(require_api_key)],
)
def approve_application(thread_id: str, db: Session = Depends(get_db)):
    """Resume a paused application run after human approval."""
    run = get_run_by_thread_id(db, thread_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Application not found")

    if run.status not in ("awaiting_approval", "needs_manual_review"):
        raise HTTPException(
            status_code=400,
            detail=f"Application is not ready for approval (status: {run.status})",
        )

    config = {
        "configurable": {"thread_id": thread_id},
        "run_name": "job_application_resume",
        "tags": ["job-assistant", "approve"],
        "metadata": {"thread_id": thread_id, "request_id": request_id_var.get()},
    }
    
    logger.info("Resuming graph run for thread_id=%s", thread_id)
    try:
        final_state = app.state.graph.invoke(None, config=config)
    except Exception:
        logger.exception("Resume failed for thread_id=%s", thread_id)
        raise HTTPException(
            status_code=503,
            detail="Could not complete the approval right now. Please try again.",
        )

    updated = update_run_from_state(db, thread_id, final_state)
    return ApplicationResponse.model_validate(updated)