import uuid

from app.core.database import SessionLocal, init_db
from app.core.logging_config import setup_logging
from app.services.run_store import create_run, get_run_by_thread_id, update_run_from_state

setup_logging()

print(">>> Creating tables (if they don't exist yet)...")
init_db()
print("Tables ready.\n")

thread_id = str(uuid.uuid4())
db = SessionLocal()

print(">>> Creating a new run...")
run = create_run(db, thread_id=thread_id, cv_text="Sample CV text", jd_text="Sample JD text")
print("Created run ID:", run.id)
print("Status:", run.status)
print("Created at:", run.created_at)

print("\n>>> Fetching it back by thread_id...")
fetched = get_run_by_thread_id(db, thread_id)
print("Fetched run ID:", fetched.id)
print("CV text matches:", fetched.cv_text == "Sample CV text")

print("\n>>> Simulating a state update (as if the graph had run)...")
fake_state = {
    "status": "awaiting_approval",
    "revision_count": 1,
    "tailored_cv": "Tailored CV text here",
    "cover_letter": "Cover letter text here",
}
updated = update_run_from_state(db, thread_id, fake_state)
print("Updated status:", updated.status)
print("Updated revision_count:", updated.revision_count)
print("Tailored CV saved:", updated.tailored_cv)

print("\n>>> Testing lookup of a non-existent thread_id...")
missing = get_run_by_thread_id(db, "does-not-exist")
print("Result:", missing)  # should print None

db.close()
print("\nDatabase test complete!")