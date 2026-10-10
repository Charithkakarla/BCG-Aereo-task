import os
import zipfile
import secrets
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.config import settings
from app.models import JobModel, CertificateModel, JobStatus, CertificateStatus
from app.services.certificate_generator import generate_pdf_certificate

def generate_cert_number() -> str:
    """Generates a clean unique credential verification code."""
    random_hex = secrets.token_hex(4).upper()
    year = datetime.now(timezone.utc).year
    return f"CERT-{year}-{random_hex}"

def validate_recipient_data(name: str, email: str) -> str | None:
    """Validates individual recipient data. Returns error string if invalid, else None."""
    if not name or not name.strip():
        return "Recipient name is empty or missing."
    if not email or "@" not in email or "." not in email.split("@")[-1]:
        return f"Invalid email format: '{email}'."
    return None

def process_bulk_certificate_job(job_id: str, db: Session = None):
    """
    Background worker function to process bulk certificate generation.
    Handles recipient-level validation and individual certificate error isolation.
    """
    should_close_db = False
    if db is None:
        db = SessionLocal()
        should_close_db = True

    try:
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        if not job:
            return

        # Mark Job as PROCESSING
        job.status = JobStatus.PROCESSING.value
        db.commit()

        # Job output directory: storage/certificates/<job_id>/
        job_dir = settings.CERTIFICATES_PATH / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        offset = 0
        chunk_size = 500

        while True:
            certificates = db.query(CertificateModel).filter(
                CertificateModel.job_id == job_id
            ).order_by(CertificateModel.id).offset(offset).limit(chunk_size).all()

            if not certificates:
                break

            for cert in certificates:
                try:
                    # 1. Recipient level data validation
                    val_error = validate_recipient_data(cert.recipient_name, cert.recipient_email)
                    if val_error:
                        cert.status = CertificateStatus.FAILED.value
                        cert.error_reason = val_error
                        job.failure_count += 1
                        continue

                    # 2. Assign unique certificate ID
                    cert_number = generate_cert_number()
                    cert.certificate_number = cert_number

                    # 3. Generate PDF
                    pdf_filename = f"{cert.id}.pdf"
                    pdf_path = job_dir / pdf_filename

                    generate_pdf_certificate(
                        output_path=pdf_path,
                        recipient_name=cert.recipient_name,
                        course_title=job.title,
                        issuer=job.issuer,
                        issue_date=job.issue_date,
                        certificate_number=cert_number,
                        custom_text=cert.custom_text
                    )

                    # 4. Mark Success
                    cert.status = CertificateStatus.SUCCESS.value
                    cert.file_path = str(pdf_path)
                    job.success_count += 1

                except Exception as e:
                    # Failure isolation: catch error without stopping rest of batch
                    cert.status = CertificateStatus.FAILED.value
                    cert.error_reason = f"PDF Generation Exception: {str(e)}"
                    job.failure_count += 1

                finally:
                    job.processed_count += 1

            # Commit batch of chunk_size to database
            db.commit()
            offset += chunk_size

        # 5. Determine final job status
        if job.failure_count == 0:
            job.status = JobStatus.COMPLETED.value
        elif job.success_count > 0:
            job.status = JobStatus.PARTIALLY_FAILED.value
        else:
            job.status = JobStatus.FAILED.value

        job.completed_at = datetime.now(timezone.utc)

        # 6. Create ZIP bundle for successful certificates (optimized lightweight query)
        if job.success_count > 0:
            zip_filename = f"job_{job.id}.zip"
            zip_path = settings.ZIPS_PATH / zip_filename
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                successful_certs = db.query(
                    CertificateModel.file_path,
                    CertificateModel.recipient_name,
                    CertificateModel.certificate_number
                ).filter(
                    CertificateModel.job_id == job_id,
                    CertificateModel.status == CertificateStatus.SUCCESS.value
                ).all()
                for file_path, r_name, cert_num in successful_certs:
                    if file_path and os.path.exists(file_path):
                        # Clean arcname for inside ZIP (RecipientName_CertID.pdf)
                        safe_name = "".join(c for c in r_name if c.isalnum() or c in (' ', '_', '-')).strip()
                        arc_name = f"{safe_name}_{cert_num}.pdf"
                        zipf.write(file_path, arcname=arc_name)

        db.commit()

    finally:
        if should_close_db:
            db.close()
