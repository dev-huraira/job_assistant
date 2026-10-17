from langchain_core.messages import HumanMessage, SystemMessage
from app.core.guardrails import UNTRUSTED_DATA_RULE, wrap_untrusted

from app.core.llm import get_llm, invoke_with_retry
from app.core.logging_config import get_logger
from app.schemas.jd_analysis import JDAnalysis

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a precise job description analyzer.

Read the job description text given by the user and extract structured
information from it. Follow these rules strictly:

- Only extract information that is actually present or strongly implied
  in the text. Do not invent skills, a company name, or details not there.
- "required_skills" are skills stated as mandatory/must-have.
- "nice_to_have_skills" are skills stated as a bonus/plus/preferred.
- "keywords" are important terms an Applicant Tracking System (ATS)
  might search for (technologies, certifications, methodologies).
- If seniority is not explicitly stated, infer it from years of experience
  or responsibilities described.
- Keep "summary" to 2-3 sentences, in your own words.
""" + UNTRUSTED_DATA_RULE


def analyze_job_description(jd_text: str) -> JDAnalysis:
    """Run the JD Analyzer agent and return a structured JDAnalysis object."""
    logger.info("Analyzing job description (%d characters)", len(jd_text))

    llm = get_llm(temperature=0.1)
    structured_llm = llm.with_structured_output(JDAnalysis)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=wrap_untrusted("job_description", jd_text)),
    ]

    result = invoke_with_retry(structured_llm, messages)

    logger.info(
        "JD analysis complete: title=%s, seniority=%s, %d required skills",
        result.job_title,
        result.seniority,
        len(result.required_skills),
    )
    return result