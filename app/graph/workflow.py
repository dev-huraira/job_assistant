from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from app.core.guardrails import find_unsupported_terms
from app.core.observability import timed_node

from app.agents.cover_letter_writer import write_cover_letter
from app.agents.cv_tailor import tailor_cv
from app.agents.jd_analyzer import analyze_job_description
from app.agents.reviewer import review_application
from app.core.config import get_settings
from app.core.logging_config import get_logger
from app.schemas.state import GraphState
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver

logger = get_logger(__name__)

@timed_node("analyze_jd")
def analyze_jd_node(state: GraphState) -> dict:
    """Node: run the JD Analyzer agent."""
    logger.info("Node: analyze_jd")
    analysis = analyze_job_description(state["jd_text"])
    return {"jd_analysis": analysis, "status": "analyzing_done"}

@timed_node("tailor_cv")
def tailor_cv_node(state: GraphState) -> dict:
    """Node: run the CV Tailor agent, using reviewer feedback if this is a revision."""
    revision_count = state.get("revision_count", 0)
    logger.info("Node: tailor_cv (revision #%d)", revision_count)

    review = state.get("review")
    feedback = review.suggestions if review else None

    tailored = tailor_cv(state["cv_text"], state["jd_analysis"], feedback=feedback)
    return {"tailored_cv": tailored.tailored_cv, "status": "tailoring_done"}

@timed_node("write_letter")
def write_letter_node(state: GraphState) -> dict:
    """Node: run the Cover Letter Writer agent, using reviewer feedback if revising."""
    revision_count = state.get("revision_count", 0)
    logger.info("Node: write_letter (revision #%d)", revision_count)

    review = state.get("review")
    feedback = review.suggestions if review else None

    letter = write_cover_letter(state["tailored_cv"], state["jd_analysis"], feedback=feedback)
    return {"cover_letter": letter.cover_letter, "status": "writing_done"}

@timed_node("review")
def review_node(state: GraphState) -> dict:
    """Node: run the Reviewer agent, then apply deterministic safety checks."""
    logger.info("Node: review")
    settings = get_settings()
    jd = state["jd_analysis"]

    review = review_application(
        state["cv_text"],
        state["tailored_cv"],
        state["cover_letter"],
        jd,
    )

    # Guardrail 1: deterministic fabrication check (does not rely on the LLM)
    unsupported = find_unsupported_terms(
        original_text=state["cv_text"],
        generated_text=state["tailored_cv"] + "\n" + state["cover_letter"],
        terms=jd.required_skills + jd.nice_to_have_skills,
    )
    if unsupported:
        names = ", ".join(unsupported)
        logger.warning("Deterministic check found unsupported terms: %s", names)
        review = review.model_copy(
            update={
                "truthful": False,
                "score": min(review.score, 40),
                "issues": review.issues
                + [f"Terms not found in the original CV appear in the output: {names}"],
                "suggestions": review.suggestions
                + [f"Remove every claim about: {names}"],
            }
        )

    # Guardrail 2: enforce the approval rule in code, not only in the prompt
    approved = review.truthful and review.score >= 75
    review = review.model_copy(update={"approved": approved})

    revision_count = state.get("revision_count", 0)

    if review.approved:
        status = "awaiting_approval"
    elif revision_count + 1 >= settings.max_revisions:
        status = "needs_manual_review"
        revision_count += 1
    else:
        status = "revising"
        revision_count += 1

    logger.info(
        "Review decision: approved=%s, status=%s, revision_count=%d",
        review.approved,
        status,
        revision_count,
    )
    return {"review": review, "revision_count": revision_count, "status": status}


def route_after_review(state: GraphState) -> str:
    """Conditional edge: decide where to go after the review node."""
    if state["status"] == "revising":
        return "revise"
    return "done"

@timed_node("await_approval")
def await_approval_node(state: GraphState) -> dict:
    """Node: this is the checkpoint node. Execution pauses BEFORE this node runs.

    When the graph is resumed (after a human approves, via the API in Plan 13),
    this node runs and marks the process as fully complete.
    """
    logger.info("Node: await_approval (resumed after human checkpoint)")
    return {"status": "completed"}


def build_graph(checkpointer=None):
    """Build and compile the full job application workflow.

    Args:
        checkpointer: a LangGraph checkpointer (e.g. MemorySaver, or a
            Postgres saver added in Plan 12). If None, the graph compiles
            without pause/resume support (same behavior as Plan 9).
    """
    graph = StateGraph(GraphState)

    graph.add_node("analyze_jd", analyze_jd_node)
    graph.add_node("tailor_cv", tailor_cv_node)
    graph.add_node("write_letter", write_letter_node)
    graph.add_node("review", review_node)
    graph.add_node("await_approval", await_approval_node)

    graph.set_entry_point("analyze_jd")
    graph.add_edge("analyze_jd", "tailor_cv")
    graph.add_edge("tailor_cv", "write_letter")
    graph.add_edge("write_letter", "review")

    graph.add_conditional_edges(
        "review",
        route_after_review,
        {
            "revise": "tailor_cv",
            "done": "await_approval",
        },
    )

    graph.add_edge("await_approval", END)

    return graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["await_approval"],
    )


def build_dev_graph():
    """Convenience builder for local dev/testing: in-memory checkpointer."""
    return build_graph(checkpointer=MemorySaver())





def build_postgres_checkpointer(database_url: str):
    """Build a production checkpointer backed by a PostgreSQL connection pool.

    Returns (checkpointer, pool) -- the caller is responsible for closing
    the pool when the application shuts down.
    """
    # psycopg (unlike SQLAlchemy) doesn't understand the "+psycopg" driver
    # suffix in the URL -- that part is purely a SQLAlchemy convention.
    psycopg_url = database_url.replace("postgresql+psycopg://", "postgresql://")

    pool = ConnectionPool(
        conninfo=psycopg_url,
        max_size=10,
        kwargs={"autocommit": True, "prepare_threshold": 0},
    )
    checkpointer = PostgresSaver(pool)
    checkpointer.setup()  # creates LangGraph's own checkpoint tables if missing
    return checkpointer, pool