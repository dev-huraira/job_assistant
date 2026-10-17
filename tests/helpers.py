from app.schemas.cover_letter import CoverLetterOutput
from app.schemas.cv_tailor import TailoredCVOutput
from app.schemas.jd_analysis import JDAnalysis, SeniorityLevel
from app.schemas.review import ReviewResult
from app.services.models import ApplicationRun

# A fictional candidate. Never put a real person's CV in test files.
CV_TEXT = """Jane Doe
BS Information Technology student, 2023-2027
Skills: Microsoft Excel, Microsoft Word, Microsoft PowerPoint, Database Management, Data Entry, Web Technologies
Coursework: Database Management Systems, Data Structures and Algorithms, Web Technology
Certification: Full Stack Web Development Online Course
"""

JD_TEXT = """Bank internship program (IT / Operations).
We are looking for a BS Information Technology student for a summer internship.
Requirements: Microsoft Excel, Microsoft Word, database basics, data entry accuracy, teamwork and communication.
Nice to have: web technologies.
"""

# A job the candidate above is NOT qualified for (used by the live tests).
BACKEND_JD_TEXT = """We are hiring a Backend Developer (Mid-Level) at Acme Corp.
Requirements: 3+ years of Python, strong REST API design, PostgreSQL experience.
Nice to have: Docker, AWS.
"""


# ---------- Fake LLM ----------


class FakeStructuredLLM:
    """What `llm.with_structured_output(Schema)` returns in production."""

    def __init__(self, owner, schema):
        self.owner = owner
        self.schema = schema

    def invoke(self, messages):
        return self.owner.respond(self.schema, messages)


class FakeChatModel:
    """Stands in for the Gemini client returned by get_llm()."""

    def __init__(self, owner):
        self.owner = owner

    def with_structured_output(self, schema):
        return FakeStructuredLLM(self.owner, schema)


class FakeLLM:
    """Records every call and returns canned results, per output schema.

    queue(Schema, a, b, c): calls get a, then b, then c.
    The LAST queued result repeats forever, so a single result means
    "always return this". An Exception in the queue is raised instead.
    """

    def __init__(self):
        self._queues = {}
        self.calls = []

    def queue(self, schema, *results):
        self._queues[schema] = list(results)

    def respond(self, schema, messages):
        self.calls.append((schema, messages))
        queue = self._queues.get(schema)
        if not queue:
            raise AssertionError(f"No fake response queued for {schema.__name__}")
        result = queue.pop(0) if len(queue) > 1 else queue[0]
        if isinstance(result, Exception):
            raise result
        return result

    def calls_for(self, schema):
        return [messages for called, messages in self.calls if called is schema]


# ---------- Factories for realistic canned results ----------


def make_jd_analysis(**overrides) -> JDAnalysis:
    data = {
        "job_title": "Bank IT Intern",
        "seniority": SeniorityLevel.INTERN,
        "required_skills": ["Excel", "Word", "databases"],
        "nice_to_have_skills": ["web technologies"],
        "keywords": ["Excel", "databases", "banking"],
        "tone": "professional",
        "company_name": "",
        "summary": "Internship for an IT student.",
    }
    data.update(overrides)
    return JDAnalysis(**data)


def make_tailored(text: str | None = None) -> TailoredCVOutput:
    return TailoredCVOutput(
        tailored_cv=text or CV_TEXT,
        changes_made=["Reordered skills to match the job"],
    )


def make_letter(text: str | None = None) -> CoverLetterOutput:
    body = text or (
        "Dear Hiring Manager, I am a BS IT student with solid Excel and Word skills "
        "and database coursework. I would welcome the chance to learn in your team. "
        "Sincerely, Jane Doe"
    )
    return CoverLetterOutput(
        cover_letter=body, word_count=len(body.split()), tone_used="professional"
    )


def make_review(**overrides) -> ReviewResult:
    data = {
        "score": 90,
        "truthful": True,
        "keyword_coverage": 0.9,
        "issues": [],
        "suggestions": [],
        "approved": True,
    }
    data.update(overrides)
    return ReviewResult(**data)


# ---------- Small helpers ----------


def prompt_text(messages) -> str:
    """Join all messages of one LLM call into a single searchable string."""
    return "\n".join(str(message.content) for message in messages)


def initial_state(cv_text: str = CV_TEXT, jd_text: str = JD_TEXT) -> dict:
    return {"cv_text": cv_text, "jd_text": jd_text, "revision_count": 0}


def queue_happy_path(fake, review: ReviewResult | None = None) -> None:
    """Queue one good answer for every agent (the reviewer can be overridden)."""
    fake.queue(JDAnalysis, make_jd_analysis())
    fake.queue(TailoredCVOutput, make_tailored())
    fake.queue(CoverLetterOutput, make_letter())
    fake.queue(ReviewResult, review or make_review())


def run_rows(session_factory) -> list[dict]:
    """Read every saved application run as plain dicts."""
    with session_factory() as session:
        return [
            {
                "thread_id": run.thread_id,
                "status": run.status,
                "revision_count": run.revision_count,
                "tailored_cv": run.tailored_cv,
                "cover_letter": run.cover_letter,
            }
            for run in session.query(ApplicationRun).all()
        ]