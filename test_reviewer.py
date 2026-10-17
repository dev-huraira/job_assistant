from app.agents.cover_letter_writer import write_cover_letter
from app.agents.cv_tailor import tailor_cv
from app.agents.jd_analyzer import analyze_job_description
from app.agents.reviewer import review_application
from app.core.logging_config import setup_logging

setup_logging()

SAMPLE_JD = """
We are hiring a Backend Developer (Mid-Level) at Acme Corp.

Requirements:
- 3+ years of experience with Python
- Strong knowledge of REST API design
- Experience with PostgreSQL
- Familiarity with Docker is a plus
"""

SAMPLE_CV = """
Jane Doe
Software Engineer

Experience:
TechStart Inc, Software Engineer (2021-2024)
- Built internal tools using Python and Flask
- Designed and maintained REST APIs for the mobile team
- Worked with PostgreSQL for data storage
- Wrote unit tests using pytest

Skills: Python, Flask, PostgreSQL, Git, pytest
"""

print(">>> Running full pipeline: JD -> Tailor -> Letter -> Review")

jd_analysis = analyze_job_description(SAMPLE_JD)
tailored = tailor_cv(SAMPLE_CV, jd_analysis)
letter = write_cover_letter(tailored.tailored_cv, jd_analysis)
review = review_application(SAMPLE_CV, tailored.tailored_cv, letter.cover_letter, jd_analysis)

print("\n=== REVIEW RESULT (honest run) ===")
print("Score:", review.score)
print("Truthful:", review.truthful)
print("Keyword coverage:", review.keyword_coverage)
print("Approved:", review.approved)
print("Issues:", review.issues)
print("Suggestions:", review.suggestions)

print("\n>>> Now testing: reviewer should catch a fabricated CV")

FAKE_TAILORED_CV = tailored.tailored_cv + "\n- Led a team of 5 engineers using Kubernetes and AWS"

bad_review = review_application(
    SAMPLE_CV, FAKE_TAILORED_CV, letter.cover_letter, jd_analysis
)

print("\n=== REVIEW RESULT (fabricated run) ===")
print("Score:", bad_review.score)
print("Truthful:", bad_review.truthful)
print("Approved:", bad_review.approved)
print("Issues:", bad_review.issues)

assert bad_review.truthful is False, "Reviewer FAILED to catch the fabrication!"
assert bad_review.approved is False, "Reviewer approved a fabricated CV!"
print("\nReviewer correctly caught the fabrication.")