from pydantic import BaseModel, Field


class ReviewResult(BaseModel):
    """Structured output of the Reviewer agent."""

    score: int = Field(..., ge=0, le=100, description="Overall quality score")
    truthful: bool = Field(
        ..., description="False if the CV/letter contains facts not in the original CV"
    )
    keyword_coverage: float = Field(
        ..., ge=0.0, le=1.0, description="Fraction of JD keywords present in the CV"
    )
    issues: list[str] = Field(
        default_factory=list, description="Specific problems found"
    )
    suggestions: list[str] = Field(
        default_factory=list, description="Concrete fixes for the Tailor/Writer"
    )
    approved: bool = Field(
        ..., description="True if this output is good enough to show the user"
    )