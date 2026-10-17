from app.agents.cv_tailor import tailor_cv
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

jd_analysis = analyze_job_description(SAMPLE_JD)
tailored = tailor_cv(SAMPLE_CV, jd_analysis)

print("=== TAILORED CV ===")
print(tailored.tailored_cv)
print("\n=== CHANGES MADE ===")
for change in tailored.changes_made:
    print("-", change)

print("\n=== SAFETY CHECK ===")
forbidden = ["Docker", "AWS", "Kubernetes", "machine learning"]
for word in forbidden:
    if word.lower() in tailored.tailored_cv.lower():
        print(f"WARNING: '{word}' appears but was NOT in the original CV!")
    else:
        print(f"OK: '{word}' correctly absent")