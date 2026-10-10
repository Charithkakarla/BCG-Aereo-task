# Bulk Certificate Generator Backend API 🎓

A production-ready, asynchronous Python backend API built with **FastAPI**, **SQLAlchemy**, and **ReportLab** designed to accept bulk certificate generation requests, validate recipient data, render professional vector PDF certificates, track job progress in real-time, and handle partial batch failures gracefully.

---

## 📋 Table of Contents
1. [Objective & Problem Statement](#-objective--problem-statement)
2. [Assignment Requirements & Implementation Mapping](#-assignment-requirements--implementation-mapping)
3. [Technology Stack](#-technology-stack)
4. [System Architecture & Storage Design](#-system-architecture--storage-design)
5. [Database Schema](#-database-schema)
6. [Getting Started & Setup](#-getting-started--setup)
7. [Running with SQLite or PostgreSQL](#-running-with-sqlite-or-postgresql)
8. [Running Automated Tests](#-running-automated-tests)
9. [API Reference & Usage Examples](#-api-reference--usage-examples)
10. [Web UI Dashboard](#-web-ui-dashboard)
11. [Design & Architectural Decisions](#-design--architectural-decisions)
12. [Interview FAQ & Scaling Strategy](#-interview-faq--scaling-strategy)

---

## 🎯 Objective & Problem Statement

Organizations hosting courses, events, or workshops frequently need to generate certificates for hundreds or thousands of participants at once. Rather than requiring clients to issue individual API calls per participant, this backend system:
- Accepts a single bulk generation request containing event metadata and an array of recipients.
- Validates each recipient's data format.
- Dispatches asynchronous background generation so the API client is not blocked.
- Isolates errors so that a single invalid recipient record does **not** abort or prevent the remaining certificates from generating.
- Provides real-time job progress tracking and statistics (processed, successful, failed).
- Supports single PDF downloads as well as bulk `.zip` bundle archive downloads.

---

## 🧩 Assignment Requirements & Implementation Mapping

| Assignment Requirement | Implementation in Project | File & Method Reference |
|---|---|---|
| **Bulk API Processing** | Accepts a single payload with metadata + recipient array; returns HTTP `202 Accepted` immediately with a `job_id`. | [`app/api/routes.py: create_certificate_job`](file:///c:/Users/nanir/OneDrive/Desktop/Projects/BCG-Aereo-task/app/api/routes.py) |
| **Input & Recipient Validation** | Pydantic validation for job metadata; recipient-level validation during batch iteration to catch invalid email formats and empty names. | [`app/schemas.py`](file:///c:/Users/nanir/OneDrive/Desktop/Projects/BCG-Aereo-task/app/schemas.py), [`app/services/job_processor.py`](file:///c:/Users/nanir/OneDrive/Desktop/Projects/BCG-Aereo-task/app/services/job_processor.py) |
| **Predefined Certificate Template** | Vector-drawn landscape A4 template featuring double ornate borders, issuer header, recipient styling, gold seal badge, credential ID, and signature line. | [`app/services/certificate_generator.py: generate_pdf_certificate`](file:///c:/Users/nanir/OneDrive/Desktop/Projects/BCG-Aereo-task/app/services/certificate_generator.py) |
| **Status & Progress Tracking** | Real-time endpoint tracking `total_recipients`, `processed_count`, `success_count`, `failure_count`, status transitions, and progress percentages. | [`app/api/routes.py: get_job_status`](file:///c:/Users/nanir/OneDrive/Desktop/Projects/BCG-Aereo-task/app/api/routes.py) |
| **Certificate Retrieval** | Endpoints for previewing/downloading individual PDFs and downloading all successful certificates in a compressed `.zip` archive. | [`app/api/routes.py: download_certificate`](file:///c:/Users/nanir/OneDrive/Desktop/Projects/BCG-Aereo-task/app/api/routes.py), [`download_all_job_certificates`](file:///c:/Users/nanir/OneDrive/Desktop/Projects/BCG-Aereo-task/app/api/routes.py) |
| **Partial Failure Handling** | Individual recipient try-catch isolation. Valid recipients succeed even if others in the batch have malformed emails or data errors. Status marked `PARTIALLY_FAILED`. | [`app/services/job_processor.py: process_bulk_certificate_job`](file:///c:/Users/nanir/OneDrive/Desktop/Projects/BCG-Aereo-task/app/services/job_processor.py) |
| **Relational Database** | SQLAlchemy ORM configured for SQLite (zero-setup default) and seamlessly switchable to PostgreSQL via `DATABASE_URL`. | [`app/database.py`](file:///c:/Users/nanir/OneDrive/Desktop/Projects/BCG-Aereo-task/app/database.py), [`app/models.py`](file:///c:/Users/nanir/OneDrive/Desktop/Projects/BCG-Aereo-task/app/models.py) |
| **Automated Testing** | 100% passing Pytest suite testing creation, validation, rendering, polling, failure isolation, and downloads. | [`tests/test_api.py`](file:///c:/Users/nanir/OneDrive/Desktop/Projects/BCG-Aereo-task/tests/test_api.py) |

---

## 🛠️ Technology Stack

| Layer | Component | Version / Tech | Justification |
|---|---|---|---|
| **Language** | Python | 3.12+ | Clean, readable syntax and rich ecosystem for document generation. |
| **Web Framework** | FastAPI | >= 0.110.0 | High performance, native async support, built-in BackgroundTasks, automatic interactive Swagger UI (`/docs`). |
| **ORM & Database** | SQLAlchemy | >= 2.0.28 | Type-safe queries, supports both SQLite and PostgreSQL without altering business logic. |
| **PostgreSQL Driver**| psycopg2-binary| >= 2.9.9 | Production-grade PostgreSQL database driver. |
| **Data Validation** | Pydantic v2 | >= 2.6.4 | High-speed data parsing, schema enforcement, and descriptive error messages. |
| **PDF Generation** | ReportLab | >= 4.1.0 | Standard Python vector PDF graphics library; generates printable, crisp PDFs without external browser dependencies. |
| **Automated Tests** | Pytest | >= 8.1.1 | Unit & integration test execution with fixtures and in-memory DB isolation. |

---

## 📂 Project Architecture

```
BCG-Aereo-task/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI initialization, CORS, routing & favicon handler
│   ├── config.py               # Settings, storage directory paths, DB connection string
│   ├── database.py             # SQLAlchemy engine, session maker, get_db generator
│   ├── models.py               # Database ORM models (JobModel, CertificateModel)
│   ├── schemas.py              # Pydantic request & response validation schemas
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # REST API endpoints (Jobs, Certificates, Downloads)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── certificate_generator.py # ReportLab PDF canvas drawing service
│   │   └── job_processor.py         # Async background batch processor with error isolation
│   └── static/
│       └── index.html          # Interactive Web UI Dashboard
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures and isolated in-memory test database
│   └── test_api.py             # Comprehensive test cases covering all criteria
├── storage/                    # Output directory for SQLite DB, PDFs, and ZIP bundles
│   ├── certificates/           # storage/certificates/<job_id>/<certificate_id>.pdf
│   └── zips/                   # storage/zips/job_<job_id>.zip
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git exclusions (venv, storage, caches)
└── README.md                   # Comprehensive project documentation
```

---

## 🗄️ Database Schema & Storage Separation

### 1. Architectural Strategy: Relational Metadata vs. Binary Files
- **PostgreSQL / SQLite Database**: Stores structured records, job status flags, recipient details, verification codes, error reasons, and timestamps.
- **Local Disk (or S3 in Production)**: Stores raw binary PDF files and `.zip` archives.
- **Why this separation?** Storing large binary BLOBs inside database tables causes rapid database table bloat, slow queries, heavy RAM usage, and difficult backups. Storing file paths in the database and streaming files directly from disk (or object storage) yields optimal database and web server performance.

### 2. Entity Relational Model

```
+------------------------------------+          +------------------------------------+
|               jobs                 |          |            certificates            |
+------------------------------------+          +------------------------------------+
| id (PK, VARCHAR 36)                |<----1:N--| id (PK, VARCHAR 36)                |
| title (VARCHAR 255)                |          | job_id (FK, VARCHAR 36)            |
| issuer (VARCHAR 255)               |          | recipient_name (VARCHAR 255)       |
| issue_date (VARCHAR 50)            |          | recipient_email (VARCHAR 255)      |
| status (VARCHAR 20)                |          | custom_text (VARCHAR 255)          |
| total_recipients (INT)             |          | status (VARCHAR 20)                |
| processed_count (INT)              |          | certificate_number (VARCHAR 50)    |
| success_count (INT)                |          | file_path (TEXT)                   |
| failure_count (INT)                |          | error_reason (TEXT)                |
| created_at (TIMESTAMP)             |          | created_at (TIMESTAMP)             |
| completed_at (TIMESTAMP)           |          +------------------------------------+
+------------------------------------+
```

---

## 🚀 Getting Started & Setup

### 1. Prerequisites
- Python 3.10+ installed on your system.
- Git.

### 2. Virtual Environment Setup
```powershell
# 1. Clone repository & navigate to folder
cd BCG-Aereo-task

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

---

## 💾 Running with SQLite or PostgreSQL

The application supports both **SQLite** and **PostgreSQL** with zero code changes:

### Option A: Default SQLite (Zero Setup)
No database installation or setup required. By default, the application creates a lightweight local database file in `storage/certificates.db`:
```powershell
.\venv\Scripts\uvicorn app.main:app --reload
```

### Option B: PostgreSQL
If you want to run with PostgreSQL:
1. Create a database named `cert_db` in PostgreSQL.
2. Set the `DATABASE_URL` environment variable:
   ```powershell
   $env:DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/cert_db"
   ```
3. Start the server:
   ```powershell
   .\venv\Scripts\uvicorn app.main:app --reload
   ```
Table schemas will be created automatically in PostgreSQL upon startup!

---

## 🧪 Running Automated Tests

Run the complete test suite using `pytest`:

```powershell
python -m pytest tests/ -v
```

### Test Coverage Highlights:
1. `test_create_job`: Tests creating a bulk certificate generation job and receiving HTTP 202 Accepted with a unique `id`.
2. `test_input_validation`: Tests rejection of empty recipient lists, blank titles, and invalid payloads with HTTP 422.
3. `test_job_processing_and_certificate_generation`: Tests end-to-end background PDF generation, credential verification numbering (`CERT-2026-XXXX`), and file creation.
4. `test_individual_certificate_failure`: Submits a mixed batch of valid and invalid recipients. Confirms valid recipients generate PDFs successfully, invalid records log reasons, and job status becomes `PARTIALLY_FAILED`.
5. `test_retrieve_generated_certificates`: Tests retrieving generated individual PDF files and downloading the complete `.zip` archive.

---

## 📡 API Reference & Usage Examples

### 1. Submit Bulk Certificate Generation Job
**`POST /api/v1/jobs`**

#### Request:
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

#### Response (`202 Accepted`):
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

### 2. Poll Job Status & Progress
**`GET /api/v1/jobs/{job_id}`**

#### Request:
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
      "job_id": "e6a0d33b-741a-4f51-b8d4-539c36297ad2",
      "recipient_name": "Sarah Connor",
      "recipient_email": "sarah.connor@cyberdyne.io",
      "custom_text": "Distinction - Grade A+",
      "status": "SUCCESS",
      "certificate_number": "CERT-2026-9F2A",
      "download_url": "/api/v1/certificates/c1f7b0a8-382b-4d44-9ad0-4d32098d1a11/download",
      "error_reason": null,
      "created_at": "2026-10-09T17:30:00Z"
    },
    {
      "id": "d2f8c1b9-9134-40ef-8b89-6e3e3b794b22",
      "job_id": "e6a0d33b-741a-4f51-b8d4-539c36297ad2",
      "recipient_name": "Invalid Recipient Test",
      "recipient_email": "not-an-email-format",
      "custom_text": "Will trigger partial failure",
      "status": "FAILED",
      "certificate_number": null,
      "download_url": null,
      "error_reason": "Invalid email format: 'not-an-email-format'.",
      "created_at": "2026-10-09T17:30:00Z"
    }
  ]
}
```

---

### 3. Retrieve Individual Certificate PDF
**`GET /api/v1/certificates/{certificate_id}/download?disposition=inline`**

- **Preview in Browser / Iframe**: `?disposition=inline`
- **Force Download to Disk**: `?disposition=attachment`

---

### 4. Download All Job Certificates (ZIP Archive)
**`GET /api/v1/jobs/{job_id}/download-all`**

Returns a compressed `.zip` bundle containing all successfully rendered PDF certificates for the batch.

---

## 💻 Web UI Dashboard

An interactive dashboard is available at **`http://localhost:8000/`**:
- **Form Card**: Easily paste or edit JSON recipient arrays with test records.
- **Live Monitor Card**: Displays real-time progress bar polling, total / processed / success / failed statistics.
- **In-Browser PDF Preview**: Displays generated certificates inside an embedded modal popup with vector crispness.
- **One-Click Download Buttons**: Direct download for individual certificates or the entire batch ZIP bundle.

---

## 🏛️ Design & Architectural Decisions

### 1. Asynchronous Background Processing
- **Problem**: Generating hundreds of PDF files synchronously inside an HTTP request will exceed gateway timeouts (e.g. 30s or 60s) and block the server thread.
- **Solution**: The API accepts the batch payload, writes initial `PENDING` records to the database, schedules generation via FastAPI's `BackgroundTasks`, and returns HTTP `202 Accepted` within milliseconds. Clients poll the job endpoint or observe the live progress bar.

### 2. Resilient Error Isolation
- **Problem**: In real-world datasets, a single misspelled email address or malformed record should never cause the entire bulk job to fail or discard valid certificates.
- **Solution**: Each recipient is generated inside an isolated `try...except` block. A failure on record $N$ records the failure reason and increments `failure_count`, while record $N+1$ continues executing. If some succeed and some fail, the job status cleanly reflects `PARTIALLY_FAILED`.

### 3. High-Quality Vector PDF Rendering
- **Problem**: HTML-to-image or raster libraries often yield blurry text when printed and require heavy headless browser binaries (e.g., Chromium or wkhtmltopdf).
- **Solution**: ReportLab renders pure vector graphics and standard Helvetica/Times fonts directly into PDF format. It runs anywhere with zero operating system dependencies and produces ultra-crisp, print-ready certificates.

---

## 🎤 Interview FAQ & Scaling Strategy

### Q1: How would you scale this to handle 100,000+ recipients per job?
> **Answer**: For enterprise scale:
> 1. Replace in-process `BackgroundTasks` with a distributed task queue like **Celery** backed by **Redis** or **RabbitMQ**.
> 2. Partition large recipient lists into chunks of 100 and distribute them across multiple Celery worker containers.
> 3. Store generated PDFs in an S3-compatible object store (Amazon S3 or MinIO) using pre-signed URLs rather than local disk.

### Q2: Why did you choose FastAPI over Django or Flask?
> **Answer**: 
> - FastAPI provides native asynchronous request handling and non-blocking I/O.
> - Automatic request validation using Pydantic eliminates manual boilerplate.
> - Interactive OpenAPI documentation (`/docs`) makes reviewing and testing endpoints immediate.
> - Lightweight footprint with zero unnecessary overhead.

---

## 📄 License
This repository was developed for the BCG & Aereo Backend Assignment. All rights reserved.
