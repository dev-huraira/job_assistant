import os

# ---- Test environment. This MUST run before any `app` module is imported. ----
RUN_LIVE = os.environ.get("RUN_LIVE_TESTS") == "1"

os.environ["API_KEY"] = ""

if not RUN_LIVE:
    os.environ["GOOGLE_API_KEY"] = "test-key-not-real"  # live tests keep the real key
os.environ["DATABASE_URL"] = "sqlite://"  # never touch Neon from tests
os.environ["LANGSMITH_TRACING"] = "false"  # never send test data to LangSmith
os.environ["MAX_REVISIONS"] = "3"
os.environ["RATE_LIMIT_MAX_REQUESTS"] = "5"
os.environ["RATE_LIMIT_WINDOW_SECONDS"] = "600"
os.environ["MIN_JD_CHARS"] = "100"
os.environ["MAX_JD_CHARS"] = "10000"
os.environ["MIN_CV_CHARS"] = "100"
os.environ["MAX_CV_CHARS"] = "20000"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from langgraph.checkpoint.memory import MemorySaver  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.database import Base, get_db  # noqa: E402
from app.core.rate_limit import limiter  # noqa: E402
from app.graph.workflow import build_graph  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
from app.services import models  # noqa: E402, F401  (registers the tables on Base)
from tests.helpers import FakeChatModel, FakeLLM  # noqa: E402


def pytest_collection_modifyitems(config, items):
    """Skip tests marked `live` unless RUN_LIVE_TESTS=1."""
    if RUN_LIVE:
        return
    skip_live = pytest.mark.skip(
        reason="live test: set RUN_LIVE_TESTS=1 to call the real Gemini API"
    )
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)


@pytest.fixture
def fake_llm(monkeypatch):
    """Replace the Gemini client in every agent with a recording fake."""
    fake = FakeLLM()
    chat_model = FakeChatModel(fake)
    for module_name in ("jd_analyzer", "cv_tailor", "cover_letter_writer", "reviewer"):
        monkeypatch.setattr(
            f"app.agents.{module_name}.get_llm", lambda *args, **kwargs: chat_model
        )
    return fake


@pytest.fixture
def no_retry_delay(monkeypatch):
    """Make tenacity's waits instant, so failure tests don't take seconds."""
    monkeypatch.setattr("time.sleep", lambda seconds: None)


@pytest.fixture
def graph():
    """A fresh workflow with an in-memory checkpointer."""
    return build_graph(checkpointer=MemorySaver())


@pytest.fixture
def db_engine():
    """A throwaway in-memory SQLite database with our tables created."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session_factory(db_engine):
    return sessionmaker(bind=db_engine, autoflush=False)


@pytest.fixture
def client(fake_llm, graph, session_factory):
    """A test HTTP client wired to the fake LLM, the test DB and a test graph."""

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.state.graph = graph
    limiter._hits.clear()

    # Not used as `with TestClient(...)`, so the real startup (Neon, Postgres
    # checkpointer) never runs.
    yield TestClient(fastapi_app)

    fastapi_app.dependency_overrides.clear()
    limiter._hits.clear()