import pytest

from app.core.guardrails import find_unsupported_terms
from tests.helpers import BACKEND_JD_TEXT, CV_TEXT, JD_TEXT, initial_state

# Every test in this file calls the REAL Gemini API and costs tokens.
pytestmark = pytest.mark.live


def test_matching_job_is_truthful_and_ready_for_approval(graph):
    state = graph.invoke(
        initial_state(CV_TEXT, JD_TEXT),
        config={"configurable": {"thread_id": "live-match"}},
    )

    assert state["review"].truthful is True
    assert state["status"] == "awaiting_approval"


def test_mismatched_job_never_ships_invented_skills(graph):
    state = graph.invoke(
        initial_state(CV_TEXT, BACKEND_JD_TEXT),
        config={"configurable": {"thread_id": "live-mismatch"}},
    )

    assert state["status"] in ("awaiting_approval", "needs_manual_review")
    if state["status"] == "awaiting_approval":
        output = state["tailored_cv"] + "\n" + state["cover_letter"]
        invented = find_unsupported_terms(
            CV_TEXT, output, ["Python", "REST API", "PostgreSQL", "Docker", "Flask"]
        )
        assert invented == []