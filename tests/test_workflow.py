import pytest

from app.schemas.cover_letter import CoverLetterOutput
from app.schemas.cv_tailor import TailoredCVOutput
from app.schemas.jd_analysis import JDAnalysis
from app.schemas.review import ReviewResult
from tests.helpers import (
    initial_state,
    make_jd_analysis,
    make_letter,
    make_review,
    make_tailored,
    prompt_text,
    queue_happy_path,
)


def config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def test_approved_first_pass_pauses_then_completes_on_resume(fake_llm, graph):
    queue_happy_path(fake_llm)
    cfg = config("t-happy")

    paused = graph.invoke(initial_state(), config=cfg)

    assert paused["status"] == "awaiting_approval"
    assert paused["revision_count"] == 0
    assert graph.get_state(cfg).next == ("await_approval",)

    final = graph.invoke(None, config=cfg)

    assert final["status"] == "completed"
    assert graph.get_state(cfg).next == ()


def test_rejected_review_sends_feedback_back_to_both_writers(fake_llm, graph):
    fake_llm.queue(JDAnalysis, make_jd_analysis())
    fake_llm.queue(TailoredCVOutput, make_tailored(), make_tailored())
    fake_llm.queue(CoverLetterOutput, make_letter(), make_letter())
    rejected = make_review(score=60, approved=False, suggestions=["Make the opening more specific"])
    fake_llm.queue(ReviewResult, rejected, make_review())

    state = graph.invoke(initial_state(), config=config("t-revise"))

    assert state["status"] == "awaiting_approval"
    assert state["revision_count"] == 1
    assert len(fake_llm.calls_for(JDAnalysis)) == 1  # the JD is analyzed only once

    tailor_calls = fake_llm.calls_for(TailoredCVOutput)
    letter_calls = fake_llm.calls_for(CoverLetterOutput)
    assert len(tailor_calls) == 2
    assert len(letter_calls) == 2
    assert "Make the opening more specific" not in prompt_text(tailor_calls[0])
    assert "Make the opening more specific" in prompt_text(tailor_calls[1])
    assert "Make the opening more specific" in prompt_text(letter_calls[1])


def test_gives_up_after_max_revisions(fake_llm, graph):
    queue_happy_path(
        fake_llm,
        review=make_review(score=50, approved=False, suggestions=["Tighten wording"]),
    )

    state = graph.invoke(initial_state(), config=config("t-max"))

    assert state["status"] == "needs_manual_review"
    assert state["revision_count"] == 3
    assert len(fake_llm.calls_for(ReviewResult)) == 3
    assert len(fake_llm.calls_for(TailoredCVOutput)) == 3


def test_deterministic_check_overrides_an_approving_reviewer(fake_llm, graph):
    fake_llm.queue(
        JDAnalysis,
        make_jd_analysis(required_skills=["Excel", "Docker"], nice_to_have_skills=[]),
    )
    fake_llm.queue(TailoredCVOutput, make_tailored())
    fake_llm.queue(
        CoverLetterOutput,
        make_letter("Dear Hiring Manager, I have used Docker and Excel in my projects."),
    )
    fake_llm.queue(ReviewResult, make_review())  # the LLM reviewer says "all good"

    state = graph.invoke(initial_state(), config=config("t-fabrication"))

    review = state["review"]
    assert review.truthful is False
    assert review.approved is False
    assert review.score <= 40
    assert any("Docker" in issue for issue in review.issues)
    assert state["status"] == "needs_manual_review"


@pytest.mark.parametrize("score, truthful", [(74, True), (60, True), (95, False)])
def test_approval_rule_is_enforced_in_code(fake_llm, graph, score, truthful):
    queue_happy_path(
        fake_llm, review=make_review(score=score, truthful=truthful, approved=True)
    )

    state = graph.invoke(initial_state(), config=config("t-rule"))

    assert state["review"].approved is False
    assert state["status"] == "needs_manual_review"


def test_a_score_of_75_is_approved_even_if_the_reviewer_said_no(fake_llm, graph):
    queue_happy_path(fake_llm, review=make_review(score=75, approved=False))

    state = graph.invoke(initial_state(), config=config("t-threshold"))

    assert state["review"].approved is True
    assert state["status"] == "awaiting_approval"


def test_llm_failure_propagates_after_three_attempts(fake_llm, graph, no_retry_delay):
    fake_llm.queue(JDAnalysis, RuntimeError("503 UNAVAILABLE"))

    with pytest.raises(RuntimeError, match="503"):
        graph.invoke(initial_state(), config=config("t-fail"))

    assert len(fake_llm.calls_for(JDAnalysis)) == 3