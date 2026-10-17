from app.core.logging_config import setup_logging
from app.graph.workflow import build_dev_graph

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

app = build_dev_graph()

# Every run needs a unique thread_id -- this is how the checkpointer
# knows which paused conversation to resume later.
config = {"configurable": {"thread_id": "test-run-001"}}

initial_state = {
    "cv_text": SAMPLE_CV,
    "jd_text": SAMPLE_JD,
    "revision_count": 0,
}

print(">>> STEP 1: Running graph until it hits the approval checkpoint...\n")
paused_state = app.invoke(initial_state, config=config)

print("\n=== STATE AT PAUSE ===")
print("Status:", paused_state["status"])
print("Review approved:", paused_state["review"].approved)

snapshot = app.get_state(config)
print("Next node(s) waiting to run:", snapshot.next)
print("(graph is PAUSED here -- it has NOT reached END yet)")

print("\n>>> STEP 2: Simulating a human looking at the result and approving...")
print(">>> (in Plan 13, this is the moment the API's /approve endpoint fires)\n")

print(">>> STEP 3: Resuming the graph with the SAME thread_id...\n")
final_state = app.invoke(None, config=config)

print("\n=== FINAL STATE AFTER RESUME ===")
print("Status:", final_state["status"])

final_snapshot = app.get_state(config)
print("Next node(s) waiting to run:", final_snapshot.next)
print("(empty tuple means the graph has fully finished)")