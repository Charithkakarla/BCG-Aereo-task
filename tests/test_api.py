import os
from pathlib import Path
from app.services.job_processor import process_bulk_certificate_job

def test_creating_a_generation_job(client):
    """
    Requirement 1: Creating a generation job.
    Submits a bulk certificate generation request and verifies 202 Accepted response.
    """
    payload = {
        "title": "Data Engineering & AI Masterclass",
        "issuer": "BCG Learning Academy",
        "issue_date": "2026-10-09",
        "recipients": [
            {"name": "Alice Smith", "email": "alice@example.com", "custom_text": "Distinction"},
            {"name": "Bob Jones", "email": "bob@example.com"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "id" in data
    assert data["title"] == payload["title"]
    assert data["total_recipients"] == 2
    assert data["status"] in ["PENDING", "PROCESSING", "COMPLETED"]

def test_input_validation(client):
    """
    Requirement 2: Input validation.
    Verifies that empty recipient lists, blank titles, or invalid payloads are rejected with HTTP 422.
    """
    # 1. Empty recipient list rejected
    response = client.post("/api/v1/jobs", json={
        "title": "Course",
        "issuer": "BCG",
        "issue_date": "2026-10-09",
        "recipients": []
    })
    assert response.status_code == 422 # Unprocessable Entity

    # 2. Blank title rejected
    response = client.post("/api/v1/jobs", json={
        "title": "   ",
        "issuer": "BCG",
        "issue_date": "2026-10-09",
        "recipients": [{"name": "Alice", "email": "alice@example.com"}]
    })
    assert response.status_code == 422

def test_certificate_generation(client, db_session):
    """
    Requirement 3: Certificate generation.
    Verifies that certificates are generated based on the predefined template with recipient info.
    """
    payload = {
        "title": "Python Developer Certification",
        "issuer": "Aereo Academy",
        "issue_date": "October 2026",
        "recipients": [
            {"name": "Charlie Brown", "email": "charlie@example.com", "custom_text": "Grade A"}
        ]
    }
    create_res = client.post("/api/v1/jobs", json=payload)
    assert create_res.status_code == 202
    job_id = create_res.json()["id"]

    # Process job synchronously
    process_bulk_certificate_job(job_id, db=db_session)

    status_res = client.get(f"/api/v1/jobs/{job_id}")
    job_data = status_res.json()
    cert = job_data["certificates"][0]

    assert cert["recipient_name"] == "Charlie Brown"
    assert cert["status"] == "SUCCESS"
    assert cert["certificate_number"].startswith("CERT-")
    assert cert["download_url"] is not None

def test_job_status_progress(client, db_session):
    """
    Requirement 4: Job status/progress.
    Verifies that the client can check the progress/result of the request.
    """
    payload = {
        "title": "Cloud Architecture Program",
        "issuer": "BCG Academy",
        "issue_date": "2026-10-09",
        "recipients": [
            {"name": "User One", "email": "user1@example.com"},
            {"name": "User Two", "email": "user2@example.com"}
        ]
    }
    create_res = client.post("/api/v1/jobs", json=payload)
    job_id = create_res.json()["id"]

    # Initial status check (PENDING or PROCESSING)
    initial_res = client.get(f"/api/v1/jobs/{job_id}")
    assert initial_res.status_code == 200
    assert initial_res.json()["total_recipients"] == 2

    # Run processing
    process_bulk_certificate_job(job_id, db=db_session)

    # Completed status check
    completed_res = client.get(f"/api/v1/jobs/{job_id}")
    data = completed_res.json()
    assert data["status"] == "COMPLETED"
    assert data["total_recipients"] == 2
    assert data["processed_count"] == 2
    assert data["success_count"] == 2
    assert data["failure_count"] == 0
    assert data["progress_percentage"] == 100.0
    assert data["completed_at"] is not None

def test_handling_individual_certificate_failure(client, db_session):
    """
    Requirement 5: Handling an individual certificate failure.
    Verifies that a failure while generating one certificate does not prevent other valid
    certificates in the same job from being generated.
    """
    payload = {
        "title": "Resilient Systems Engineering",
        "issuer": "BCG & Aereo",
        "issue_date": "2026-10-09",
        "recipients": [
            {"name": "Valid Recipient One", "email": "valid1@example.com"},
            {"name": "Invalid Recipient Two", "email": "not-a-valid-email-format"}, # Invalid format
            {"name": "Valid Recipient Three", "email": "valid3@example.com"}
        ]
    }
    create_res = client.post("/api/v1/jobs", json=payload)
    assert create_res.status_code == 202
    job_id = create_res.json()["id"]

    # Run processing
    process_bulk_certificate_job(job_id, db=db_session)

    status_res = client.get(f"/api/v1/jobs/{job_id}")
    job_data = status_res.json()

    # Total = 3, Success = 2, Failure = 1 -> Status = PARTIALLY_FAILED
    assert job_data["status"] == "PARTIALLY_FAILED"
    assert job_data["total_recipients"] == 3
    assert job_data["processed_count"] == 3
    assert job_data["success_count"] == 2
    assert job_data["failure_count"] == 1

    # Check recipient statuses
    certs = job_data["certificates"]
    failed_certs = [c for c in certs if c["status"] == "FAILED"]
    success_certs = [c for c in certs if c["status"] == "SUCCESS"]

    assert len(failed_certs) == 1
    assert len(success_certs) == 2
    assert failed_certs[0]["recipient_name"] == "Invalid Recipient Two"
    assert "Invalid email format" in failed_certs[0]["error_reason"]

def test_retrieving_generated_certificates(client, db_session):
    """
    Requirement 6: Retrieving generated certificates.
    Verifies that generated certificates can be retrieved individually and as a ZIP bundle.
    """
    payload = {
        "title": "Cloud Native Architecture",
        "issuer": "BCG Cloud Labs",
        "issue_date": "2026-10-09",
        "recipients": [
            {"name": "Diana Prince", "email": "diana@example.com"}
        ]
    }
    create_res = client.post("/api/v1/jobs", json=payload)
    assert create_res.status_code == 202
    job_id = create_res.json()["id"]

    process_bulk_certificate_job(job_id, db=db_session)

    status_res = client.get(f"/api/v1/jobs/{job_id}")
    job_data = status_res.json()
    cert_id = job_data["certificates"][0]["id"]

    # 1. Download Individual PDF
    pdf_res = client.get(f"/api/v1/certificates/{cert_id}/download")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 0 # PDF binary content exists

    # 2. Download ZIP bundle
    zip_res = client.get(f"/api/v1/jobs/{job_id}/download-all")
    assert zip_res.status_code == 200
    assert zip_res.headers["content-type"] == "application/zip"
    assert len(zip_res.content) > 0
