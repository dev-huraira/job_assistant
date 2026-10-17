from pydantic import BaseModel, ConfigDict


class ApplicationResponse(BaseModel):
    """What every API endpoint returns to describe one application run."""

    model_config = ConfigDict(from_attributes=True)

    thread_id: str
    status: str
    revision_count: int
    jd_analysis: dict | None = None
    tailored_cv: str | None = None
    cover_letter: str | None = None
    review: dict | None = None