from typing import Optional, TypedDict

from app.schemas.jd_analysis import JDAnalysis
from app.schemas.review import ReviewResult


class GraphState(TypedDict, total=False):
    """Shared state passed between every node in the LangGraph workflow."""

    cv_text: str
    jd_text: str

    jd_analysis: Optional[JDAnalysis]
    tailored_cv: Optional[str]
    cover_letter: Optional[str]
    review: Optional[ReviewResult]

    revision_count: int
    status: str
    error: Optional[str]