# SPRM Backend API - Complete Guide

**Malaysian Anti-Corruption Commission (SPRM) - AI-Powered Complaint Management System**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12%2B-blue)](https://www.postgresql.org/)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-Qwen_2.5_VL-orange)](https://openrouter.ai/)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Database Schema](#database-schema)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

This backend system provides a comprehensive complaint management API with AI-powered features:

1. **Complaint Submission** - Accept complaints with form data and file attachments
2. **Document Processing** - Extract text and data from images using AI vision models
3. **Data Extraction** - Automatically identify names, dates, locations, amounts
4. **5W1H Generation** - Generate comprehensive summaries in Bahasa Malaysia
5. **Sector Classification** - AI determines government sector (10 categories)
6. **Akta Determination** - AI identifies relevant Malaysian legislation
7. **CRIS/NFA Classification** - AI-powered corruption classification with confidence scores
8. **Database Storage** - Store all data in PostgreSQL with full audit trail

---

## ✨ Features

### Core Features
- ✅ Multi-field complaint form submission
- ✅ File upload support (PDF, PNG, JPG, JPEG)
- ✅ AI-powered image text extraction (OCR)
- ✅ Structured data extraction (entities, dates, amounts)
- ✅ 5W1H summary generation (Bahasa Malaysia)
- ✅ Sector classification (10 government sectors)
- ✅ Akta determination (10 Malaysian legislation types)
- ✅ CRIS/NFA classification with confidence scoring
- ✅ Background processing (non-blocking)
- ✅ PostgreSQL database with JSONB support
- ✅ RESTful API with auto-generated docs
- ✅ CORS enabled for frontend integration

### AI Features (via OpenRouter)
- 🤖 Vision model: **Qwen 2.5 VL 72B Instruct**
- 🖼️ Image text extraction and analysis
- 📊 Structured entity extraction
- 📝 Intelligent 5W1H summary generation
- 🔍 CRIS/NFA corruption classification
- 🌐 Bilingual support (Malay/English)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- OpenRouter API key (provided)

### 1. Installation

```bash
# Clone or navigate to project
cd SPRM_Backend

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Start PostgreSQL (if not running)
# Windows: services.msc → PostgreSQL
# Linux: sudo systemctl start postgresql
# Mac: brew services start postgresql

# Create database
createdb sprm_db

# Or using psql:
psql -U postgres
CREATE DATABASE sprm_db;
\q
```

### 3. Environment Configuration

The `.env` file is already configured:

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sprm_db
DB_USER=postgres
DB_PASSWORD=postgres

# OpenRouter AI (already configured)
OPENROUTER_API_KEY=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
OPENROUTER_MODEL=qwen/qwen-2.5-vl-72b-instruct
VLLM_TIMEOUT=120
```

**Note:** Update `DB_PASSWORD` if your PostgreSQL password is different.

### 4. Start the Server

```bash
python src/main.py
```

You should see:

```
🚀 Initializing OpenRouter Service...
✅ OpenRouter Service initialized (Model: qwen/qwen-2.5-vl-72b-instruct)
🚀 Initializing Classification Service...
✅ Classification Service initialized (threshold: 0.5)
✅ Database tables created successfully

============================================================
🚀 SPRM Backend API Ready!
============================================================
📝 Complaint submission: POST /complaints/submit
🔍 View complaint: GET /complaints/{id}
📋 List complaints: GET /complaints
📚 API Docs: http://localhost:8000/docs
============================================================

INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 5. Test the API

**Open API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Quick Test:**
```bash
# Health check
curl http://localhost:8000/health

# Submit a test complaint
curl -X POST "http://localhost:8000/complaints/submit" \
  -F "phone_number=012-3456789" \
  -F "complaint_title=Test Complaint" \
  -F "category=Rasuah" \
  -F "complaint_description=This is a test complaint to verify the system"
```

---

## 🔍 CRIS/NFA Classification

The system automatically classifies complaints into two categories:

### Classification Types

**CRIS (Case Requiring Investigation/Siasatan)**
- Complaints showing clear corruption indicators
- Requires formal investigation
- Examples:
  - Bribery with specific amounts
  - Abuse of power with evidence
  - Conflict of interest with documented proof

**NFA (No Further Action)**
- Complaints lacking corruption indicators
- Insufficient evidence or vague allegations
- Examples:
  - General dissatisfaction
  - Incomplete information
  - Non-corruption matters

### How Classification Works

1. **5W1H Analysis**: AI generates comprehensive summary
2. **Corruption Indicators**: System identifies:
   - Financial transactions (bribes, kickbacks)
   - Abuse of authority
   - Conflict of interest
   - Evidence of wrongdoing
   - Specific parties involved
3. **Confidence Scoring**: Returns score from 0.0 to 1.0
4. **Threshold**: Configurable via `CLASSIFICATION_THRESHOLD` (default: 0.5)

### Classification Response Fields

```json
{
  "classification": "CRIS",           // or "NFA"
  "classification_confidence": 0.92,  // 0.0 - 1.0
  "classification_reasoning": "Clear evidence of bribery with specific amount...",
  "corruption_indicators": [
    "Financial transaction (RM 50,000)",
    "Government official involved",
    "Specific date and location"
  ]
}
```

---

## 📦 Case Management System

The system automatically groups related complaints into **cases**. A case represents a single corruption incident that may have multiple complaints from different sources.

### How Auto-Grouping Works

When a complaint is processed:

1. **Similarity Search**: System searches for similar existing complaints using:
   - 5W1H summary content
   - Entity matching (names, organizations, locations)
   - Keyword similarity
   - Semantic similarity (AI embeddings)

2. **Grouping Decision**:
   - **Similarity ≥ 0.70**: Complaint added to existing case
   - **Similarity < 0.70**: New standalone case created

3. **Case Title Generation**: Auto-generated from common keywords in complaints

### Example Scenario

```
Scenario: 3 people report the same bribery incident

Complaint #1 (Ahmad): "Pegawai JKR terima rasuah RM50,000 untuk tender"
Complaint #3 (Fatimah): "Saya saksi pegawai JKR ambil wang RM50k"
Complaint #5 (Anonim): "Rasuah di JKR melibatkan tender projek"

→ System groups into:
   CASE-2025-0001: "JKR Rasuah Tender"
   ├─ Complaint #1 (similarity: 1.0 - primary)
   ├─ Complaint #3 (similarity: 0.85)
   └─ Complaint #5 (similarity: 0.78)
```

### Manual Case Management

Frontend can also:
- **Create new cases** manually
- **Move complaints** between cases
- **Split cases** into multiple cases
- **Merge cases** together
- **Update case** status/priority

---

## 📡 API Endpoints

### Base URL
```
http://localhost:8000
```

---

### 1. Submit Complaint

**Endpoint:** `POST /complaints/submit`

**Description:** Submit a new complaint with optional file attachments. Files are processed by AI to extract text and data.

**Content-Type:** `multipart/form-data`

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `full_name` | string | No | Full name of complainant |
| `ic_number` | string | No | IC/Passport number |
| `phone_number` | string | **Yes** | Contact phone (e.g., 012-3456789) |
| `email` | string | No | Email address |
| `complaint_title` | string | **Yes** | Title/subject of complaint |
| `category` | string | **Yes** | Category (e.g., Rasuah, Penyalahgunaan Kuasa) |
| `urgency_level` | string | No | Rendah/Sederhana/Tinggi/Kritikal (default: Sederhana) |
| `complaint_description` | string | **Yes** | Detailed description (min 10 chars) |
| `files` | file[] | No | Supporting documents (PDF, PNG, JPG, JPEG) |

**Response:**
```json
{
  "complaint_id": 1,
  "status": "submitted",
  "message": "Aduan berjaya diterima dan sedang diproses / Complaint successfully received and being processed",
  "submitted_at": "2025-01-27T10:30:00",
  "document_count": 2
}
```

**🚀 Performance Notes:**
- **Returns immediately** - API responds in ~1-2 seconds with complaint ID
- **Processing runs in background** - AI processing (5W1H, sector, akta, classification) happens asynchronously
- **Concurrent processing** - System can process up to 5 complaints simultaneously
- **No blocking** - Multiple users can submit complaints at the same time without waiting
- **Check status** - Use `GET /complaints/{id}` to check if processing is complete (status: "pending" → "processed")

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/complaints/submit" \
  -F "full_name=Ahmad bin Ali" \
  -F "phone_number=012-3456789" \
  -F "email=ahmad@example.com" \
  -F "complaint_title=Penyalahgunaan kuasa dalam tender" \
  -F "category=Rasuah" \
  -F "urgency_level=Tinggi" \
  -F "complaint_description=Pegawai kerajaan menerima rasuah untuk meluluskan tender" \
  -F "files=@evidence.jpg" \
  -F "files=@document.pdf"
```

**JavaScript Example:**
```javascript
const formData = new FormData();
formData.append('full_name', 'Ahmad bin Ali');
formData.append('phone_number', '012-3456789');
formData.append('complaint_title', 'Penyalahgunaan kuasa');
formData.append('category', 'Rasuah');
formData.append('complaint_description', 'Detailed description...');

// Add files
const files = document.getElementById('fileInput').files;
for (let file of files) {
  formData.append('files', file);
}

const response = await fetch('http://localhost:8000/complaints/submit', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('Complaint ID:', result.complaint_id);
```

---

### 2. Get Complaint Details

**Endpoint:** `GET /complaints/{complaint_id}`

**Description:** Retrieve detailed information about a complaint, including AI-extracted data and 5W1H summary.

**Response:**
```json
{
  "id": 1,
  "full_name": "Ahmad bin Ali",
  "ic_number": "901231-01-5678",
  "phone_number": "012-3456789",
  "email": "ahmad@example.com",
  "complaint_title": "Penyalahgunaan kuasa dalam tender",
  "category": "Rasuah",
  "urgency_level": "Tinggi",
  "complaint_description": "Detailed description...",
  "status": "processed",

  "extracted_data": {
    "entities": {
      "names": ["Ahmad bin Ali", "Dato' Rashid"],
      "organizations": ["Jabatan Kerja Raya"],
      "locations": ["Kuala Lumpur"],
      "dates": ["15 Januari 2024"],
      "amounts": ["RM 50,000"]
    },
    "summary": "Aduan rasuah melibatkan pegawai kerajaan..."
  },

  "w1h_summary": "**WHAT (Apa):** Pegawai kerajaan menerima rasuah RM 50,000...\n\n**WHO (Siapa):** Ahmad bin Ali (pegawai) dan Dato' Rashid...\n\n**WHEN (Bila):** 15 Januari 2024...\n\n**WHERE (Di mana):** Kuala Lumpur...\n\n**WHY (Mengapa):** Untuk meluluskan tender...\n\n**HOW (Bagaimana):** Menerima wang tunai...",

  "w1h_what": "Pegawai kerajaan menerima rasuah RM 50,000",
  "w1h_who": "Ahmad bin Ali (pegawai) dan Dato' Rashid (kontraktor)",
  "w1h_when": "15 Januari 2024",
  "w1h_where": "Kuala Lumpur",
  "w1h_why": "Untuk meluluskan tender projek pembinaan",
  "w1h_how": "Menerima wang tunai secara sulit",

  "sector": "Pembinaan & Infrastruktur",
  "akta": "Akta SPRM 2009",

  "classification": "CRIS",
  "classification_confidence": 0.92,

  "submitted_at": "2025-01-27T10:30:00",
  "processed_at": "2025-01-27T10:30:15",
  "has_documents": true,
  "document_count": 2,

  "documents": [
    {
      "id": 1,
      "complaint_id": 1,
      "filename": "complaint_1_20250127_103000_evidence.jpg",
      "original_filename": "evidence.jpg",
      "file_path": "uploads/complaint_1_20250127_103000_evidence.jpg",
      "file_size": 524288,
      "file_type": "image/jpeg",
      "uploaded_at": "2025-01-27T10:30:00"
    }
  ]
}
```

**Example:**
```bash
curl "http://localhost:8000/complaints/1"
```

---

### 3. List Complaints

**Endpoint:** `GET /complaints`

**Description:** List complaints with optional filtering and pagination.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status (submitted, processed) |
| `category` | string | Filter by category |
| `limit` | integer | Number of results (default: 50, max: 100) |
| `offset` | integer | Pagination offset (default: 0) |

**Response:**
```json
{
  "total": 150,
  "complaints": [
    {
      "id": 1,
      "complaint_title": "Penyalahgunaan kuasa",
      "category": "Rasuah",
      "status": "processed",
      "urgency_level": "Tinggi",
      "submitted_at": "2025-01-27T10:30:00",
      "has_documents": true
    }
  ],
  "limit": 50,
  "offset": 0
}
```

**Examples:**
```bash
# Get all complaints
curl "http://localhost:8000/complaints"

# Get processed complaints only
curl "http://localhost:8000/complaints?status=processed"

# Get complaints by category
curl "http://localhost:8000/complaints?category=Rasuah"

# Pagination
curl "http://localhost:8000/complaints?limit=20&offset=40"

# Combined filters
curl "http://localhost:8000/complaints?status=processed&category=Rasuah&limit=10"
```

---

### 4. Update Complaint

**Endpoint:** `PUT /complaints/{complaint_id}`

**Description:** Update complaint fields (manual editing by officers).

**Editable Fields:**

| Field | Description |
|-------|-------------|
| `complaint_title` | Update complaint title |
| `complaint_description` | Update description |
| `category` | Change category |
| `urgency_level` | Change urgency (Rendah/Sederhana/Tinggi/Kritikal) |
| `w1h_what` | Edit WHAT field |
| `w1h_who` | Edit WHO field |
| `w1h_when` | Edit WHEN field |
| `w1h_where` | Edit WHERE field |
| `w1h_why` | Edit WHY field |
| `w1h_how` | Edit HOW field |
| `w1h_summary` | Edit full 5W1H summary |
| `sector` | Change government sector |
| `akta` | Change relevant legislation/act |
| `classification` | Change classification (CRIS/NFA) |
| `classification_confidence` | Update confidence score |
| `status` | Change status |

**Request Body:**
```json
{
  "w1h_what": "Pegawai kerajaan menerima wang rasuah sebanyak RM100,000",
  "w1h_who": "En. Ahmad bin Ali (Pegawai JKR) dan Dato' Rashid (Kontraktor)",
  "classification": "CRIS"
}
```

**⚡ Auto Re-Processing:**
When any 5W1H field is edited, the system automatically (in background):
- ✅ Rebuilds `w1h_summary` from individual fields
- ✅ Re-classifies as CRIS/NFA based on new 5W1H
- ✅ Re-determines sector and akta
- ✅ Regenerates embedding for similarity search
- ✅ Updates all derived fields automatically

**Response:**
```json
{
  "id": 1,
  "complaint_title": "Rasuah di JKR",
  "w1h_what": "Pegawai kerajaan menerima wang rasuah sebanyak RM100,000",
  "w1h_who": "En. Ahmad bin Ali (Pegawai JKR) dan Dato' Rashid (Kontraktor)",
  "classification": "CRIS",
  // ... full complaint details
}
```

**Example:**
```bash
curl -X PUT "http://localhost:8000/complaints/1" \
  -H "Content-Type: application/json" \
  -d '{
    "w1h_what": "Updated what happened",
    "w1h_who": "Updated persons involved",
    "classification": "CRIS"
  }'
```

---

### 5. Download Document

**Endpoint:** `GET /documents/{document_id}/download`

**Description:** Download or preview an uploaded complaint document (image, PDF, etc.).

**Path Parameters:**
- `document_id` - Document ID (from complaint's `documents` array)

**Returns:** File with appropriate content-type headers for browser preview/download

**Frontend Usage:**

**Image Preview:**
```html
<img src="http://localhost:8000/documents/123/download" alt="Evidence" />
```

**Download Link:**
```html
<a href="http://localhost:8000/documents/123/download" download>
  Download Document
</a>
```

**JavaScript Fetch:**
```javascript
const downloadDocument = async (documentId) => {
  const response = await fetch(`http://localhost:8000/documents/${documentId}/download`);
  const blob = await response.blob();

  // Create download link
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'document.pdf';
  a.click();
};
```

**Example:**
```bash
curl "http://localhost:8000/documents/1/download" --output evidence.jpg
```

---

### 6. List Cases

**Endpoint:** `GET /cases`

**Description:** List all cases with optional filtering and pagination.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status (open, investigating, closed) |
| `limit` | integer | Number of results (default: 50) |
| `offset` | integer | Pagination offset (default: 0) |

**Response:**
```json
{
  "total": 25,
  "cases": [
    {
      "id": 1,
      "case_number": "CASE-2025-0001",
      "case_title": "JKR Rasuah Tender",
      "status": "open",
      "priority": "high",
      "classification": "CRIS",
      "complaint_count": 3,
      "auto_grouped": true,
      "created_at": "2025-01-27T10:30:00",
      "updated_at": "2025-01-27T15:45:00"
    }
  ],
  "limit": 50,
  "offset": 0
}
```

**Examples:**
```bash
# Get all cases
curl "http://localhost:8000/cases"

# Get open cases only
curl "http://localhost:8000/cases?status=open"

# Pagination
curl "http://localhost:8000/cases?limit=10&offset=20"
```

---

### 7. Get Case Details

**Endpoint:** `GET /cases/{case_id}`

**Description:** Get detailed case information including all related complaints.

**Response:**
```json
{
  "id": 1,
  "case_number": "CASE-2025-0001",
  "case_title": "JKR Rasuah Tender",
  "case_description": null,
  "primary_complaint_id": 1,
  "common_keywords": ["rasuah", "tender", "jkr", "pegawai"],
  "status": "open",
  "priority": "high",
  "classification": "CRIS",
  "complaint_count": 3,
  "auto_grouped": true,
  "created_at": "2025-01-27T10:30:00",
  "updated_at": "2025-01-27T15:45:00",

  "complaints": [
    {
      "id": 1,
      "complaint_title": "Pegawai JKR terima rasuah",
      "complaint_description": "...",
      "classification": "CRIS",
      "submitted_at": "2025-01-27T10:30:00",
      "similarity_score": 1.0,
      "added_by": "system",
      "added_at": "2025-01-27T10:35:00"
    },
    {
      "id": 3,
      "complaint_title": "Saksi rasuah JKR",
      "similarity_score": 0.85,
      "added_by": "system"
    }
  ]
}
```

**Example:**
```bash
curl "http://localhost:8000/cases/1"
```

---

### 8. Create Case (Manual)

**Endpoint:** `POST /cases`

**Description:** Manually create a case with specified complaints.

**Request Body:**
```json
{
  "complaint_ids": [1, 3, 5],
  "case_title": "JKR Tender Scandal",
  "added_by": "officer_ahmad"
}
```

**Response:**
```json
{
  "message": "Case created successfully",
  "case_id": 1,
  "case_number": "CASE-2025-0001",
  "case": { /* full case details */ }
}
```

---

### 9. Update Case

**Endpoint:** `PUT /cases/{case_id}`

**Description:** Update case information.

**Request Body:**
```json
{
  "case_title": "Updated Title",
  "status": "investigating",
  "priority": "critical",
  "classification": "CRIS"
}
```

**Allowed fields:**
- `case_title` - Update case title
- `case_description` - Add/update description
- `status` - Change status (open, investigating, closed)
- `priority` - Change priority (low, medium, high, critical)
- `classification` - Change classification (CRIS, NFA)

---

### 10. Delete Case

**Endpoint:** `DELETE /cases/{case_id}`

**Description:** Delete a case. Complaints remain in the system.

**Response:**
```json
{
  "message": "Case 1 deleted successfully"
}
```

---

### 11. Add Complaint to Case

**Endpoint:** `POST /cases/{case_id}/complaints`

**Description:** Add a complaint to an existing case.

**Request Body:**
```json
{
  "complaint_id": 7,
  "added_by": "officer_fatimah"
}
```

**Response:**
```json
{
  "message": "Complaint 7 added to case 1",
  "case": { /* updated case details */ }
}
```

---

### 12. Remove Complaint from Case

**Endpoint:** `DELETE /cases/{case_id}/complaints/{complaint_id}`

**Description:** Remove complaint from case. If last complaint, case is deleted.

**Response:**
```json
{
  "message": "Complaint 7 removed from case 1"
}
```

---

### 13. Get Related Cases

**Endpoint:** `GET /cases/{case_id}/related`

**Description:** Get related closed cases that were similar when this case was created. This helps officers identify recurring issues or patterns.

**Response:**
```json
{
  "case_id": 42,
  "case_number": "CASE-2025-0042",
  "related_cases": [
    {
      "case_id": 15,
      "case_number": "CASE-2024-0015",
      "case_title": "Kes: Rasuah Tender",
      "similarity_score": 0.87,
      "status": "closed",
      "closed_at": "2024-12-15T10:30:00",
      "detected_at": "2025-10-30T16:45:00"
    },
    {
      "case_id": 23,
      "case_number": "CASE-2024-0023",
      "case_title": "Kes: Tender Projek JKR",
      "similarity_score": 0.79,
      "status": "closed",
      "closed_at": "2024-11-20T14:20:00",
      "detected_at": "2025-10-30T16:45:00"
    }
  ]
}
```

**Use Cases:**
- Display warning banner when viewing a case that has similar closed cases
- Allow officers to review previous investigations for context
- Identify repeat offenders or recurring patterns
- Help decide whether to reopen an old case vs. creating a new one

---

### 14. Get Complaint's Case

**Endpoint:** `GET /complaints/{complaint_id}/case`

**Description:** Get the case that a complaint belongs to.

**Response:**
```json
{
  "id": 1,
  "case_number": "CASE-2025-0001",
  "case_title": "JKR Rasuah Tender",
  /* ... full case details with all complaints ... */
}
```

---

### 15. Health Check

**Endpoint:** `GET /health`

**Description:** Check API health and service status.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "classifier_trained": false,
  "gpu_available": false
}
```

---

## 🗄️ Database Schema

### Complaints Table

```sql
CREATE TABLE complaints (
    id SERIAL PRIMARY KEY,

    -- Complainant Information
    full_name VARCHAR(255),
    ic_number VARCHAR(20),
    phone_number VARCHAR(20) NOT NULL,
    email VARCHAR(255),

    -- Complaint Details
    complaint_title VARCHAR(500) NOT NULL,
    category VARCHAR(100) NOT NULL,
    urgency_level VARCHAR(50) DEFAULT 'Sederhana',
    complaint_description TEXT NOT NULL,

    -- AI Processing Results
    extracted_data JSONB,              -- Structured entities extracted by AI
    w1h_summary TEXT,                  -- 5W1H summary in Bahasa Malaysia
    classification VARCHAR(50),        -- CRIS or NFA classification
    classification_confidence FLOAT,   -- Confidence score (0.0 - 1.0)

    -- Processing Status
    status VARCHAR(50) DEFAULT 'pending',  -- pending, submitted, processed

    -- Timestamps
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,

    -- Metadata
    has_documents BOOLEAN DEFAULT FALSE,
    document_count INTEGER DEFAULT 0
);
```

### Complaint Documents Table

```sql
CREATE TABLE complaint_documents (
    id SERIAL PRIMARY KEY,
    complaint_id INTEGER REFERENCES complaints(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,           -- Unique filename on disk
    original_filename VARCHAR(255) NOT NULL,  -- User's original filename
    file_path VARCHAR(500) NOT NULL,          -- Full path: uploads/complaint_1_20250127_file.pdf
    file_size INTEGER,                        -- File size in bytes
    file_type VARCHAR(50),                    -- MIME type: image/jpeg, application/pdf
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Important Notes:**
- **Files are stored on filesystem** in `uploads/` directory, NOT in database
- **Database stores metadata only** (filename, path, size, type)
- **Download endpoint**: `GET /documents/{id}/download` returns the actual file
- **Frontend usage**:
  - Image preview: `<img src="http://localhost:8000/documents/123/download" />`
  - Download link: `<a href="http://localhost:8000/documents/123/download" download>`

### Cases Table

```sql
CREATE TABLE cases (
    id SERIAL PRIMARY KEY,
    case_number VARCHAR(50) UNIQUE NOT NULL,       -- e.g., CASE-2025-0001
    case_title VARCHAR(500) NOT NULL,
    case_description TEXT,

    -- Auto-generated metadata
    primary_complaint_id INTEGER REFERENCES complaints(id),
    common_keywords TEXT[],                         -- Array of common keywords
    common_entities JSONB,                          -- Common names, orgs, locations

    -- Status and classification
    status VARCHAR(50) DEFAULT 'open',              -- open, investigating, closed
    priority VARCHAR(50) DEFAULT 'medium',          -- low, medium, high, critical
    classification VARCHAR(50),                     -- YES or NO (corruption indicator)

    -- Related cases tracking
    related_cases JSONB DEFAULT '[]'::jsonb,        -- Array of similar closed cases for reference

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,

    -- Metadata
    complaint_count INTEGER DEFAULT 0,
    auto_grouped BOOLEAN DEFAULT TRUE               -- TRUE if auto-grouped by system
);
```

**Related Cases Feature:**

When a new complaint is processed, the system:
1. Searches for similar complaints in **open cases** first
2. If found, adds to existing open case
3. If not found, searches for similar **closed cases** for reference
4. Creates new case with `related_cases` array containing:
   ```json
   [
     {
       "case_id": 15,
       "case_number": "CASE-2024-0015",
       "case_title": "Kes: Rasuah Tender",
       "similarity_score": 0.87,
       "status": "closed",
       "closed_at": "2024-12-15T10:30:00",
       "detected_at": "2025-10-30T16:45:00"
     }
   ]
   ```

This allows officers to:
- See if similar cases were previously investigated
- Review closed case details for context
- Identify recurring patterns or repeat offenders
- Make informed decisions about reopening old cases

### Case-Complaints Junction Table

```sql
CREATE TABLE case_complaints (
    id SERIAL PRIMARY KEY,
    case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,
    complaint_id INTEGER REFERENCES complaints(id) ON DELETE CASCADE,
    similarity_score FLOAT,                         -- Similarity to primary complaint
    added_by VARCHAR(50) DEFAULT 'system',          -- 'system' or username
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(case_id, complaint_id)                   -- Prevent duplicate entries
);
```

### Similar Cases Table

```sql
CREATE TABLE similar_cases (
    id SERIAL PRIMARY KEY,
    complaint_id INTEGER REFERENCES complaints(id) ON DELETE CASCADE,
    similar_complaint_id INTEGER,                   -- ID of similar complaint
    similarity_score FLOAT,
    rank INTEGER,
    found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## ⚙️ Configuration

### Environment Variables

Edit `.env` file:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sprm_db
DB_USER=postgres
DB_PASSWORD=your_password_here

# OpenRouter AI Configuration
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL=qwen/qwen-2.5-vl-72b-instruct
VLLM_TIMEOUT=120

# Classification Configuration
CLASSIFICATION_THRESHOLD=0.5    # Confidence threshold for CRIS/NFA (0.0 - 1.0)

# Case Grouping Configuration
CASE_GROUPING_THRESHOLD=0.70    # Similarity threshold for auto-grouping (0.0 - 1.0)

# Application Configuration
APP_HOST=0.0.0.0
APP_PORT=8000
```

### Supported AI Models

Current: **Qwen 2.5 VL 72B Instruct** (vision model)

Alternative models (via OpenRouter):
```bash
# Claude with vision
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Gemini with vision
OPENROUTER_MODEL=google/gemini-pro-vision

# GPT-4 with vision
OPENROUTER_MODEL=openai/gpt-4-vision-preview
```

### File Upload Settings

Default settings in code:
- **Accepted formats:** PDF, PNG, JPG, JPEG
- **Max file size:** 10MB per file
- **Storage location:** `uploads/` directory

To change limits, edit `src/main.py`:
```python
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg'}
```

---

## 🚀 Deployment

### Development Server

```bash
python src/main.py
# Runs on http://localhost:8000 with hot-reload
```

### Production Server

#### Option 1: Uvicorn (Recommended)

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Option 2: Gunicorn

```bash
gunicorn src.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

#### Option 3: Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Build and run:**
```bash
docker build -t sprm-backend .
docker run -p 8000:8000 --env-file .env sprm-backend
```

---

## 🔧 Troubleshooting

### Issue: Database connection failed

**Error:**
```
⚠️  Database initialization failed: connection to server at "localhost" (127.0.0.1), port 5432 failed
```

**Solution:**
1. Check if PostgreSQL is running:
   ```bash
   # Windows
   services.msc → Check PostgreSQL service

   # Linux/Mac
   sudo systemctl status postgresql
   ```

2. Verify database exists:
   ```bash
   psql -U postgres -l
   ```

3. Check credentials in `.env` file

4. Update `DB_HOST` to `127.0.0.1` if `localhost` doesn't work

---

### Issue: OpenRouter API errors

**Error:**
```
❌ OpenRouter API error: 401 Unauthorized
```

**Solution:**
1. Verify API key in `.env`:
   ```bash
   echo $OPENROUTER_API_KEY
   ```

2. Check API key is valid at https://openrouter.ai/

3. Test API key:
   ```bash
   curl https://openrouter.ai/api/v1/models \
     -H "Authorization: Bearer YOUR_API_KEY"
   ```

---

### Issue: File upload fails

**Error:**
```
❌ Error submitting complaint: Maximum upload size exceeded
```

**Solution:**
1. Check file size (max 10MB per file)
2. Verify file format (PDF, PNG, JPG, JPEG only)
3. Increase limit in `src/main.py` if needed

---

### Issue: Port 8000 already in use

**Error:**
```
ERROR: [Errno 48] Address already in use
```

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process or use different port
python src/main.py --port 8001
```

---

## 📊 Processing Flow

```
┌─────────────────────────────────────────────┐
│  Frontend: User submits complaint + files   │
└───────────────┬─────────────────────────────┘
                ↓
┌─────────────────────────────────────────────┐
│  Backend: Save to PostgreSQL (immediate)    │
│  - Store form data                          │
│  - Save files to uploads/                   │
│  - Return complaint_id                      │
└───────────────┬─────────────────────────────┘
                ↓
┌─────────────────────────────────────────────┐
│  Background Processing (async)              │
└───────────────┬─────────────────────────────┘
                ↓
        ┌───────┴────────┐
        ↓                ↓
┌──────────────┐  ┌──────────────────┐
│  Form Text   │  │  Process Images  │
│              │  │  via OpenRouter  │
│  - Title     │  │  Vision Model    │
│  - Desc      │  │                  │
└──────┬───────┘  └────────┬─────────┘
       │                   │
       │          ┌────────┴────────┐
       │          │  Extract from   │
       │          │  each image:    │
       │          │  - Text (OCR)   │
       │          │  - Entities     │
       │          └────────┬────────┘
       │                   │
       └──────────┬────────┘
                  ↓
       ┌──────────────────────┐
       │  Combine all data    │
       │  Form + All images   │
       └──────────┬───────────┘
                  ↓
       ┌──────────────────────┐
       │  OpenRouter:         │
       │  Extract entities    │
       │  - Names             │
       │  - Dates             │
       │  - Locations         │
       │  - Amounts           │
       └──────────┬───────────┘
                  ↓
       ┌──────────────────────┐
       │  OpenRouter:         │
       │  Generate 5W1H       │
       │  (Bahasa Malaysia)   │
       └──────────┬───────────┘
                  ↓
       ┌──────────────────────┐
       │  Classification:     │
       │  Analyze 5W1H for    │
       │  corruption          │
       │  indicators          │
       │  → CRIS or NFA       │
       └──────────┬───────────┘
                  ↓
       ┌──────────────────────┐
       │  Save results to DB  │
       │  - extracted_data    │
       │  - w1h_summary       │
       │  - classification    │
       │  - confidence        │
       │  - status=processed  │
       └──────────┬───────────┘
                  ↓
       ┌──────────────────────┐
       │  Auto-Group into     │
       │  Case:               │
       │  - Search similar    │
       │    complaints        │
       │  - Group if          │
       │    similarity ≥ 0.70 │
       │  - Create new case   │
       │    or add to         │
       │    existing case     │
       └──────────────────────┘
```

---

## 📈 Performance & Cost

### Response Times
- **Complaint submission:** < 500ms (immediate)
- **Image processing:** 2-5 seconds per image
- **5W1H generation:** 3-8 seconds
- **Classification:** 2-4 seconds
- **Case grouping:** 0.5-2 seconds (similarity search)
- **Total background processing:** 8-25 seconds

### OpenRouter Costs
- **Model:** Qwen 2.5 VL 72B Instruct
- **Input:** ~$0.80 per million tokens
- **Output:** ~$0.80 per million tokens
- **Average cost per complaint:** $0.002 - $0.005 (very cheap!)

### Optimization Tips
1. Images are processed in background (non-blocking)
2. Database uses JSONB for efficient JSON storage
3. Connection pooling for database
4. CORS configured for multiple origins

---

## 🔐 Security Considerations

### Production Checklist

- [ ] **Change default PostgreSQL password**
- [ ] **Restrict CORS origins** (edit `src/main.py`)
- [ ] **Add rate limiting** for API endpoints
- [ ] **Enable HTTPS** (use nginx/apache reverse proxy)
- [ ] **Protect API key** (use environment variables, never commit)
- [ ] **Set file upload limits**
- [ ] **Sanitize user inputs**
- [ ] **Regular database backups**

### CORS Configuration

Update in `src/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],  # Change from ["*"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📚 Additional Resources

### API Documentation
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Complaint API Guide:** [docs/COMPLAINT_API.md](COMPLAINT_API.md)

### Project Structure
```
SPRM_Backend/
├── src/                          # Source code
│   ├── main.py                   # FastAPI application
│   ├── database.py               # PostgreSQL connection
│   ├── complaint_service.py      # Complaint processing logic
│   ├── case_service.py           # Case grouping & management
│   ├── openrouter_service.py     # AI integration (vision model)
│   ├── classification_service.py # CRIS/NFA classification
│   ├── search_relevant_case.py   # Similarity search engine
│   ├── models.py                 # Pydantic models
│   └── sprm_classification.py    # Legacy classifier
├── examples/                     # Example scripts
│   └── example_usage.py
├── docs/                         # Documentation
│   ├── Backend_README.md         # This file
│   ├── COMPLAINT_API.md
│   ├── API_SPECIFICATION.md
│   └── ...
├── uploads/                      # File uploads (gitignored)
├── requirements.txt              # Python dependencies
├── .env                          # Environment config
├── .env.example                  # Template
└── .gitignore
```

---

## 🤝 Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review API docs at http://localhost:8000/docs
3. Check server logs for detailed error messages

---

## 📝 Changelog

### Version 2.2.0 (Current)
- ✨ Added case management system with auto-grouping
- ✨ Automatic complaint grouping based on similarity (threshold: 0.70)
- ✨ Manual case management API (create, update, delete, move complaints)
- ✨ Case numbering system (CASE-2025-XXXX)
- ✨ Common keyword and entity extraction for cases
- 📊 New database tables: cases, case_complaints
- 🔧 Integrated case grouping into complaint processing pipeline

### Version 2.1.0
- ✨ Added CRIS/NFA classification based on 5W1H summaries
- ✨ Added classification confidence scoring
- ✨ Added configurable classification thresholds
- 🔧 Improved background processing pipeline

### Version 2.0.0
- ✨ Added complaint submission API with file uploads
- ✨ Integrated OpenRouter AI for document processing
- ✨ Added image text extraction (OCR)
- ✨ Added structured data extraction
- ✨ Added 5W1H summary generation
- ✨ PostgreSQL database with JSONB support
- ✨ Background async processing
- 🔧 Improved error handling and logging

### Version 1.0.0
- Initial release
- Classification API
- Search API
- Health check endpoints

---

## 📄 License

MIT License

---

**Happy coding! 🚀**

For frontend integration examples, see [COMPLAINT_API.md](COMPLAINT_API.md)
