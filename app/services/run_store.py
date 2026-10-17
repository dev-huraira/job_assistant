from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.services.models import ApplicationRun

logger = get_logger(__name__)


def create_run(db: Session, thread_id: str, cv_text: str, jd_text: str) -> ApplicationRun:
    """Insert a new application run row with status 'pending'."""
    run = ApplicationRun(
        thread_id=thread_id,
        cv_text=cv_text,
        jd_text=jd_text,
        status="pending",
        revision_count=0,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    logger.info("Created run %s (thread_id=%s)", run.id, run.thread_id)
    return run


def get_run_by_thread_id(db: Session, thread_id: str) -> ApplicationRun | None:
    """Fetch a run by its LangGraph thread_id, or None if it doesn't exist."""
    return db.query(ApplicationRun).filter(ApplicationRun.thread_id == thread_id).first()


def update_run_from_state(db: Session, thread_id: str, state: dict) -> ApplicationRun | None:
    """Sync fields from a LangGraph state dict into the database row.

    Only overwrites fields that are actually present in `state`, so this
    is safe to call with a partial state (e.g. right after just one node
    has run).
    """
    run = get_run_by_thread_id(db, thread_id)
    if run is None:
        logger.warning("No run found for thread_id=%s, cannot update", thread_id)
        return None

    if state.get("jd_analysis") is not None:
        run.jd_analysis = state["jd_analysis"].model_dump()
    if state.get("tailored_cv") is not None:
        run.tailored_cv = state["tailored_cv"]
    if state.get("cover_letter") is not None:
        run.cover_letter = state["cover_letter"]
    if state.get("review") is not None:
        run.review = state["review"].model_dump()
    if state.get("status") is not None:
        run.status = state["status"]
    if state.get("revision_count") is not None:
        run.revision_count = state["revision_count"]

    db.commit()
    db.refresh(run)
    logger.info("Updated run %s: status=%s", run.id, run.status)
    return run

def set_run_status(db: Session, thread_id: str, status: str) -> None:
    """Set only the status of a run (used to mark failures)."""
    run = get_run_by_thread_id(db, thread_id)
    if run is None:
        logger.warning("No run found for thread_id=%s, cannot set status", thread_id)
        return

    run.status = status
    db.commit()
    logger.info("Run %s status set to %s", run.id, status)