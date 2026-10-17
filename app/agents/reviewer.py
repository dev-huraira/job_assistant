from langchain_core.messages import HumanMessage, SystemMessage
from app.core.guardrails import UNTRUSTED_DATA_RULE, wrap_untrusted

from app.core.llm import get_llm, invoke_with_retry
from app.core.logging_config import get_logger
from app.schemas.jd_analysis import JDAnalysis
from app.schemas.review import ReviewResult

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a strict, detail-oriented reviewer of job
application materials. You check a tailored CV and a cover letter against
the candidate's ORIGINAL CV and the job description analysis.

Check for these things, in order of importance:

1. TRUTHFULNESS (most important): Does the tailored CV or cover letter
   claim any skill, employer, tool, metric, or achievement that is NOT
   present in the original CV? If yes, set truthful=False and describe
   the specific fabrication in "issues". This overrides everything else:
   if truthful=False, you MUST set approved=False regardless of score.

2. KEYWORD COVERAGE: What fraction (0.0 to 1.0) of the JD's keywords and
   required skills are reasonably reflected in the tailored CV?

3. QUALITY: Is the writing clear, well-structured, free of generic filler,
   and does the cover letter stay roughly within 200-350 words?

Scoring: give an overall score from 0 to 100 reflecting truthfulness,
keyword coverage, and quality combined. Truthfulness violations should
drag the score down heavily (below 40) even if the writing quality is good.

Approval rule: approved=True only if truthful=True AND score >= 75.
Otherwise approved=False, and "suggestions" must contain concrete,
actionable fixes for the next revision (not vague praise or vague
criticism).
""" + UNTRUSTED_DATA_RULE


def review_application(
    original_cv: str,
    tailored_cv: str,
    cover_letter: str,
    jd_analysis: JDAnalysis,
) -> ReviewResult:
    """Run the Reviewer agent and return a structured ReviewResult."""
    logger.info("Reviewing application for job title: %s", jd_analysis.job_title)

    llm = get_llm(temperature=0.0)
    structured_llm = llm.with_structured_output(ReviewResult)

    human_content = (
        f"ORIGINAL CV (source of truth for facts):\n{wrap_untrusted('original_cv', original_cv)}\n\n"
        f"TAILORED CV (to review):\n{wrap_untrusted('tailored_cv', tailored_cv)}\n\n"
        f"COVER LETTER (to review):\n{wrap_untrusted('cover_letter', cover_letter)}\n\n"
        f"Job title: {jd_analysis.job_title}\n"
        f"Required skills: {', '.join(jd_analysis.required_skills)}\n"
        f"Nice to have skills: {', '.join(jd_analysis.nice_to_have_skills)}\n"
        f"Keywords: {', '.join(jd_analysis.keywords)}"
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=human_content),
    ]

    result = invoke_with_retry(structured_llm, messages)

    logger.info(
        "Review complete: score=%d, truthful=%s, approved=%s",
        result.score,
        result.truthful,
        result.approved,
    )
    return result