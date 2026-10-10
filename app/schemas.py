from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.models import JobStatus, CertificateStatus

class RecipientInput(BaseModel):
    name: str = Field(..., description="Full name of recipient")
    email: str = Field(..., description="Email address of recipient")
    custom_text: Optional[str] = Field(None, description="Optional custom text or grade")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if v is None:
            return ""
        return str(v).strip()

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if v is None:
            return ""
        return str(v).strip()

class JobCreateRequest(BaseModel):
    title: str = Field(..., description="Title of course or event", min_length=1, max_length=255)
    issuer: str = Field(..., description="Organization issuing the certificate", min_length=1, max_length=255)
    issue_date: str = Field(..., description="Issue date (e.g. YYYY-MM-DD or October 9, 2026)")
    recipients: List[RecipientInput] = Field(..., description="List of recipient details", min_length=1)

    @field_validator("title", "issuer", "issue_date")
    @classmethod
    def not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Field cannot be empty")
        return v

class CertificateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    recipient_name: str
    recipient_email: str
    custom_text: Optional[str] = None
    status: CertificateStatus
    certificate_number: Optional[str] = None
    download_url: Optional[str] = None
    error_reason: Optional[str] = None
    created_at: datetime

class JobProgressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    issuer: str
    issue_date: str
    status: JobStatus
    total_recipients: int
    processed_count: int
    success_count: int
    failure_count: int
    progress_percentage: float
    created_at: datetime
    completed_at: Optional[datetime] = None
    download_zip_url: Optional[str] = None
    certificates: List[CertificateResponse] = []

class JobListResponse(BaseModel):
    total_jobs: int
    jobs: List[JobProgressResponse]
