from pydantic import BaseModel, Field


class TailoredCVOutput(BaseModel):
    """Structured output of the CV Tailor agent."""

    tailored_cv: str = Field(
        ..., description="The full rewritten CV text, ready to show the user"
    )
    changes_made: list[str] = Field(
        default_factory=list,
        description="Short list of what was changed and why, for traceability",
    )