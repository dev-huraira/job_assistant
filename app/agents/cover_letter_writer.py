from langchain_core.messages import HumanMessage, SystemMessage
from app.core.guardrails import UNTRUSTED_DATA_RULE, wrap_untrusted

from app.core.llm import get_llm, invoke_with_retry
from app.core.logging_config import get_logger
from app.schemas.cover_letter import CoverLetterOutput
from app.schemas.jd_analysis import JDAnalysis

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a skilled cover letter writer.

Write a concise, genuine-sounding cover letter based ONLY on the candidate's
actual CV content and the job description analysis provided. Follow these
rules strictly:

1. NEVER invent experience, skills, employers, or achievements not present
   in the candidate's CV text given to you.
2. Match the tone of the job posting (e.g. formal corporate vs. startup-casual).
3. Structure: a short opening hook, 1-2 paragraphs connecting real experience
   to the job's needs, and a brief closing paragraph with a call to action.
4. Keep it between 200 and 350 words.
5. Do not use generic filler like "I am a hard worker" without tying it to
   a specific, real example from the CV.
6. If given reviewer feedback, revise accordingly without violating rules 1-5.
7. Do not invent a greeting name if none is given; use "Dear Hiring Manager,".
8. Do not mention any required skill or tool that is not present in the
   CV, not even as something the candidate plans to learn.

Return the full cover letter body (including greeting and sign-off),
its approximate word count, and the tone you used.
""" + UNTRUSTED_DATA_RULE


def write_cover_letter(
    tailored_cv: str,
    jd_analysis: JDAnalysis,
    feedback: list[str] | None = None,
) -> CoverLetterOutput:
    """Run the Cover Letter Writer agent and return structured output."""
    logger.info("Writing cover letter for job title: %s", jd_analysis.job_title)

    llm = get_llm(temperature=0.4)
    structured_llm = llm.with_structured_output(CoverLetterOutput)

    feedback_block = ""
    if feedback:
        feedback_lines = "\n".join(f"- {item}" for item in feedback)
        feedback_block = (
            f"\n\nReviewer feedback to address on this revision:\n{feedback_lines}"
        )

    human_content = (
        f"{wrap_untrusted('tailored_cv', tailored_cv)}\n\n"
        f"Job title: {jd_analysis.job_title}\n"
        f"Company name: {jd_analysis.company_name or 'the company'}\n"
        f"Seniority: {jd_analysis.seniority.value}\n"
        f"Required skills: {', '.join(jd_analysis.required_skills)}\n"
        f"Job posting tone: {jd_analysis.tone}\n"
        f"Role summary: {jd_analysis.summary}"
        f"{feedback_block}"
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=human_content),
    ]

    result = invoke_with_retry(structured_llm, messages)

    logger.info(
        "Cover letter complete: %d words, tone=%s", result.word_count, result.tone_used
    )
    return result