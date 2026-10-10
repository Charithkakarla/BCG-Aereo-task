# Bulk Certificate Generator API

A REST API for generating certificates for multiple recipients through a single bulk request.

The system validates recipient data, creates a generation job, processes certificates independently in the background, tracks real-time progress and failures, and provides APIs to retrieve generated certificates.

Built as part of the AEREO Software Development Internship assignment.

---

## Key Features

- **Bulk Generation**: Issue hundreds or thousands of certificates in a single API call
- **Request Validation**: Strict schema and boundary validation using Pydantic v2
- **Background Processing**: Non-blocking asynchronous job execution preventing HTTP timeouts
- **Failure Isolation**: Individual recipient failures do not abort or invalidate the rest of the batch
- **Progress Tracking**: Granular job-level metrics (counts, percentages, and recipient diagnostics)
- **Flexible Retrieval**: Single PDF downloads and batch ZIP archive exports
- **Automated Test Suite**: 100% passing tests covering all assignment requirements

---

## Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Core backend runtime |
| FastAPI | High-performance asynchronous REST API framework |
| SQLAlchemy | Relational ORM with B-Tree indexed queries |
| SQLite / PostgreSQL | Database persistence (zero-setup SQLite default, production PostgreSQL ready) |
| Pydantic v2 | Request validation and schema enforcement |
| ReportLab | Vector PDF certificate rendering |
| Pytest | Automated testing suite |

---

## Architecture

```text
                    Client
                       │
                       ▼
                FastAPI REST API
                       │
                       ▼
               Request Validation
                       │
                       ▼
                 Generation Job
                       │
                       ▼
              Background Processing
                 /     │      \
                /      │       \
          Certificate Certificate Certificate
              #1          #2          #N
                \          │         /
                 \         │        /
                       Database
                         +
                    File Storage
```

The API creates a generation job and processes certificates independently in the background.

Each certificate maintains its own lifecycle status, allowing individual recipient errors (e.g., malformed email) to fail gracefully without interrupting valid records.

The database stores job metadata, recipient statuses, and error diagnostics, while generated PDF files and ZIP bundles are stored separately on disk.

---

## API Usage

### 1. Create Generation Job
`POST /api/v1/jobs`

```json
{
  "title": "AEREO Backend Workshop",
  "issuer": "AEREO Learning Academy",
  "issue_date": "October 10, 2026",
  "recipients": [
    { "name": "Alice Smith", "email": "alice@example.com", "custom_text": "Distinction" },
    { "name": "Bob Jones", "email": "bob@example.com" },
    { "name": "Invalid Recipient", "email": "not-an-email" }
  ]
}
```

Response (`202 Accepted`):
```json
{
  "id": "e6a0d33b-741a-4f51-b8d4-539c36297ad2",
  "title": "AEREO Backend Workshop",
  "status": "PENDING",
  "total_recipients": 3,
  "processed_count": 0,
  "progress_percentage": 0.0
}
```

### 2. Check Job Status & Progress
`GET /api/v1/jobs/{job_id}`

Response (`200 OK`):
```json
{
  "id": "e6a0d33b-741a-4f51-b8d4-539c36297ad2",
  "status": "PARTIALLY_FAILED",
  "total_recipients": 3,
  "processed_count": 3,
  "success_count": 2,
  "failure_count": 1,
  "progress_percentage": 100.0,
  "download_zip_url": "/api/v1/jobs/e6a0d33b-741a-4f51-b8d4-539c36297ad2/download-all",
  "certificates": [
    {
      "recipient_name": "Alice Smith",
      "status": "SUCCESS",
      "certificate_number": "CERT-2026-9F2A",
      "download_url": "/api/v1/certificates/c1f7b0a8-382b-4d44-9ad0-4d32098d1a11/download"
    },
    {
      "recipient_name": "Invalid Recipient",
      "status": "FAILED",
      "error_reason": "Invalid email format: 'not-an-email'."
    }
  ]
}
```

### 3. Retrieve Certificates
- **Single PDF Download**: `GET /api/v1/certificates/{certificate_id}/download`
- **Bulk ZIP Archive**: `GET /api/v1/jobs/{job_id}/download-all`

Interactive API Documentation:
- Swagger UI: `http://localhost:8000/docs`
- Interactive Dashboard: `http://localhost:8000/`

---

## Setup & Run

### Prerequisites
- Python 3.11+
- Git

### Installation & Run

```bash
git clone <repository-url>
cd BCG-Aereo-task

# Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the API (runs out of the box with zero-setup SQLite)
uvicorn app.main:app --reload
```

*(Optional) For PostgreSQL, configure `DATABASE_URL` in `.env`:*
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/cert_db
```

Application URLs:
- **API Base**: `http://localhost:8000`
- **Swagger Documentation**: `http://localhost:8000/docs`

---

## Testing

Run the automated test suite with pytest:

```bash
pytest -v
```

Tests cover:
- Generation job creation (`202 Accepted`)
- Input validation (empty lists, blank strings)
- Certificate generation (ReportLab vector PDF)
- Job progress and status tracking
- Individual certificate failure handling (`PARTIALLY_FAILED`)
- Certificate retrieval (individual PDF and ZIP bundle)

```text
tests/test_api.py::test_creating_a_generation_job PASSED                 [ 16%]
tests/test_api.py::test_input_validation PASSED                          [ 33%]
tests/test_api.py::test_certificate_generation PASSED                    [ 50%]
tests/test_api.py::test_job_status_progress PASSED                       [ 66%]
tests/test_api.py::test_handling_individual_certificate_failure PASSED   [ 83%]
tests/test_api.py::test_retrieving_generated_certificates PASSED         [100%]

============================== 6 passed in 0.27s ==============================
```

---

## Key Design Decisions

### Background Processing
Certificate rendering is performed asynchronously via background tasks so the HTTP endpoint responds immediately with a `job_id`. This prevents long batch requests from causing HTTP gateway timeouts (e.g. 30s proxy limits) or blocking web worker threads.

### Failure Isolation
Each recipient is validated and rendered independently in an isolated try-catch block. A failure on one certificate record does not abort the remaining records in the batch, marking the overall job as `PARTIALLY_FAILED` with clear error reasons.

### Relational Database Persistence
Uses SQLAlchemy ORM with B-Tree indexes on `job_id`, `status`, and `created_at` to provide fast $O(\log N)$ status queries and persistent state tracking across restarts.

### Decoupled Metadata & Storage Layer
The database only stores structured metadata, statuses, and file paths. Binary PDF files and ZIP archives are persisted to disk / object storage, preventing table bloat and optimizing file streaming performance.

### API Versioning
All endpoints are namespaced under `/api/v1` to support future schema iterations without breaking existing client integrations.

---

## Project Structure

```text
BCG-Aereo-task/
├── app/
│   ├── api/
│   │   └── routes.py           # REST API endpoints
│   ├── models.py               # SQLAlchemy models (Job, Certificate)
│   ├── schemas.py              # Pydantic v2 validation schemas
│   ├── services/
│   │   ├── certificate_generator.py # ReportLab PDF canvas generator
│   │   └── job_processor.py         # Async background worker & failure isolator
│   ├── static/
│   │   └── index.html          # Web UI dashboard
│   ├── config.py               # Configuration & storage paths
│   ├── database.py             # SQLAlchemy session manager & connection pool
│   └── main.py                 # FastAPI application entry point & CORS
├── tests/
│   ├── conftest.py             # Pytest fixtures & isolated in-memory DB
│   └── test_api.py             # 6 required test suites (100% passing)
├── storage/                    # Output directory for PDFs and ZIPs (auto-created)
├── requirements.txt            # Project dependencies
├── pytest.ini                  # Pytest configuration
└── README.md                   # Project documentation
```

---

## Future Scope

- **Distributed Task Queue**: Offload batch processing to Celery with Redis / RabbitMQ brokers for multi-worker horizontal scaling across server clusters.
- **Cloud Object Storage**: Persist generated certificate PDFs to AWS S3 / Google Cloud Storage with expiring pre-signed URLs instead of local disk storage.
- **Automated Email Dispatch**: Asynchronously email generated PDF certificates directly to recipient addresses upon batch completion.
- **Authentication & Rate Limiting**: Implement API key / JWT authentication and token-bucket rate limiting for secure multi-tenant deployments.
- **Dynamic Template Engine**: Support customizable Jinja2 / HTML templates with user-uploaded branding, custom fonts, and dynamic layouts.
- **Webhook Notifications**: Deliver webhook callbacks to client servers upon job completion to eliminate client polling.
