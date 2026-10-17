from app.schemas.jd_analysis import JDAnalysis, SeniorityLevel
from app.schemas.review import ReviewResult
from app.schemas.state import GraphState

# --- Test JDAnalysis ---
jd = JDAnalysis(
    job_title="Backend Developer",
    seniority=SeniorityLevel.MID,
    required_skills=["Python", "PostgreSQL", "REST APIs"],
    nice_to_have_skills=["Docker"],
    keywords=["Python", "backend", "API"],
    tone="professional",
    company_name="Acme Corp",
    summary="Mid-level backend role focused on Python APIs.",
)
print("JDAnalysis OK:", jd.job_title, jd.seniority)
print(jd.model_dump_json(indent=2))

# --- Test ReviewResult ---
review = ReviewResult(
    score=82,
    truthful=True,
    keyword_coverage=0.75,
    issues=["Missing mention of Docker"],
    suggestions=["Add a line about containerization if applicable"],
    approved=True,
)
print("ReviewResult OK:", review.score, review.approved)

# --- Test invalid data (should fail) ---
try:
    ReviewResult(
        score=150,  # invalid: over 100
        truthful=True,
        keyword_coverage=0.5,
        approved=True,
    )
    print("ERROR: this should have failed validation!")
except Exception as e:
    print("Validation correctly rejected bad score:", type(e).__name__)

# --- Test GraphState ---
state: GraphState = {
    "cv_text": "John Doe, 3 years experience...",
    "jd_text": "We need a backend developer...",
    "jd_analysis": jd,
    "tailored_cv": None,
    "cover_letter": None,
    "review": None,
    "revision_count": 0,
    "status": "analyzing",
    "error": None,
}
print("GraphState OK:", state["status"], state["revision_count"])