from app.agents.jd_analyzer import analyze_job_description
from app.core.logging_config import setup_logging

setup_logging()

SAMPLE_JD = """
We are hiring a Backend Developer (Mid-Level) at Acme Corp.

Requirements:
- 3+ years of experience with Python
- Strong knowledge of REST API design
- Experience with PostgreSQL
- Familiarity with Docker is a plus
- Experience with AWS is a plus

You will work closely with our frontend team to build scalable services.
We offer a fast-paced startup environment.
"""

analysis = analyze_job_description(SAMPLE_JD)

print("Job title:", analysis.job_title)
print("Seniority:", analysis.seniority)
print("Company:", analysis.company_name)
print("Required skills:", analysis.required_skills)
print("Nice to have:", analysis.nice_to_have_skills)
print("Keywords:", analysis.keywords)
print("Tone:", analysis.tone)
print("Summary:", analysis.summary)