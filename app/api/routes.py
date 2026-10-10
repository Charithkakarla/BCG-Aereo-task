import os
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models import JobModel, CertificateModel, JobStatus, CertificateStatus
from app.schemas import (
    JobCreateRequest,
    JobProgressResponse,
    CertificateResponse,
    JobListResponse
)
from app.services.job_processor import process_bulk_certificate_job

router = APIRouter()

def build_cert_response(cert: CertificateModel, request_host: str = "") -> CertificateResponse:
    download_url = None
    if cert.status == CertificateStatus.SUCCESS.value and cert.file_path:
        download_url = f"/api/v1/certificates/{cert.id}/download"
        
    return CertificateResponse(
        id=cert.id,
        job_id=cert.job_id,
        recipient_name=cert.recipient_name,
        recipient_email=cert.recipient_email,
        custom_text=cert.custom_text,
        status=CertificateStatus(cert.status),
        certificate_number=cert.certificate_number,
        download_url=download_url,
        error_reason=cert.error_reason,
        created_at=cert.created_at
    )

def build_job_response(job: JobModel) -> JobProgressResponse:
    cert_responses = [build_cert_response(c) for c in job.certificates]
    
    progress_pct = 0.0
    if job.total_recipients > 0:
        progress_pct = round((job.processed_count / job.total_recipients) * 100.0, 2)
        
    download_zip_url = None
    zip_path = settings.ZIPS_PATH / f"job_{job.id}.zip"
    if os.path.exists(zip_path) and job.success_count > 0:
        download_zip_url = f"/api/v1/jobs/{job.id}/download-all"

    return JobProgressResponse(
        id=job.id,
        title=job.title,
        issuer=job.issuer,
        issue_date=job.issue_date,
        status=JobStatus(job.status),
        total_recipients=job.total_recipients,
        processed_count=job.processed_count,
        success_count=job.success_count,
        failure_count=job.failure_count,
        progress_percentage=progress_pct,
        created_at=job.created_at,
        completed_at=job.completed_at,
        download_zip_url=download_zip_url,
        certificates=cert_responses
    )

@router.post("/jobs", response_model=JobProgressResponse, status_code=status.HTTP_202_ACCEPTED)
def create_certificate_job(
    request: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create a bulk certificate generation job and dispatch background processing.
    """
    # 1. Create Job record
    job = JobModel(
        title=request.title,
        issuer=request.issuer,
        issue_date=request.issue_date,
        status=JobStatus.PENDING.value,
        total_recipients=len(request.recipients),
        processed_count=0,
        success_count=0,
        failure_count=0
    )
    db.add(job)
    db.flush() # populated job.id

    # 2. Create Certificate records
    for recipient in request.recipients:
        cert = CertificateModel(
            job_id=job.id,
            recipient_name=recipient.name,
            recipient_email=recipient.email,
            custom_text=recipient.custom_text,
            status=CertificateStatus.PENDING.value
        )
        db.add(cert)

    db.commit()
    db.refresh(job)

    # 3. Schedule Background Task for bulk processing
    background_tasks.add_task(process_bulk_certificate_job, job.id)

    return build_job_response(job)

@router.get("/jobs", response_model=JobListResponse)
def list_jobs(db: Session = Depends(get_db)):
    """List all certificate generation jobs."""
    jobs = db.query(JobModel).order_by(JobModel.created_at.desc()).all()
    job_responses = [build_job_response(j) for j in jobs]
    return JobListResponse(total_jobs=len(job_responses), jobs=job_responses)

@router.get("/jobs/{job_id}", response_model=JobProgressResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Check status, progress and details of a specific generation job."""
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return build_job_response(job)

@router.get("/jobs/{job_id}/download-all")
def download_all_job_certificates(job_id: str, db: Session = Depends(get_db)):
    """Download a ZIP archive containing all generated certificates for a job."""
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    zip_path = settings.ZIPS_PATH / f"job_{job.id}.zip"
    if not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="ZIP archive not found or job has no generated certificates")

    clean_title = "".join(c for c in job.title if c.isalnum() or c in (' ', '_')).strip().replace(' ', '_')
    filename = f"{clean_title}_Certificates.zip"
    
    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=filename
    )

@router.get("/certificates/{certificate_id}", response_model=CertificateResponse)
def get_certificate_metadata(certificate_id: str, db: Session = Depends(get_db)):
    """Get metadata for an individual certificate."""
    cert = db.query(CertificateModel).filter(CertificateModel.id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    return build_cert_response(cert)

@router.get("/certificates/{certificate_id}/download")
def download_certificate(
    certificate_id: str,
    disposition: str = "inline",
    db: Session = Depends(get_db)
):
    """
    Retrieve/download the generated PDF for an individual certificate.
    - disposition="inline": renders inside browser/iframe preview (default)
    - disposition="attachment": triggers direct file download save dialog
    """
    cert = db.query(CertificateModel).filter(CertificateModel.id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
        
    if cert.status != CertificateStatus.SUCCESS.value or not cert.file_path or not os.path.exists(cert.file_path):
        raise HTTPException(status_code=404, detail="Certificate file not generated or generation failed")

    safe_name = "".join(c for c in cert.recipient_name if c.isalnum() or c in (' ', '_')).strip().replace(' ', '_')
    filename = f"Certificate_{safe_name}_{cert.certificate_number}.pdf"

    content_disposition = "attachment" if disposition.lower() == "attachment" else "inline"

    return FileResponse(
        path=cert.file_path,
        media_type="application/pdf",
        filename=filename,
        content_disposition_type=content_disposition
    )
