import httpx

BASE_URL = "http://127.0.0.1:8000"
CV_PATH = "sample_cv.pdf"

JD_TEXT = """
Bank internship program (IT / Operations).

We are looking for a motivated BS Information Technology student for a summer internship.

Requirements:
- Currently enrolled in a BS IT or Computer Science program
- Good working knowledge of Microsoft Excel, Word and PowerPoint
- Basic understanding of databases and data entry accuracy
- Strong communication and teamwork skills
- Attention to detail and time management

Nice to have:
- Exposure to web technologies
- Interest in banking and financial services
"""

with httpx.Client(base_url=BASE_URL, timeout=30) as client:

    print(">>> Checking health endpoint...")
    health = client.get("/health")
    print(health.status_code, health.json())

    print("\n>>> Submitting application (full pipeline, may take a few minutes)...")
    with open(CV_PATH, "rb") as f:
        files = {"cv_file": (CV_PATH, f, "application/pdf")}
        data = {"jd_text": JD_TEXT}
        response = client.post("/applications", files=files, data=data, timeout=300)

    print("Status code:", response.status_code)
    result = response.json()
    print("Thread ID:", result["thread_id"])
    print("Status:", result["status"])
    print("Revision count:", result["revision_count"])
    print("Review:", result["review"])

    thread_id = result["thread_id"]

    print("\n>>> Fetching the application by thread_id...")
    check = client.get(f"/applications/{thread_id}")
    print("Status:", check.json()["status"])

    print("\n>>> Approving the application...")
    approve = client.post(f"/applications/{thread_id}/approve")
    print("Status code:", approve.status_code)
    print("Final status:", approve.json()["status"])

    print("\n>>> Fetching again to confirm it's fully completed...")
    final_check = client.get(f"/applications/{thread_id}")
    print("Final status:", final_check.json()["status"])

    print("\n>>> Checking approve is rejected the second time...")
    second_approve = client.post(f"/applications/{thread_id}/approve")
    print("Status code (expect 400):", second_approve.status_code)
    print("Detail:", second_approve.json()["detail"])