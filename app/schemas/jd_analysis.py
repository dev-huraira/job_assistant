from enum import Enum

from pydantic import BaseModel, Field


class SeniorityLevel(str, Enum):
    """Allowed seniority levels, used instead of free text."""

    INTERN = "intern"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"


class JDAnalysis(BaseModel):
    """Structured output of the JD Analyzer agent."""

    job_title: str = Field(..., description="The job title as written in the JD")
    seniority: SeniorityLevel = Field(..., description="Inferred seniority level")
    required_skills: list[str] = Field(
        default_factory=list,
        description="Hard skills explicitly required by the JD",
    )
    nice_to_have_skills: list[str] = Field(
        default_factory=list,
        description="Skills mentioned as a bonus, not mandatory",
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Important keywords/phrases an ATS might scan for",
    )
    tone: str = Field(
        default="professional",
        description="Tone of the job posting, e.g. formal, startup-casual",
    )
    company_name: str = Field(default="", description="Company name if mentioned")
    summary: str = Field(
        default="", description="2-3 sentence summary of what the role needs"
    )