import logging

from app.core.logging_config import RequestIdFilter, request_id_var
from app.core.observability import resolve_request_id, setup_tracing, timed_node


class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())


# --- RequestIdFilter ---
record = logging.LogRecord("t", logging.INFO, __file__, 1, "msg", None, None)
RequestIdFilter().filter(record)
assert record.request_id == "-", record.request_id

token = request_id_var.set("abc123")
record2 = logging.LogRecord("t", logging.INFO, __file__, 1, "msg", None, None)
RequestIdFilter().filter(record2)
request_id_var.reset(token)
assert record2.request_id == "abc123", record2.request_id
print("RequestIdFilter OK (default '-', picks up the current ID)")

# --- resolve_request_id ---
assert resolve_request_id("my-id_123") == "my-id_123"
generated = resolve_request_id(None)
assert len(generated) == 12
bad = resolve_request_id("bad id with spaces")
assert bad != "bad id with spaces" and len(bad) == 12
too_long = resolve_request_id("x" * 100)
assert len(too_long) == 12
print("resolve_request_id OK (keeps safe IDs, replaces unsafe ones)")

# --- timed_node ---
handler = ListHandler()
node_logger = logging.getLogger("app.core.observability")
node_logger.setLevel(logging.INFO)
node_logger.addHandler(handler)


@timed_node("demo")
def good_node(state):
    return {"ok": True}


@timed_node("broken")
def bad_node(state):
    raise ValueError("boom")


assert good_node({}) == {"ok": True}
assert any("Node demo finished in" in m for m in handler.messages)

try:
    bad_node({})
    raise AssertionError("bad_node should have re-raised ValueError")
except ValueError:
    pass
assert any("Node broken failed after" in m for m in handler.messages)
print("timed_node OK (logs success, logs failure, re-raises)")

# --- setup_tracing ---
enabled = setup_tracing()
print("setup_tracing returned:", enabled, "(True only if LANGSMITH_TRACING=true and a key is set)")

print("\nAll observability unit tests passed!")