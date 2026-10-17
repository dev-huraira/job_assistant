from app.core.logging_config import setup_logging
from app.graph.workflow import build_graph

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

app = build_graph()

initial_state = {
    "cv_text": SAMPLE_CV,
    "jd_text": SAMPLE_JD,
    "revision_count": 0,
}

print(">>> Running the full graph...\n")
final_state = app.invoke(initial_state)

print("\n=== FINAL STATE SUMMARY ===")
print("Status:", final_state["status"])
print("Revision count:", final_state["revision_count"])
print("Review approved:", final_state["review"].approved)
print("Review score:", final_state["review"].score)

print("\n=== TAILORED CV ===")
print(final_state["tailored_cv"])

print("\n=== COVER LETTER ===")
print(final_state["cover_letter"])