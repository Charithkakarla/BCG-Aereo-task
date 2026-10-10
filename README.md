# Bulk Certificate Generator Backend API 🎓

A scalable, asynchronous Python backend API built with **FastAPI**, **SQLAlchemy**, and **ReportLab** designed to accept bulk certificate generation requests for a list of recipients, validate participant data, generate certificates based on a predefined template, track real-time progress, isolate partial batch errors, and provide flexible retrieval.

---

## 📋 Required Assignment Documentation Sections
1. [How to Set Up the Project](#1-how-to-set-up-the-project)
2. [How to Run the Application](#2-how-to-run-the-application)
3. [How to Run Tests](#3-how-to-run-tests)
4. [How to Submit a Certificate Generation Request](#4-how-to-submit-a-certificate-generation-request)
5. [How to Retrieve Generated Certificates](#5-how-to-retrieve-generated-certificates)
6. [Important Implementation / Design Decisions](#6-important-implementation--design-decisions)
   - [Choice & Reasoning: Synchronous vs. Background Processing](#choice--reasoning-synchronous-vs-background-processing)
   - [Validation & Partial Failure Handling Strategy](#validation--partial-failure-handling-strategy)
   - [Relational Database & Scalable Storage Architecture](#relational-database--scalable-storage-architecture)
   - [Certificate Template Design & Rendering Library](#certificate-template-design--rendering-library)
7. [System Architecture & Folder Structure](#7-system-architecture--folder-structure)
8. [Optional Improvements (Interactive Dashboard)](#8-optional-improvements-interactive-dashboard)

---

## 1. How to Set Up the Project

### Prerequisites
- **Python 3.10+** (Python 3.12 recommended)
- **Git**
- Optional: PostgreSQL (SQLite is enabled out-of-the-box with zero setup)

### Step-by-Step Installation

```powershell
# 1. Clone repository & navigate to workspace
git clone <repository_url>
cd BCG-Aereo-task

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux / macOS:
source venv/bin/activate

# 4. Install all dependencies
pip install -r requirements.txt
```

---

## 2. How to Run the Application

### Option A: Running with SQLite (Default - Zero Setup Required)
No database installation or credentials needed. The application automatically initializes an SQLite database at `storage/certificates.db`:

```powershell
.\venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Option B: Running with PostgreSQL (Production Ready)
If you want to run against a PostgreSQL server:
1. Ensure a PostgreSQL database exists (e.g. `cert_db`).
2. Set the `DATABASE_URL` environment variable:
   ```powershell
   $env:DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/cert_db"
   ```
3. Start the server:
   ```powershell
   .\venv\Scripts\uvicorn app.main:app --reload
   ```

Once started:
- 📖 **Interactive OpenAPI (Swagger) Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- 📑 **ReDoc API Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- 🌐 **Web UI Dashboard**: [http://localhost:8000/](http://localhost:8000/)

---

## 3. How to Run Tests

The automated test suite in [`tests/test_api.py`](file:///c:/Users/nanir/OneDrive/Desktop/Projects/BCG-Aereo-task/tests/test_api.py) covers all required functionality using Pytest and an isolated in-memory test database:

```powershell
# Run all tests with verbose output
python -m pytest tests/ -v
```

### Test Coverage Mapping:
| Required Test Criteria (From Assignment PDF) | Test Function Name | Status |
|---|---|---|
| **• Creating a generation job** | `test_creating_a_generation_job` | ✅ PASSED |
| **• Input validation** | `test_input_validation` | ✅ PASSED |
| **• Certificate generation** | `test_certificate_generation` | ✅ PASSED |
| **• Job status/progress** | `test_job_status_progress` | ✅ PASSED |
| **• Handling an individual certificate failure** | `test_handling_individual_certificate_failure` | ✅ PASSED |
| **• Retrieving generated certificates** | `test_retrieving_generated_certificates` | ✅ PASSED |

You can also run any specific test case:
```powershell
python -m pytest tests/test_api.py -k "test_handling_individual_certificate_failure" -v
```

---

## 4. How to Submit a Certificate Generation Request

To generate certificates in bulk, submit a `POST` request to `/api/v1/jobs`.

### Endpoint: `POST /api/v1/jobs`
- **Status Code**: `202 Accepted`

#### Example `curl` Command:
```bash
curl -X POST "http://localhost:8000/api/v1/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Advanced AI & Cloud Architecture Masterclass",
    "issuer": "BCG & Aereo Learning Academy",
    "issue_date": "October 9, 2026",
    "recipients": [
      {
        "name": "Sarah Connor",
        "email": "sarah.connor@cyberdyne.io",
        "custom_text": "Distinction - Grade A+"
      },
      {
        "name": "Alex Mercer",
        "email": "alex.mercer@gentek.com",
        "custom_text": "First Class Honors"
      },
      {
        "name": "Invalid Recipient Test",
        "email": "not-an-email-format",
        "custom_text": "Will trigger partial failure"
      }
    ]
  }'
```

#### Example Response (`202 Accepted`):
```json
{
  "id": "e6a0d33b-741a-4f51-b8d4-539c36297ad2",
  "title": "Advanced AI & Cloud Architecture Masterclass",
  "issuer": "BCG & Aereo Learning Academy",
  "issue_date": "October 9, 2026",
  "status": "PENDING",
  "total_recipients": 3,
  "processed_count": 0,
  "success_count": 0,
  "failure_count": 0,
  "progress_percentage": 0.0,
  "created_at": "2026-10-09T17:30:00Z",
  "completed_at": null,
  "download_zip_url": null,
  "certificates": [...]
}
```

---

## 5. How to Retrieve Generated Certificates

### A. Check Progress & Retrieve Status
**Endpoint**: `GET /api/v1/jobs/{job_id}`

```bash
curl -X GET "http://localhost:8000/api/v1/jobs/e6a0d33b-741a-4f51-b8d4-539c36297ad2"
```

#### Response (`200 OK`):
```json
{
  "id": "e6a0d33b-741a-4f51-b8d4-539c36297ad2",
  "title": "Advanced AI & Cloud Architecture Masterclass",
  "issuer": "BCG & Aereo Learning Academy",
  "issue_date": "October 9, 2026",
  "status": "PARTIALLY_FAILED",
  "total_recipients": 3,
  "processed_count": 3,
  "success_count": 2,
  "failure_count": 1,
  "progress_percentage": 100.0,
  "created_at": "2026-10-09T17:30:00Z",
  "completed_at": "2026-10-09T17:30:02Z",
  "download_zip_url": "/api/v1/jobs/e6a0d33b-741a-4f51-b8d4-539c36297ad2/download-all",
  "certificates": [
    {
      "id": "c1f7b0a8-382b-4d44-9ad0-4d32098d1a11",
      "recipient_name": "Sarah Connor",
      "recipient_email": "sarah.connor@cyberdyne.io",
      "status": "SUCCESS",
      "certificate_number": "CERT-2026-9F2A",
      "download_url": "/api/v1/certificates/c1f7b0a8-382b-4d44-9ad0-4d32098d1a11/download",
      "error_reason": null
    },
    {
      "id": "d2f8c1b9-9134-40ef-8b89-6e3e3b794b22",
      "recipient_name": "Invalid Recipient Test",
      "recipient_email": "not-an-email-format",
      "status": "FAILED",
      "certificate_number": null,
      "download_url": null,
      "error_reason": "Invalid email format: 'not-an-email-format'."
    }
  ]
}
```

### B. Download an Individual PDF Certificate
**Endpoint**: `GET /api/v1/certificates/{certificate_id}/download`

- **In-Browser / Iframe Preview**: `?disposition=inline`
  ```bash
  curl "http://localhost:8000/api/v1/certificates/c1f7b0a8-382b-4d44-9ad0-4d32098d1a11/download?disposition=inline"
  ```
- **Force Download to Disk**: `?disposition=attachment`
  ```bash
  curl "http://localhost:8000/api/v1/certificates/c1f7b0a8-382b-4d44-9ad0-4d32098d1a11/download?disposition=attachment" -o Certificate.pdf
  ```

### C. Download All Certificates as a ZIP Archive
**Endpoint**: `GET /api/v1/jobs/{job_id}/download-all`

Downloads a compressed `.zip` bundle containing all successfully generated PDF certificates for the batch:
```bash
curl "http://localhost:8000/api/v1/jobs/e6a0d33b-741a-4f51-b8d4-539c36297ad2/download-all" -o All_Certificates.zip
```

---

## 6. Important Implementation / Design Decisions

### Choice & Reasoning: Synchronous vs. Background Processing
* **Requirement**: *"You may choose how the generation is processed. For example, generation may be handled synchronously or through background processing. The choice and reasoning should be documented."*
* **Design Choice**: **Asynchronous Background Processing** using FastAPI's `BackgroundTasks`.
* **Reasoning**:
  1. **HTTP Gateway Timeouts**: In bulk operations with 500 to 10,000+ recipients, generating PDFs synchronously in a single request would take dozens of seconds, exceeding gateway timeout thresholds (e.g. Nginx/AWS ALB 30-60 second limit).
  2. **Non-Blocking User Experience**: The client receives an immediate HTTP `202 Accepted` response with a tracking `job_id` within milliseconds (~20 ms).
  3. **Polling & Progress Visibility**: Clients can monitor the generation process in real-time (`progress_percentage`, `processed_count`, `success_count`) instead of being left in the dark during a hung HTTP connection.

### Validation & Partial Failure Handling Strategy
* **Requirement**: *"A failure while generating one certificate should not unnecessarily prevent other valid certificates in the same job from being generated. The job status should provide enough information to identify successful and failed generations."*
* **Design Choice**: **Isolated Recipient Execution Loop**.
* **Reasoning**:
  - Request-level validation checks structural integrity (presence of title, non-empty recipient array).
  - Recipient-level validation occurs during batch processing inside an isolated `try...except` block.
  - If record $N$ has an invalid email format or empty name, it is recorded as `status="FAILED"` with the specific `error_reason`, incrementing `failure_count`.
  - Record $N+1$ continues executing without interruption.
  - Overall job transitions cleanly to:
    - `COMPLETED`: 100% of certificates generated.
    - `PARTIALLY_FAILED`: Some succeeded, some failed.
    - `FAILED`: All recipients failed.

### Relational Database & Scalable Storage Architecture
* **Requirement**: *"A relational database"*
* **Design Choice**: **Relational Database for Metadata + Disk/Object Storage for PDFs**.
* **Reasoning**:
  - **Relational Tables**: Storing structured data in PostgreSQL/SQLite (`jobs` and `certificates`) allows indexing, relationship integrity (`CASCADE` delete), and fast aggregation of progress metrics.
  - **No Database BLOBs**: Storing heavy PDF binaries directly in database tables causes rapid database table bloat, slow queries, and heavy RAM consumption. Storing file paths in the database and streaming files directly from disk (or S3) maximizes speed.
  - **B-Tree Database Indexing**: Composite indexes on `job_id`, `status`, and `created_at` guarantee $O(\log N)$ query lookups even across millions of records.
  - **Chunked Processing**: The background worker queries and commits in chunks of 500, keeping RAM usage flat ($O(1)$) and eliminating 99.8% of disk fsync write bottlenecks.

### Certificate Template Design & Rendering Library
* **Requirement**: *"Use a single predefined certificate template... The exact certificate format and generation library are up to you."*
* **Design Choice**: **ReportLab Vector PDF Generation**.
* **Reasoning**:
  - Pure Python vector rendering without external headless browser dependencies (like Chromium or wkhtmltopdf).
  - Resolution-independent, print-ready output with ornate navy and gold double borders, issuer headers, dynamic recipient underline matching name length, unique credential verification codes (`CERT-2026-XXXX`), official gold seal badge, and signature line.

---

## 7. System Architecture & Folder Structure

```
BCG-Aereo-task/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application, OpenAPI configuration & static mounting
│   ├── config.py               # Application settings, paths, DB URLs
│   ├── database.py             # SQLAlchemy engine & session management
│   ├── models.py               # ORM Models (JobModel & CertificateModel with B-Tree indexes)
│   ├── schemas.py              # Pydantic schemas (JobCreate, JobProgress, CertificateResponse)
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # REST API Endpoints (POST /jobs, GET /jobs, Downloads)
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
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest configuration
├── .gitignore                  # Git exclusions (venv, storage, caches)
└── README.md                   # Comprehensive project documentation
```

---

## 8. Optional Improvements (Interactive Dashboard)

As permitted under the *"Optional"* assignment section, an interactive web dashboard is embedded at `http://localhost:8000/`:
- **Live Form**: Pre-populated with sample valid and invalid records for rapid demonstration of partial failure handling.
- **Real-Time Polling**: Visual progress bar and counters (`Total`, `Processed`, `Success`, `Failed`).
- **In-Browser PDF Modal Preview**: Review generated certificates directly inside the browser.
- **One-Click Downloads**: Direct download of individual certificates or full ZIP archive.

---

## 📄 License
Developed for the BCG & Aereo Backend Assignment. All rights reserved.
