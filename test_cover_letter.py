from app.agents.cover_letter_writer import write_cover_letter
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
letter = write_cover_letter(tailored.tailored_cv, jd_analysis)

print("=== COVER LETTER ===")
print(letter.cover_letter)
print("\nWord count:", letter.word_count)
print("Tone used:", letter.tone_used)

print("\n=== SAFETY CHECK ===")
forbidden = ["Docker", "Kubernetes", "AWS", "machine learning", "team lead"]
for word in forbidden:
    if word.lower() in letter.cover_letter.lower():
        print(f"WARNING: '{word}' appears but was NOT in the original CV!")
    else:
        print(f"OK: '{word}' correctly absent")