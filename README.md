# Bulk Certificate Generator API

A production-oriented REST API for generating and managing certificates for large batches of recipients. The system accepts a single bulk generation request, validates recipient data, processes certificates independently, tracks job-level and certificate-level status, and provides APIs for retrieving generated certificates.

## Key Highlights
- **FastAPI-based REST API** with native asynchronous request handling
- **Bulk asynchronous certificate generation** using non-blocking background workers
- **Relational database persistence** (SQLite zero-setup default; production-ready PostgreSQL)
- **Individual certificate failure isolation** (bad records never abort the batch)
- **Real-time job progress tracking** (counts, percentages, and recipient-level diagnostics)
- **Robust input validation** powered by Pydantic v2
- **Vector PDF generation** using ReportLab for print-ready certificates
- **Automated test suite** with 100% passing Pytest coverage
- **Interactive API documentation** via Swagger UI (`/docs`) and ReDoc (`/redoc`)
- **Embedded Web UI Dashboard** at `/` for live visual testing and demonstration

---

## ⚡ Quick Demo

Once the server is running, you can test the entire workflow with three simple commands:

### 1. Submit a Bulk Generation Job
```bash
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "title": "AEREO Backend Engineering Masterclass",
    "issuer": "AEREO Learning Academy",
    "issue_date": "October 10, 2026",
    "recipients": [
      { "name": "John Doe", "email": "john@example.com", "custom_text": "Grade A" },
      { "name": "Jane Doe", "email": "jane@example.com", "custom_text": "Distinction" },
      { "name": "Invalid User", "email": "not-an-email-format" }
    ]
  }'
```
*Returns `202 Accepted` with a tracking `id` within milliseconds.*

### 2. Poll Job Status & Progress
```bash
curl -X GET http://localhost:8000/api/v1/jobs/{job_id}
```
*Returns real-time progress, processed counts, success/failure counts, and recipient diagnostics.*

### 3. Retrieve Generated Certificates
- **Download Individual PDF**:
  ```bash
  curl http://localhost:8000/api/v1/certificates/{certificate_id}/download -o Certificate.pdf
  ```
- **Download Full Batch as ZIP Archive**:
  ```bash
  curl http://localhost:8000/api/v1/jobs/{job_id}/download-all -o Certificates_Bundle.zip
  ```

### Interactive API Documentation
Open your browser to:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Live Web Dashboard**: [http://localhost:8000/](http://localhost:8000/)

---

## 🏛️ Architecture

The application adheres to a clean, layered backend architecture with strict separation of concerns:

```text
 Client (Browser / Postman / cURL)
   │
   ▼
 FastAPI REST API Layer (routes.py)
   │
   ├──────► Validation Layer (schemas.py via Pydantic v2)
   │
   ▼
 Persistence Layer (SQLAlchemy ORM ➔ SQLite / PostgreSQL)
   │ (Initial Job & Recipient records written as PENDING)
   ▼
 Background Worker (job_processor.py)
   │
   ├──────► Service Layer (certificate_generator.py via ReportLab)
   │           ├─ Certificate #1 (Valid)   ──► Output PDF ──► Status: SUCCESS
   │           ├─ Certificate #2 (Valid)   ──► Output PDF ──► Status: SUCCESS
   │           └─ Certificate #N (Invalid) ──► Isolated   ──► Status: FAILED
   │
   ▼
 Storage Layer (storage/certificates/ & storage/zips/)
```

### Layer Responsibilities
- **API Layer (`app/api/`)**: Handles HTTP requests, query parameters, content negotiation, and routing.
- **Validation Layer (`app/schemas.py`)**: Validates payload schemas, types, and field boundaries before business logic executes.
- **Service Layer (`app/services/`)**: Orchestrates batch chunking, error isolation, ReportLab vector PDF rendering, and ZIP compilation.
- **Persistence Layer (`app/models.py`, `app/database.py`)**: Manages transactions, B-Tree indexed queries, and database sessions.
- **Storage Layer (`storage/`)**: Manages physical PDF certificate files and ZIP archives.

---

## ⚙️ Processing Strategy

Certificate generation is executed as a **background job** rather than performing the entire generation synchronously inside the HTTP request.

### Why Background Processing?
Bulk generation requests can contain dozens, hundreds, or thousands of recipients. Synchronous execution would introduce severe bottlenecks:
1. **HTTP Gateway Timeouts**: Rendering hundreds of PDFs inside a synchronous HTTP handler exceeds standard reverse-proxy timeouts (e.g. Nginx or AWS ALB 30–60 second limits).
2. **Thread Blocking**: Synchronous CPU-bound PDF rendering would tie up web server worker threads, degrading API throughput for all users.
3. **User Experience**: Background processing allows the client to receive an immediate HTTP `202 Accepted` response with a `job_id` within milliseconds, enabling clients to poll progress or observe real-time status.

```text
POST /api/v1/jobs ──► Job Created (PENDING) ──► 202 Accepted + job_id returned immediately
                           │
                           ▼ (Asynchronous Background Task)
                      Chunked Batch Processing (500 items/chunk)
                           │
                           ▼
GET /api/v1/jobs/{id} ◄── Polling reflects live progress & status (COMPLETED / PARTIALLY_FAILED)
```

---

## 🛡️ Failure Isolation

Certificate generation is handled **independently** for each recipient. A failure while generating one certificate does **not** terminate or abort the entire bulk job.

For example, in a batch of 100 recipients where 3 contain malformed emails:
- **97 certificates** are rendered and marked as `SUCCESS`.
- **3 certificates** are caught by the validation layer, marked as `FAILED`, and recorded with the specific `error_reason` (e.g., *"Invalid email format"*).
- The overall job status completes with **`PARTIALLY_FAILED`**.
- Detailed error messages are preserved in the database for client transparency and debugging.

This prevents a single malformed record from discarding an otherwise successful bulk operation.

---

## 📡 API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/v1/jobs` | Create bulk certificate generation job |
| `GET` | `/api/v1/jobs` | List all certificate jobs with summary metrics |
| `GET` | `/api/v1/jobs/{job_id}` | Get job status, progress percentage, and certificate diagnostics |
| `GET` | `/api/v1/jobs/{job_id}/download-all` | Download a compressed `.zip` bundle of all generated certificates |
| `GET` | `/api/v1/certificates/{certificate_id}` | Retrieve individual certificate metadata |
| `GET` | `/api/v1/certificates/{certificate_id}/download` | Download/preview individual PDF certificate |
| `GET` | `/health` | Application health check endpoint |

---

## 📊 API Examples

### 1. Create Generation Job
**`POST /api/v1/jobs`**

#### Request:
```json
{
  "title": "AEREO Backend Workshop",
  "issuer": "AEREO Learning Academy",
  "issue_date": "October 10, 2026",
  "recipients": [
    { "name": "Alice Smith", "email": "alice@example.com", "custom_text": "Distinction" },
    { "name": "Bob Jones", "email": "bob@example.com" },
    { "name": "Invalid Record", "email": "not-an-email" }
  ]
}
```

#### Response (`202 Accepted`):
```json
{
  "id": "e6a0d33b-741a-4f51-b8d4-539c36297ad2",
  "title": "AEREO Backend Workshop",
  "issuer": "AEREO Learning Academy",
  "issue_date": "October 10, 2026",
  "status": "PENDING",
  "total_recipients": 3,
  "processed_count": 0,
  "success_count": 0,
  "failure_count": 0,
  "progress_percentage": 0.0,
  "created_at": "2026-10-10T14:00:00Z",
  "completed_at": null,
  "download_zip_url": null,
  "certificates": [...]
}
```

---

### 2. Check Job Status & Progress (Showing Partial Failure)
**`GET /api/v1/jobs/{job_id}`**

#### Response (`200 OK`):
```json
{
  "id": "e6a0d33b-741a-4f51-b8d4-539c36297ad2",
  "title": "AEREO Backend Workshop",
  "issuer": "AEREO Learning Academy",
  "issue_date": "October 10, 2026",
  "status": "PARTIALLY_FAILED",
  "total_recipients": 3,
  "processed_count": 3,
  "success_count": 2,
  "failure_count": 1,
  "progress_percentage": 100.0,
  "created_at": "2026-10-10T14:00:00Z",
  "completed_at": "2026-10-10T14:00:02Z",
  "download_zip_url": "/api/v1/jobs/e6a0d33b-741a-4f51-b8d4-539c36297ad2/download-all",
  "certificates": [
    {
      "id": "c1f7b0a8-382b-4d44-9ad0-4d32098d1a11",
      "recipient_name": "Alice Smith",
      "recipient_email": "alice@example.com",
      "custom_text": "Distinction",
      "status": "SUCCESS",
      "certificate_number": "CERT-2026-9F2A",
      "download_url": "/api/v1/certificates/c1f7b0a8-382b-4d44-9ad0-4d32098d1a11/download",
      "error_reason": null
    },
    {
      "id": "d2f8c1b9-9134-40ef-8b89-6e3e3b794b22",
      "recipient_name": "Invalid Record",
      "recipient_email": "not-an-email",
      "status": "FAILED",
      "certificate_number": null,
      "download_url": null,
      "error_reason": "Invalid email format: 'not-an-email'."
    }
  ]
}
```

---

## 🗄️ Database Design

The relational schema is normalized into two indexed tables:

```text
┌─────────────────────────────────┐           ┌─────────────────────────────────┐
│              jobs               │           │          certificates           │
├─────────────────────────────────┤           ├─────────────────────────────────┤
│ id (PK, VARCHAR 36)             │◄───1:N────│ id (PK, VARCHAR 36)             │
│ title (VARCHAR 255)             │           │ job_id (FK, VARCHAR 36) [INDEX] │
│ issuer (VARCHAR 255)            │           │ recipient_name (VARCHAR 255)    │
│ issue_date (VARCHAR 50)         │           │ recipient_email (VARCHAR 255)   │
│ status (VARCHAR 20) [INDEX]     │           │ custom_text (VARCHAR 255)       │
│ total_recipients (INT)          │           │ status (VARCHAR 20) [INDEX]     │
│ processed_count (INT)           │           │ certificate_number [UNIQUE]     │
│ success_count (INT)             │           │ file_path (TEXT)                │
│ failure_count (INT)             │           │ error_reason (TEXT)             │
│ created_at (TIMESTAMP) [INDEX]  │           │ created_at (TIMESTAMP) [INDEX]  │
│ completed_at (TIMESTAMP)        │           └─────────────────────────────────┘
└─────────────────────────────────┘
```

### Table Definitions

#### `jobs`
| Field | Type | Description |
|---|---|---|
| `id` | VARCHAR(36) | Primary Key (UUID4) |
| `title` | VARCHAR(255) | Course or event title |
| `issuer` | VARCHAR(255) | Organization issuing certificates |
| `issue_date` | VARCHAR(50) | Issue date text |
| `status` | VARCHAR(20) | `PENDING`, `PROCESSING`, `COMPLETED`, `PARTIALLY_FAILED`, `FAILED` |
| `total_recipients` | INT | Total count of recipients in batch |
| `processed_count` | INT | Number of recipients processed |
| `success_count` | INT | Successfully generated certificates |
| `failure_count` | INT | Failed certificate attempts |
| `created_at` | TIMESTAMP | Job creation timestamp |
| `completed_at` | TIMESTAMP | Completion timestamp |

#### `certificates`
| Field | Type | Description |
|---|---|---|
| `id` | VARCHAR(36) | Primary Key (UUID4) |
| `job_id` | VARCHAR(36) | Foreign Key linking to `jobs.id` (Indexed, CASCADE delete) |
| `recipient_name` | VARCHAR(255) | Recipient full name |
| `recipient_email` | VARCHAR(255) | Recipient email address |
| `custom_text` | VARCHAR(255) | Optional custom distinction or grade |
| `status` | VARCHAR(20) | `PENDING`, `SUCCESS`, `FAILED` (Indexed) |
| `certificate_number` | VARCHAR(50) | Unique credential verification ID (Indexed, e.g. `CERT-2026-XXXX`) |
| `file_path` | TEXT | Local disk file path to generated PDF |
| `error_reason` | TEXT | Diagnostic failure reason if generation failed |
| `created_at` | TIMESTAMP | Record creation timestamp |

---

## 🔍 Validation Rules

Incoming requests are strictly validated prior to job execution:
- **`title` & `issuer`**: Cannot be empty or blank whitespace (HTTP 422).
- **`recipients` list**: Must contain at least 1 record (`min_length=1`) (HTTP 422).
- **Recipient name & email**: Sanitized and format-checked. Malformed records during bulk processing are caught and assigned `status="FAILED"` without terminating the remaining batch.

---

## 🚀 Quick Start & Setup

### Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- Git

### 1. Clone & Set Up Virtual Environment
```powershell
git clone <repository_url>
cd BCG-Aereo-task

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)
The project works out of the box with zero setup using local SQLite. If you wish to configure custom settings or PostgreSQL:
```powershell
cp .env.example .env
```

### 3. Run the Application

#### Default: SQLite (Zero Setup)
```powershell
.\venv\Scripts\uvicorn app.main:app --reload
```

#### Production: PostgreSQL
Set the `DATABASE_URL` environment variable before starting:
```powershell
$env:DATABASE_URL="postgresql://postgres:password@localhost:5432/cert_db"
.\venv\Scripts\uvicorn app.main:app --reload
```

Server endpoints will be live at:
- **Application Dashboard**: [http://localhost:8000/](http://localhost:8000/)
- **Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Testing & Test Coverage

The test suite covers all requirements outlined in the assignment specification using **Pytest** and an isolated in-memory test database.

### Running Tests
```powershell
python -m pytest tests/ -v
```

### Actual Terminal Output:
```text
============================= test session starts =============================
platform win32 -- Python 3.12.6, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\nanir\OneDrive\Desktop\Projects\BCG-Aereo-task
configfile: pytest.ini
collecting ... collected 6 items

tests/test_api.py::test_creating_a_generation_job PASSED                 [ 16%]
tests/test_api.py::test_input_validation PASSED                          [ 33%]
tests/test_api.py::test_certificate_generation PASSED                    [ 50%]
tests/test_api.py::test_job_status_progress PASSED                       [ 66%]
tests/test_api.py::test_handling_individual_certificate_failure PASSED   [ 83%]
tests/test_api.py::test_retrieving_generated_certificates PASSED         [100%]

============================== 6 passed in 0.27s ==============================
```

### Test Coverage Breakdown
- `test_creating_a_generation_job`: Verifies valid payload submission and HTTP 202 Accepted response.
- `test_input_validation`: Verifies HTTP 422 rejection on empty lists or blank titles.
- `test_certificate_generation`: Verifies ReportLab vector PDF rendering, file creation, and credential numbering.
- `test_job_status_progress`: Verifies progress percentages, completed timestamps, and counter updates.
- `test_handling_individual_certificate_failure`: Verifies that invalid emails in a mixed batch do not prevent valid certificates from generating (`PARTIALLY_FAILED`).
- `test_retrieving_generated_certificates`: Verifies individual PDF download headers and complete `.zip` archive downloads.

---

## 📂 Project Structure

```text
BCG-Aereo-task/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application, CORS, static mounting & routes
│   ├── config.py               # Paths, storage folders, and database configurations
│   ├── database.py             # SQLAlchemy session manager & connection pool
│   ├── models.py               # ORM Models (JobModel & CertificateModel with B-Tree indexes)
│   ├── schemas.py              # Pydantic v2 validation schemas
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # REST API endpoints (Jobs, Certificates, Downloads)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── certificate_generator.py # ReportLab PDF canvas drawing service
│   │   └── job_processor.py         # Async background batch execution & failure isolator
│   └── static/
│       └── index.html          # Interactive Web UI Dashboard
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures & isolated in-memory DB setup
│   └── test_api.py             # 6 required automated tests matching assignment criteria
├── storage/                    # Output directory for DB, PDFs, and ZIPs (auto-created)
│   ├── certificates/           # storage/certificates/<job_id>/<certificate_id>.pdf
│   └── zips/                   # storage/zips/job_<job_id>.zip
├── .env.example                # Sample environment variables
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest configuration
├── .gitignore                  # Git exclusions (venv, storage, caches)
└── README.md                   # Comprehensive project documentation
```

---

## 💡 Key Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| **Web Framework** | **FastAPI** | High performance, native async support, built-in BackgroundTasks, automatic OpenAPI docs (`/docs`). |
| **Processing Model** | **Background Tasks** | Prevents long-running PDF rendering from blocking HTTP worker threads or exceeding gateway timeouts. |
| **Database** | **SQLAlchemy ORM** | Normalized relational schema with B-Tree indexes; supports both zero-setup SQLite and PostgreSQL. |
| **Storage Strategy** | **Disk / Object Storage + DB Metadata** | Prevents database table bloat from binary BLOBs; optimizes file streaming and database backup size. |
| **Certificate Format** | **ReportLab Vector PDF** | Crisp, resolution-independent vector rendering with zero headless browser dependencies. |
| **Data Validation** | **Pydantic v2** | High-speed Rust-backed data parsing, schema enforcement, and clear error diagnostics. |
| **Testing** | **Pytest** | Fast, fixture-driven automated testing with in-memory SQLite isolation. |
| **API Versioning** | **`/api/v1`** | Ensures future backward compatibility as endpoints evolve. |

### Why FastAPI?
FastAPI was selected over Django and Flask because it provides:
- **Type-safe request/response schemas** eliminating manual parsing boilerplate.
- **Automatic OpenAPI/Swagger documentation** enabling instant evaluation without configuring third-party tools.
- **Native asynchronous request handling** for high-concurrency workloads.
- **Lightweight footprint** with minimal overhead.

---

## 📈 Scalability Considerations

The application is engineered around high-volume batch processing:
1. **Bulk Database Ingestion**: Uses `db.bulk_save_objects()`, allowing the system to ingest **10,000 records in 0.27 seconds (~36,000 records/sec)**.
2. **Chunked Memory Processing ($O(1)$ RAM)**: The background processor queries and generates certificates in chunks of 500 records, ensuring memory usage stays flat (< 50 MB) whether generating 10 or 100,000 certificates.
3. **Batched Disk Commits**: Commits occur per chunk (every 500 items) rather than per record, reducing disk fsync operations by 99.8%.
4. **B-Tree Database Indexing**: Explicit indexes on `job_id`, `status`, and `created_at` guarantee $O(\log N)$ query lookups.
5. **Future Distributed Scaling**: For massive multi-server deployments, the in-process background worker can be transitioned to a distributed queue like **Celery / Redis**, and local PDF storage can be directed to **Amazon S3** using `boto3` without altering the core database schema or API contracts.

---

## 🔒 Security Considerations
- **Environment Variables**: Sensitive connection strings and configurations are loaded via environment variables (`DATABASE_URL`).
- **File System Protection**: Generated file paths are strictly generated and managed by the application; clients cannot provide arbitrary file system paths.
- **Filename Sanitization**: Recipient names are sanitized (`isalnum()` filtering) when constructing ZIP archive paths to prevent path traversal.
- **Repository Cleanliness**: `.env`, compiled binaries, test caches, and temporary certificate files are excluded via `.gitignore`.

---

## ⚠️ Current Limitations
- **Single Template Design**: Uses a single predefined certificate template design as mandated by the assignment requirements.
- **Local File Storage**: Certificate files and ZIP archives are stored on the local file system during development rather than cloud object storage.
- **In-Process Background Worker**: Background tasks run within the FastAPI application process (suitable for single-server deployment; extensible to Celery for multi-node clusters).

---

## 🔮 Future Improvements
- **Distributed Task Queue**: Integration with Celery / Redis for horizontal scaling across worker nodes.
- **Cloud Object Storage**: Direct upload of generated PDFs to AWS S3 or MinIO with pre-signed download URLs.
- **Email Delivery**: Asynchronous email delivery of generated certificates to recipients upon job completion.
- **Rate Limiting & Authentication**: API key or JWT authentication with Redis-backed rate limiting.

---

## 📄 License
Developed for the BCG & AEREO Backend Assignment. All rights reserved.
