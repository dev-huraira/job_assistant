import httpx

BASE_URL = "http://127.0.0.1:8000"

with httpx.Client(base_url=BASE_URL, timeout=30) as client:
    print(">>> 1. Every response carries an X-Request-ID")
    r = client.get("/health")
    rid = r.headers.get("x-request-id")
    print(r.status_code, "request id:", rid)
    assert rid and len(rid) == 12

    print("\n>>> 2. A safe client-supplied ID is echoed back")
    r = client.get("/health", headers={"X-Request-ID": "my-test-id-123"})
    print("echoed:", r.headers.get("x-request-id"))
    assert r.headers.get("x-request-id") == "my-test-id-123"

    print("\n>>> 3. An unsafe client-supplied ID is replaced")
    r = client.get("/health", headers={"X-Request-ID": "bad id with spaces!"})
    print("replaced with:", r.headers.get("x-request-id"))
    assert r.headers.get("x-request-id") != "bad id with spaces!"

    print("\n>>> 4. Readiness check (hits the database)")
    r = client.get("/ready")
    print(r.status_code, r.json())
    assert r.status_code == 200 and r.json() == {"status": "ready"}

    print("\n>>> 5. Errors still carry the request ID")
    r = client.get("/applications/does-not-exist")
    print(r.status_code, r.json(), "request id:", r.headers.get("x-request-id"))
    assert r.status_code == 404
    assert r.headers.get("x-request-id")

print("\nAll API observability tests passed!")