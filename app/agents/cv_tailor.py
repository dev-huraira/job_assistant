from langchain_core.messages import HumanMessage, SystemMessage
from app.core.guardrails import UNTRUSTED_DATA_RULE, wrap_untrusted

from app.core.llm import get_llm, invoke_with_retry
from app.core.logging_config import get_logger
from app.schemas.cv_tailor import TailoredCVOutput
from app.schemas.jd_analysis import JDAnalysis

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a careful, honest CV tailoring assistant.

Your job is to rewrite the given CV so it better matches the target job,
following these rules strictly and without exception:

1. NEVER invent skills, tools, employers, job titles, dates, metrics, or
   achievements that are not already present in the original CV text.
2. You MAY: reorder bullets, rephrase wording, emphasize relevant existing
   experience, and surface keywords from the job description IF the
   underlying skill/experience is genuinely already present in the CV.
3. If the candidate's CV is missing something the job wants, DO NOT add it.
   Simply do not claim it.
4. Keep the CV's real structure (sections, employers, dates) unchanged.
   You are rewriting the wording and emphasis, not the facts.
5. If given reviewer feedback, apply it carefully without violating rules 1-4.
6. Before writing, compare the job's required skills with the CV. For every
   required skill or tool that is NOT in the CV, do not mention it anywhere
   in your output, not even as "familiar with" or "eager to learn".

Return the full tailored CV text, plus a short list of the changes you made.
""" + UNTRUSTED_DATA_RULE


def tailor_cv(
    cv_text: str,
    jd_analysis: JDAnalysis,
    feedback: list[str] | None = None,
) -> TailoredCVOutput:
    """Run the CV Tailor agent and return a structured TailoredCVOutput."""
    logger.info("Tailoring CV for job title: %s", jd_analysis.job_title)

    llm = get_llm(temperature=0.2)
    structured_llm = llm.with_structured_output(TailoredCVOutput)

    feedback_block = ""
    if feedback:
        feedback_lines = "\n".join(f"- {item}" for item in feedback)
        feedback_block = (
            f"\n\nReviewer feedback to address on this revision:\n{feedback_lines}"
        )

    human_content = (
        f"{wrap_untrusted('original_cv', cv_text)}\n\n"
        f"Target job title: {jd_analysis.job_title}\n"
        f"Seniority: {jd_analysis.seniority.value}\n"
        f"Required skills: {', '.join(jd_analysis.required_skills)}\n"
        f"Nice to have skills: {', '.join(jd_analysis.nice_to_have_skills)}\n"
        f"Keywords to surface where truthful: {', '.join(jd_analysis.keywords)}"
        f"{feedback_block}"
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=human_content),
    ]

    result = invoke_with_retry(structured_llm, messages)

    logger.info("CV tailoring complete: %d change(s) made", len(result.changes_made))
    return result