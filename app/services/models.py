import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ApplicationRun(Base):
    """One row per job application run (one CV + one JD)."""

    __tablename__ = "application_runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    thread_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)

    cv_text: Mapped[str] = mapped_column(Text)
    jd_text: Mapped[str] = mapped_column(Text)

    jd_analysis: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    tailored_cv: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_letter: Mapped[str | None] = mapped_column(Text, nullable=True)
    review: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="pending")
    revision_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )