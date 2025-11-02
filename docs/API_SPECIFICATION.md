# SPRM Backend - API Specification

## Base Information

- **Base URL**: `http://localhost:8000`
- **Protocol**: HTTP/HTTPS
- **Content-Type**: `application/json` (except file uploads use `multipart/form-data`)
- **Character Encoding**: UTF-8

---

## 📡 Endpoints Summary

### Core System Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Get API information |
| GET | `/health` | Health check |
| GET | `/model-info` | Get model information |

### Legacy Classification Endpoints (Optional)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/classify` | Classify a case (legacy) |
| POST | `/train` | Train classification model |
| POST | `/load-model` | Load pre-trained model |
| POST | `/search/similar` | Search similar cases (legacy) |
| POST | `/search/load-cases` | Load cases from CSV |
| POST | `/search/add-case` | Add single case |
| GET | `/search/stats` | Get search statistics |

### Complaint Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/complaints/submit` | Submit new complaint with files |
| GET | `/complaints/{id}` | Get complaint details |
| GET | `/complaints` | List all complaints |
| GET | `/complaints/unassigned` | List unassigned complaints |
| PUT | `/complaints/{id}` | Update complaint fields |
| PUT | `/complaints/{id}/evaluation` | Save officer evaluation |
| PUT | `/complaints/{id}/officer-review` | Update officer review status |
| POST | `/complaints/{id}/move-to-case/{case_id}` | Move complaint to existing case |
| POST | `/complaints/{id}/move-to-new-case` | Move complaint to new standalone case |
| GET | `/complaints/{id}/case` | Get case containing complaint |

### Case Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cases` | List all cases |
| GET | `/cases/{id}` | Get case details |
| POST | `/cases` | Create new case |
| PUT | `/cases/{id}` | Update case information |
| DELETE | `/cases/{id}` | Delete case |
| GET | `/cases/{id}/related` | Get related closed cases |
| POST | `/cases/{id}/complaints` | Add complaint to case |
| DELETE | `/cases/{id}/complaints/{complaint_id}` | Remove complaint from case |

### Document Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/documents/{id}/download` | Download/preview document |

### Configuration
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/config/evaluation-options` | Get evaluation form dropdown options |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics/dashboard` | Get pre-computed dashboard analytics |
| GET | `/analytics/entities` | Get entity-based analytics |
| GET | `/analytics/patterns` | Detect common patterns |
| GET | `/analytics/trending` | Get trending keywords |
| GET | `/analytics/cases` | Get case-level analytics |
| POST | `/analytics/precompute` | Pre-compute analytics (background) |
| POST | `/analytics/cache/invalidate` | Invalidate analytics cache |
| GET | `/analytics/cache/status` | Get cache status |

### Letter Generation
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/letters/types` | Get available letter types |
| GET | `/letters/template/{type}` | Get letter template fields |
| POST | `/complaints/{id}/letters/generate` | Generate letter for complaint |
| GET | `/complaints/{id}/letters` | Get letter history for complaint |
| GET | `/letters/{id}` | Get specific letter by ID |

---

## 1. Classification Endpoints

### POST `/classify`

Classify a case description as CORRUPTION or NO CORRUPTION.

**Request Body:**
```json
{
  "text": "string (required)",
  "description_5": "string (optional)"
}
```

**Response 200:**
```json
{
  "classification": "CORRUPTION" | "NO CORRUPTION",
  "confidence": 87.43,
  "corruption_probability": 87.43,
  "no_corruption_probability": 12.57
}
```

**Response 503:**
```json
{
  "detail": "Classifier not ready. Please train the model first using POST /train"
}
```

**Response 500:**
```json
{
  "detail": "Classification error: {error_message}"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "pegawai kerajaan menerima rasuah daripada syarikat swasta",
    "description_5": "projek pembinaan bernilai RM 5 juta"
  }'
```

---

### POST `/train`

Train the corruption classification model.

**Request Body:**
```json
{
  "cris_path": "string (default: 'Data CMS/complaint_cris.csv')",
  "nfa_path": "string (default: 'Data CMS/complaint_nfa.csv')",
  "description_columns": ["description", "description_5"],
  "test_size": 0.2
}
```

**Response 200:**
```json
{
  "accuracy": 51.7,
  "auc_score": 0.51,
  "total_cases": 262249,
  "cris_cases": 63612,
  "nfa_cases": 198637,
  "confusion_matrix": [[matrix_data]]
}
```

**Response 404:**
```json
{
  "detail": "Data files not found: {error}. Please ensure CSV files are in the correct location."
}
```

**Response 500:**
```json
{
  "detail": "Training error: {error_message}"
}
```

---

### POST `/load-model`

Load a pre-trained classification model.

**Query Parameters:**
- `model_path` (string, default: "sprm_model.pkl"): Path to model file

**Response 200:**
```json
{
  "message": "Model loaded successfully",
  "model_path": "sprm_model.pkl"
}
```

**Response 404:**
```json
{
  "detail": "Model file not found: {model_path}"
}
```

---

## 2. Search Endpoints

### POST `/search/similar`

Search for cases similar to the provided description.

**Request Body:**
```json
{
  "description": "string (required)",
  "description_1": "string (optional)",
  "description_2": "string (optional)",
  "description_3": "string (optional)",
  "description_4": "string (optional)",
  "description_5": "string (optional)",
  "top_k": 5
}
```

**Response 200:**
```json
{
  "query_text": "combined query text",
  "total_matches": 5,
  "top_matches": [
    {
      "id": 12345,
      "description": "case description text",
      "similarity_score": 0.9234,
      "rank": 1
    }
  ]
}
```

**Response 503:**
```json
{
  "detail": "No cases loaded. Please load cases using POST /search/load-cases"
}
```

**Response 500:**
```json
{
  "detail": "Search error: {error_message}"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/search/similar" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "pegawai kerajaan menerima wang rasuah",
    "description_5": "projek pembinaan",
    "top_k": 5
  }'
```

---

### POST `/search/load-cases`

Load cases from CSV file into the search engine.

**Request Body:**
```json
{
  "csv_path": "string (required)",
  "max_cases": 5000 (optional)
}
```

**Response 200:**
```json
{
  "message": "Cases loaded successfully",
  "total_cases": 5000,
  "csv_path": "Data CMS/complaint_cris.csv"
}
```

**Response 404:**
```json
{
  "detail": "CSV file not found: {csv_path}"
}
```

**Response 500:**
```json
{
  "detail": "Error loading cases: {error_message}"
}
```

---

### POST `/search/add-case`

Add a single case to the search engine.

**Query Parameters:**
- `case_id` (integer, required): Unique case ID
- `description` (string, required): Main case description
- `description_1` (string, optional): Additional description 1
- `description_2` (string, optional): Additional description 2
- `description_3` (string, optional): Additional description 3
- `description_4` (string, optional): Additional description 4
- `description_5` (string, optional): Additional description 5

**Response 200:**
```json
{
  "message": "Case added successfully",
  "case_id": 999,
  "total_cases": 5001
}
```

**Response 500:**
```json
{
  "detail": "Error adding case: {error_message}"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/search/add-case?case_id=999&description=Test+case+description"
```

---

### GET `/search/stats`

Get search engine statistics.

**Response 200:**
```json
{
  "total_cases": 5000,
  "model_name": "all-MiniLM-L6-v2",
  "use_database": false,
  "embeddings_loaded": true
}
```

---

## 3. Utility Endpoints

### GET `/`

Get API information and available endpoints.

**Response 200:**
```json
{
  "message": "SPRM Corruption Classification & Case Search API",
  "status": "active",
  "endpoints": {
    "classify": "POST /classify - Classify a corruption case",
    "train": "POST /train - Train the classifier",
    "search": "POST /search/similar - Search for similar cases",
    "load_cases": "POST /search/load-cases - Load cases from CSV",
    "add_case": "POST /search/add-case - Add a single case",
    "search_stats": "GET /search/stats - Get search engine statistics",
    "health": "GET /health - Check API health",
    "model_info": "GET /model-info - Get model information"
  }
}
```

---

### GET `/health`

Health check endpoint to verify API status and model readiness.

**Response 200:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "classifier_trained": true,
  "gpu_available": false
}
```

---

### GET `/model-info`

Get information about the loaded models.

**Response 200:**
```json
{
  "model_name": "all-MiniLM-L6-v2",
  "batch_size": 512,
  "device": "cpu",
  "embedding_model_loaded": true,
  "classifier_trained": true
}
```

**Response 500:**
```json
{
  "detail": "Classifier not initialized"
}
```

---

## 📊 Data Models

### Complaint
```typescript
interface Complaint {
  id: number;
  full_name?: string;
  ic_number?: string;
  phone_number?: string;
  email?: string;
  complaint_title: string;
  complaint_description: string;
  category?: string;
  urgency_level?: string;

  // AI-Generated Fields
  status: 'pending' | 'submitted' | 'processed';
  classification?: 'CRIS' | 'NFA';
  classification_confidence?: number;
  sector?: string;
  akta?: string;

  // 5W1H Structured Data
  w1h_summary?: string;      // Full text format
  w1h_what?: string;         // What happened
  w1h_who?: string;          // Who involved
  w1h_when?: string;         // When
  w1h_where?: string;        // Where
  w1h_why?: string;          // Why
  w1h_how?: string;          // How

  // Extracted Data
  extracted_data?: {
    entities: {
      names: string[];
      organizations: string[];
      locations: string[];
      dates: string[];
      amounts: string[];
    };
  };

  // Timestamps
  submitted_at: string;
  processed_at?: string;

  // Documents
  has_documents: boolean;
  document_count: number;
  documents?: ComplaintDocument[];

  // Similar Cases
  similar_cases?: SimilarCase[];

  // Case Assignment
  case_id?: number;
  case_number?: string;

  // Officer Review
  officer_status?: 'pending_review' | 'nfa' | 'escalated' | 'investigating' | 'closed';
  officer_remarks?: string;
  reviewed_by?: string;
  reviewed_at?: string;

  // Evaluation
  type_of_information?: string;
  source_type?: string;
  sub_sector?: string;
  currency_type?: string;
  property_value?: number;
  akta_sections?: string[];
  evaluated_at?: string;
  evaluated_by?: string;
}
```

### ComplaintDocument
```typescript
interface ComplaintDocument {
  id: number;
  complaint_id: number;
  filename: string;
  original_filename: string;
  file_path: string;
  file_size: number;
  file_type: string;
  uploaded_at: string;
  download_url: string;  // Use this for frontend!
}
```

### Case
```typescript
interface Case {
  id: number;
  case_number: string;           // e.g. "CASE-2025-0001"
  case_title: string;
  case_description?: string;
  primary_complaint_id: number;
  common_keywords: string[];

  // Status & Priority
  status: 'open' | 'investigating' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'critical';
  classification?: 'CRIS' | 'NFA';

  // Metadata
  complaint_count: number;
  auto_grouped: boolean;
  created_at: string;
  updated_at: string;
  closed_at?: string;

  // Complaints in Case
  complaints?: CaseComplaint[];

  // Related Closed Cases
  related_cases?: RelatedCase[];
}
```

### CaseComplaint
```typescript
interface CaseComplaint extends Complaint {
  similarity_score: number;  // 0-1
  added_by: string;         // 'system' or 'officer_name'
  added_at: string;
}
```

### RelatedCase
```typescript
interface RelatedCase {
  case_id: number;
  case_number: string;
  case_title: string;
  similarity_score: number;
  status: string;
  closed_at?: string;
  detected_at: string;
}
```

### SimilarCase
```typescript
interface SimilarCase {
  id: number;
  similar_case_id: number;
  similarity_score: number;  // 0-1
  rank: number;             // 1-based
  description?: string;
}
```

### EvaluationOptions
```typescript
interface EvaluationOptions {
  main_sectors: string[];
  sub_sectors: { [sector: string]: string[] };
  type_of_information_options: string[];
  source_type_options: string[];
  currency_types: string[];
  officer_status_options: string[];
}
```

### Letter
```typescript
interface Letter {
  id: number;
  complaint_id: number;
  letter_type: string;
  letter_content: string;
  generated_by: string;
  generated_at: string;
}
```

### AnalyticsDashboard
```typescript
interface AnalyticsDashboard {
  summary: {
    total_complaints: number;
    yes_classification_count: number;
    no_classification_count: number;
    pending_review_count: number;
    nfa_count: number;
    escalated_count: number;
    total_cases: number;
  };
  top_names: { name: string; count: number }[];
  top_organizations: { organization: string; count: number }[];
  top_locations: { location: string; count: number }[];
  top_amounts: { amount: string; count: number }[];
  sectors: {
    sector: string;
    complaint_count: number;
    yes_count: number;
    no_count: number;
  }[];
  patterns: {
    pattern: string;
    count: number;
  }[];
}
```

---

## Legacy Data Models (for old endpoints)

### ClassificationResponse
```typescript
interface ClassificationResponse {
  classification: "CORRUPTION" | "NO CORRUPTION";
  confidence: number;
  corruption_probability: number;
  no_corruption_probability: number;
}
```

### SearchRequest
```typescript
interface SearchRequest {
  description: string;
  description_1?: string;
  description_2?: string;
  description_3?: string;
  description_4?: string;
  description_5?: string;
  top_k?: number;
}
```

---

## 🔐 Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input parameters |
| 404 | Not Found - Resource doesn't exist (file, model, etc.) |
| 500 | Internal Server Error - Server-side error |
| 503 | Service Unavailable - Model not loaded/trained |

---

## 4. Complaint Management Endpoints

### POST `/complaints/submit`

Submit a new complaint with optional file attachments. All complainant information is optional for anonymous complaints.

**Content-Type:** `multipart/form-data`

**Form Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `full_name` | string | No | Full name (optional for anonymous) |
| `ic_number` | string | No | IC/Passport number |
| `phone_number` | string | No | Contact phone |
| `email` | string | No | Email address |
| `complaint_title` | string | **Yes** | Complaint title |
| `complaint_description` | string | **Yes** | Detailed description |
| `category` | string | No | Complaint category |
| `urgency_level` | string | No | Urgency level |
| `files` | file[] | No | Supporting documents |

**Response 200:**
```json
{
  "complaint_id": 123,
  "status": "submitted",
  "message": "Aduan berjaya diterima...",
  "submitted_at": "2025-01-15T10:30:00",
  "document_count": 2
}
```

**Example - JavaScript:**
```javascript
const formData = new FormData();
formData.append('complaint_title', 'Rasuah Tender JKR');
formData.append('complaint_description', 'Pegawai menerima rasuah...');
formData.append('category', 'Rasuah');
formData.append('files', fileInput.files[0]);

const response = await fetch('http://localhost:8000/complaints/submit', {
  method: 'POST',
  body: formData
});
const result = await response.json();
```

---

### GET `/complaints/{complaint_id}`

Get detailed information about a complaint including documents, classification, similar cases, and case assignment.

**Response 200:**
```json
{
  "id": 123,
  "complaint_title": "Rasuah Tender JKR",
  "complaint_description": "...",
  "classification": "CRIS",
  "classification_confidence": 0.92,
  "sector": "Pembinaan & Infrastruktur",
  "akta": "Akta SPRM 2009",
  "status": "processed",
  "w1h_summary": "**WHAT:** ...",
  "w1h_what": "Pegawai menerima rasuah",
  "w1h_who": "En. Ahmad, Dato' Rashid",
  "w1h_when": "15 Januari 2024",
  "w1h_where": "Kuala Lumpur",
  "w1h_why": "Untuk meluluskan tender",
  "w1h_how": "Melalui suapan tunai",
  "documents": [
    {
      "id": 1,
      "original_filename": "evidence.pdf",
      "file_size": 524288,
      "file_type": "application/pdf",
      "download_url": "/documents/1/download"
    }
  ],
  "similar_cases": [
    {
      "id": 45678,
      "similarity_score": 0.92,
      "rank": 1
    }
  ],
  "case_id": 5,
  "case_number": "CASE-2025-0005",
  "submitted_at": "2025-01-15T10:30:00",
  "processed_at": "2025-01-15T10:30:15"
}
```

---

### GET `/complaints`

List complaints with optional filtering.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status (pending, processed) |
| `category` | string | Filter by category |
| `assigned` | boolean | Filter by case assignment |
| `officer_status` | string | Filter by officer status |
| `limit` | integer | Results per page (default: 50) |
| `offset` | integer | Pagination offset (default: 0) |

**Response 200:**
```json
{
  "total": 150,
  "complaints": [...],
  "limit": 50,
  "offset": 0
}
```

**Example:**
```javascript
const response = await fetch(
  'http://localhost:8000/complaints?status=processed&limit=20'
);
const data = await response.json();
```

---

### PUT `/complaints/{complaint_id}`

Update complaint fields (for officer editing).

**Request Body:**
```json
{
  "w1h_what": "Updated description",
  "w1h_who": "Updated persons involved",
  "classification": "CRIS",
  "sector": "Pembinaan & Infrastruktur"
}
```

**Editable Fields:**
- Basic: `complaint_title`, `complaint_description`, `category`, `urgency_level`
- 5W1H: `w1h_what`, `w1h_who`, `w1h_when`, `w1h_where`, `w1h_why`, `w1h_how`, `w1h_summary`
- Classification: `sector`, `akta`, `classification`, `classification_confidence`, `status`

**Note:** Editing 5W1H fields triggers automatic re-processing (re-classification, re-embedding).

---

### PUT `/complaints/{complaint_id}/officer-review`

Officer review and status update.

**Request Body:**
```json
{
  "officer_status": "nfa",
  "officer_remarks": "Not a corruption case after review",
  "reviewed_by": "officer_ahmad"
}
```

**Valid Statuses:**
- `pending_review` - Waiting for review
- `nfa` - No Further Action
- `escalated` - Escalate for investigation
- `investigating` - Under investigation
- `closed` - Case closed

**Response 200:**
```json
{
  "message": "Officer review updated successfully",
  "complaint_id": 123,
  "officer_status": "nfa",
  "reviewed_by": "officer_ahmad",
  "reviewed_at": "2025-01-15T14:30:00"
}
```

---

## 5. Case Management Endpoints

### GET `/cases`

List all cases with optional filtering.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status (open, investigating, closed) |
| `limit` | integer | Results per page (default: 50) |
| `offset` | integer | Pagination offset |

**Response 200:**
```json
{
  "total": 25,
  "cases": [
    {
      "id": 1,
      "case_number": "CASE-2025-0001",
      "case_title": "JKR Tender Scandal",
      "status": "open",
      "priority": "high",
      "classification": "CRIS",
      "complaint_count": 3,
      "auto_grouped": true,
      "created_at": "2025-01-15T10:30:00"
    }
  ]
}
```

---

### GET `/cases/{case_id}`

Get detailed case information including all complaints.

**Response 200:**
```json
{
  "id": 1,
  "case_number": "CASE-2025-0001",
  "case_title": "JKR Tender Scandal",
  "status": "open",
  "priority": "high",
  "classification": "CRIS",
  "complaint_count": 3,
  "complaints": [
    {
      "id": 1,
      "complaint_title": "Pegawai JKR terima rasuah",
      "similarity_score": 1.0,
      "added_by": "system",
      "submitted_at": "2025-01-15T10:30:00"
    }
  ],
  "related_cases": [
    {
      "case_id": 15,
      "case_number": "CASE-2024-0015",
      "similarity_score": 0.87,
      "status": "closed"
    }
  ]
}
```

---

### POST `/cases`

Create a new case manually with selected complaints.

**Request Body:**
```json
{
  "complaint_ids": [1, 3, 5],
  "case_title": "JKR Tender Scandal",
  "added_by": "officer_ahmad"
}
```

**Response 200:**
```json
{
  "message": "Case created successfully",
  "case_id": 1,
  "case_number": "CASE-2025-0001",
  "case": { /* full case details */ }
}
```

---

### PUT `/cases/{case_id}`

Update case information.

**Request Body:**
```json
{
  "case_title": "Updated Title",
  "status": "investigating",
  "priority": "critical"
}
```

**Allowed Fields:**
- `case_title`, `case_description`
- `status` (open, investigating, closed)
- `priority` (low, medium, high, critical)
- `classification` (CRIS, NFA)

---

## 6. Document Management Endpoints

### GET `/documents/{document_id}/download`

Download or preview a complaint document.

**Response:** File stream with appropriate `Content-Type` header

**Usage in Frontend:**
```javascript
// Image preview
<img src={`http://localhost:8000/documents/${doc.id}/download`} />

// Download link
<a href={`http://localhost:8000/documents/${doc.id}/download`} download>
  Download
</a>

// PDF viewer
<iframe src={`http://localhost:8000/documents/${doc.id}/download`} />
```

**Note:** Always use the `download_url` field from complaint details response.

---

## 7. Analytics Endpoints

### GET `/analytics/dashboard`

Get pre-computed dashboard analytics (FAST - no computation needed).

**Response 200:**
```json
{
  "summary": {
    "total_complaints": 150,
    "yes_classification_count": 90,
    "no_classification_count": 60,
    "pending_review_count": 45,
    "total_cases": 85
  },
  "top_names": [
    {"name": "Ahmad", "count": 12}
  ],
  "top_organizations": [
    {"organization": "JKR", "count": 8}
  ],
  "sectors": [
    {
      "sector": "Pembinaan",
      "complaint_count": 25,
      "yes_count": 15
    }
  ],
  "patterns": [
    {"pattern": "tender + gold", "count": 8}
  ]
}
```

---

### GET `/analytics/entities`

Get entity-based analytics (names, organizations, locations, amounts).

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `days` | integer | Limit to last N days (optional) |

**Example:**
```
GET /analytics/entities?days=30
```

---

### GET `/analytics/patterns`

Detect common patterns and combinations in complaints.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `min_occurrences` | integer | Minimum pattern occurrences (default: 2) |

**Response:**
```json
{
  "two_keyword_patterns": [
    {
      "pattern": "tender + gold",
      "count": 3
    }
  ]
}
```

---

## 8. Letter Generation Endpoints

### GET `/letters/types`

Get available letter types for generation.

**Response 200:**
```json
{
  "letter_types": [
    {
      "type": "rujuk_jabatan",
      "name": "Surat Rujuk Jabatan",
      "description": "Refer complaint to relevant department"
    }
  ]
}
```

---

### GET `/letters/template/{letter_type}`

Get letter template fields with pre-filled values from complaint.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `complaint_id` | integer | Complaint ID to pre-fill values |

**Example:**
```
GET /letters/template/rujuk_jabatan?complaint_id=123
```

**Response:**
```json
{
  "letter_type": "rujuk_jabatan",
  "fields": {
    "auto_filled": {...},
    "editable": {...}
  },
  "template_preview": "..."
}
```

---

### POST `/complaints/{complaint_id}/letters/generate`

Generate a letter for a complaint with officer-filled data.

**Request Body:**
```json
{
  "letter_type": "rujuk_jabatan",
  "fields": {
    "recipient_title": "YBhg. Dato',",
    "recipient_name": "Datuk Bandar",
    "recipient_organization": "Majlis Bandaraya",
    "subject_line": "ADUAN BERHUBUNG..."
  },
  "generated_by": "officer_ahmad"
}
```

**Response 200:**
```json
{
  "letter_id": 1,
  "letter_content": "...",
  "letter_type": "rujuk_jabatan",
  "generated_at": "2025-01-15T10:30:00"
}
```

---

### GET `/complaints/{complaint_id}/letters`

Get all letters generated for a complaint.

**Response 200:**
```json
{
  "complaint_id": 123,
  "total_letters": 2,
  "letters": [
    {
      "id": 1,
      "letter_type": "rujuk_jabatan",
      "generated_by": "officer_ahmad",
      "generated_at": "2025-01-15T10:30:00"
    }
  ]
}
```

---

## 9. Configuration Endpoints

### GET `/config/evaluation-options`

Get all dropdown options for complaint evaluation form.

**Response 200:**
```json
{
  "main_sectors": ["Pembinaan & Infrastruktur", ...],
  "sub_sectors": {"Pembinaan & Infrastruktur": [...]},
  "type_of_information_options": [...],
  "source_type_options": [...],
  "currency_types": [...],
  "officer_status_options": [
    "pending_review",
    "nfa",
    "escalated",
    "investigating",
    "closed"
  ]
}
```

---

## 📝 Notes for Frontend Developers

### 1. **CORS**
The API accepts requests from all origins by default. In production, configure allowed origins.

### 2. **Request Timeout**
- Complaint submission: Returns immediately (1-2s), processes in background
- Analytics requests: Instant (<100ms) - pre-computed
- Classification/Search: 1-3 seconds
- Training requests: Several minutes

### 3. **Background Processing**
When submitting complaints:
1. API returns immediately with `status: "submitted"`
2. Processing happens in background (5W1H, sector, classification)
3. Poll `GET /complaints/{id}` to check when `status` becomes `"processed"`

### 4. **File Downloads**
Always use the `download_url` field from API responses:
```javascript
const fileUrl = `${backendUrl}${document.download_url}`;
```

### 5. **Error Handling**
Always implement proper error handling:
```javascript
try {
  const response = await fetch('/complaints/submit', {...});
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }
  const data = await response.json();
  // Handle success
} catch (error) {
  // Handle error
  console.error('API Error:', error.message);
}
```

---

## 🧪 Testing

### Postman Collection
Import the OpenAPI schema from: `http://localhost:8000/openapi.json`

### Sample Test Cases

**Classification Test:**
```json
{
  "text": "Pegawai kerajaan menerima rasuah sebanyak RM 50,000 daripada kontraktor untuk meluluskan projek pembinaan jambatan baharu. Kes ini melibatkan salah guna kuasa dan penyelewengan tender kerajaan."
}
```

Expected: `classification: "CORRUPTION"`, `confidence: >70%`

**Search Test:**
```json
{
  "description": "Penyelewengan dalam proses tender kerajaan melibatkan pegawai tinggi",
  "top_k": 3
}
```

Expected: 3 similar cases with `similarity_score > 0.5`

---

## 📞 Support

For API issues or questions:
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Check Logs**: View server console output

---

## 📝 Important Notes

### Modern vs Legacy Endpoints

This API has evolved from a simple classification system to a full complaint management system:

**Modern System (Recommended):**
- Use `/complaints/*` endpoints for complaint submission and management
- Use `/cases/*` endpoints for case management
- Use `/analytics/*` endpoints for dashboard analytics
- Use `/letters/*` endpoints for letter generation
- Background processing with status polling

**Legacy System (Optional):**
- `/classify`, `/train`, `/search/similar` - Original ML classification endpoints
- Still functional but not required for main workflow
- Kept for backward compatibility and manual testing

### Getting Started

1. **For Public Complaint Submission:** Use `POST /complaints/submit`
2. **For Officer Dashboard:** Use `GET /complaints`, `GET /cases`, `GET /analytics/dashboard`
3. **For Case Management:** Use `/cases/*` endpoints
4. **For Letter Generation:** Use `/letters/*` endpoints

---

**Last Updated**: 2025-11-02
**API Version**: 2.3.0
**Backend Version**: 2.3.0
