# Complaint Submission API Documentation

## Overview

The Complaint Submission API allows frontend applications to submit complaints with optional file attachments. The system automatically:
1. Stores complaint data in PostgreSQL
2. Saves uploaded documents
3. Classifies the complaint as CORRUPTION or NO CORRUPTION
4. Finds similar historical cases

## Database Setup

### 1. Install PostgreSQL

Make sure PostgreSQL is installed and running on your system.

### 2. Create Database

```sql
CREATE DATABASE sprm_db;
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sprm_db
DB_USER=postgres
DB_PASSWORD=your_password
```

### 4. Initialize Tables

Tables are automatically created on first startup. You can also manually run:

```python
from src.database import db
db.create_tables()
```

## API Endpoints

### 1. Submit Complaint

**Endpoint:** `POST /complaints/submit`

**Content-Type:** `multipart/form-data` (for file uploads)

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `full_name` | string | No | Full name of complainant |
| `ic_number` | string | No | IC/Passport number |
| `phone_number` | string | **Yes** | Contact phone number |
| `email` | string | No | Email address |
| `complaint_title` | string | **Yes** | Title/subject of complaint |
| `category` | string | **Yes** | Complaint category |
| `urgency_level` | string | No | Urgency: Rendah/Sederhana/Tinggi/Kritikal (default: Sederhana) |
| `complaint_description` | string | **Yes** | Detailed complaint description |
| `files` | file[] | No | Supporting documents (PDF, PNG, JPG, JPEG, max 10MB each) |

**Response:**

```json
{
  "complaint_id": 123,
  "status": "submitted",
  "message": "Aduan berjaya diterima dan sedang diproses / Complaint successfully received and being processed",
  "submitted_at": "2025-01-15T10:30:00",
  "classification": null,
  "classification_confidence": null,
  "similar_cases": null,
  "document_count": 2
}
```

**Example - JavaScript/Fetch:**

```javascript
const formData = new FormData();
formData.append('full_name', 'Ahmad bin Ali');
formData.append('ic_number', '901231-01-5678');
formData.append('phone_number', '012-3456789');
formData.append('email', 'ahmad@email.com');
formData.append('complaint_title', 'Penyalahgunaan kuasa dalam tender');
formData.append('category', 'Rasuah');
formData.append('urgency_level', 'Tinggi');
formData.append('complaint_description', 'Pegawai kerajaan menerima rasuah...');

// Add files
const fileInput = document.getElementById('fileInput');
for (let file of fileInput.files) {
  formData.append('files', file);
}

const response = await fetch('http://localhost:8000/complaints/submit', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('Complaint ID:', result.complaint_id);
```

**Example - Axios:**

```javascript
import axios from 'axios';

const formData = new FormData();
formData.append('full_name', 'Ahmad bin Ali');
formData.append('phone_number', '012-3456789');
formData.append('complaint_title', 'Penyalahgunaan kuasa');
formData.append('category', 'Rasuah');
formData.append('complaint_description', 'Detailed description...');

// Add files
files.forEach(file => {
  formData.append('files', file);
});

const response = await axios.post(
  'http://localhost:8000/complaints/submit',
  formData,
  {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  }
);

console.log('Complaint submitted:', response.data);
```

**Example - React:**

```jsx
import React, { useState } from 'react';
import axios from 'axios';

function ComplaintForm() {
  const [formData, setFormData] = useState({
    full_name: '',
    phone_number: '',
    email: '',
    complaint_title: '',
    category: '',
    urgency_level: 'Sederhana',
    complaint_description: ''
  });
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const data = new FormData();
    Object.keys(formData).forEach(key => {
      if (formData[key]) {
        data.append(key, formData[key]);
      }
    });

    files.forEach(file => {
      data.append('files', file);
    });

    try {
      const response = await axios.post(
        'http://localhost:8000/complaints/submit',
        data
      );
      setResult(response.data);
      alert(`Complaint ${response.data.complaint_id} submitted successfully!`);
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to submit complaint');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Full Name"
        value={formData.full_name}
        onChange={(e) => setFormData({...formData, full_name: e.target.value})}
      />
      <input
        type="tel"
        placeholder="Phone Number *"
        required
        value={formData.phone_number}
        onChange={(e) => setFormData({...formData, phone_number: e.target.value})}
      />
      <input
        type="email"
        placeholder="Email"
        value={formData.email}
        onChange={(e) => setFormData({...formData, email: e.target.value})}
      />
      <input
        type="text"
        placeholder="Complaint Title *"
        required
        value={formData.complaint_title}
        onChange={(e) => setFormData({...formData, complaint_title: e.target.value})}
      />
      <select
        required
        value={formData.category}
        onChange={(e) => setFormData({...formData, category: e.target.value})}
      >
        <option value="">-- Select Category --</option>
        <option value="Rasuah">Rasuah</option>
        <option value="Penyalahgunaan Kuasa">Penyalahgunaan Kuasa</option>
        <option value="Penyelewengan">Penyelewengan</option>
      </select>
      <select
        value={formData.urgency_level}
        onChange={(e) => setFormData({...formData, urgency_level: e.target.value})}
      >
        <option value="Rendah">Rendah</option>
        <option value="Sederhana">Sederhana</option>
        <option value="Tinggi">Tinggi</option>
        <option value="Kritikal">Kritikal</option>
      </select>
      <textarea
        placeholder="Complaint Description *"
        required
        value={formData.complaint_description}
        onChange={(e) => setFormData({...formData, complaint_description: e.target.value})}
      />
      <input
        type="file"
        multiple
        accept=".pdf,.png,.jpg,.jpeg"
        onChange={(e) => setFiles(Array.from(e.target.files))}
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Submitting...' : 'Submit Complaint'}
      </button>
    </form>
  );
}
```

---

### 2. Get Complaint Details

**Endpoint:** `GET /complaints/{complaint_id}`

**Response:**

```json
{
  "id": 123,
  "full_name": "Ahmad bin Ali",
  "ic_number": "901231-01-5678",
  "phone_number": "012-3456789",
  "email": "ahmad@email.com",
  "complaint_title": "Penyalahgunaan kuasa dalam tender",
  "category": "Rasuah",
  "urgency_level": "Tinggi",
  "complaint_description": "Detailed description...",
  "status": "processed",
  "classification": "CORRUPTION",
  "classification_confidence": 87.43,
  "submitted_at": "2025-01-15T10:30:00",
  "processed_at": "2025-01-15T10:30:15",
  "has_documents": true,
  "document_count": 2,
  "documents": [
    {
      "id": 1,
      "complaint_id": 123,
      "filename": "complaint_123_20250115_103000_evidence.pdf",
      "original_filename": "evidence.pdf",
      "file_path": "uploads/complaint_123_20250115_103000_evidence.pdf",
      "file_size": 524288,
      "file_type": "application/pdf",
      "uploaded_at": "2025-01-15T10:30:00"
    }
  ],
  "similar_cases": [
    {
      "id": 1,
      "similar_case_id": 45678,
      "similarity_score": 0.9234,
      "rank": 1,
      "description": "Similar case description..."
    }
  ]
}
```

**Example:**

```javascript
const response = await fetch('http://localhost:8000/complaints/123');
const complaint = await response.json();
console.log('Classification:', complaint.classification);
console.log('Similar cases:', complaint.similar_cases);
```

---

### 3. List Complaints

**Endpoint:** `GET /complaints`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status (pending, classified, processed) |
| `category` | string | Filter by category |
| `limit` | integer | Number of results (default: 50) |
| `offset` | integer | Pagination offset (default: 0) |

**Response:**

```json
{
  "total": 150,
  "complaints": [
    {
      "id": 123,
      "complaint_title": "...",
      "category": "Rasuah",
      "status": "processed",
      "submitted_at": "2025-01-15T10:30:00"
    }
  ],
  "limit": 50,
  "offset": 0
}
```

**Example:**

```javascript
// Get all pending complaints
const response = await fetch('http://localhost:8000/complaints?status=pending&limit=20');
const data = await response.json();
console.log(`Found ${data.total} pending complaints`);
```

---

## Processing Flow

1. **Submission** - Form data and files are submitted via POST request
2. **Storage** - Complaint saved to PostgreSQL, files saved to `uploads/` directory
3. **Background Processing** (automatic, non-blocking):
   - **Classification** - AI model classifies as CORRUPTION or NO CORRUPTION
   - **Similarity Search** - Finds top 5 most similar historical cases
4. **Status Updates** - Status changes from `pending` → `classified` → `processed`

---

## Database Schema

### Complaints Table

```sql
CREATE TABLE complaints (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255),
    ic_number VARCHAR(20),
    phone_number VARCHAR(20) NOT NULL,
    email VARCHAR(255),
    complaint_title VARCHAR(500) NOT NULL,
    category VARCHAR(100) NOT NULL,
    urgency_level VARCHAR(50) DEFAULT 'Sederhana',
    complaint_description TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    classification VARCHAR(50),
    classification_confidence FLOAT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    has_documents BOOLEAN DEFAULT FALSE,
    document_count INTEGER DEFAULT 0
);
```

### Complaint Documents Table

```sql
CREATE TABLE complaint_documents (
    id SERIAL PRIMARY KEY,
    complaint_id INTEGER REFERENCES complaints(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    file_type VARCHAR(50),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Similar Cases Table

```sql
CREATE TABLE similar_cases (
    id SERIAL PRIMARY KEY,
    complaint_id INTEGER REFERENCES complaints(id) ON DELETE CASCADE,
    similar_case_id INTEGER,
    similarity_score FLOAT,
    rank INTEGER,
    found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Error Handling

All errors return JSON:

```json
{
  "detail": "Error message description"
}
```

**Common Errors:**

- `400` - Bad Request (missing required fields)
- `404` - Complaint not found
- `500` - Internal Server Error
- `503` - Service Unavailable (database/model not ready)

**Example Error Handling:**

```javascript
try {
  const response = await axios.post('/complaints/submit', formData);
  // Handle success
} catch (error) {
  if (error.response) {
    // Server responded with error
    console.error('Error:', error.response.data.detail);
    alert(`Error: ${error.response.data.detail}`);
  } else if (error.request) {
    // No response from server
    alert('Server is not responding');
  } else {
    // Other errors
    console.error('Error:', error.message);
  }
}
```

---

## Testing

### 1. Using cURL

```bash
# Submit complaint without files
curl -X POST "http://localhost:8000/complaints/submit" \
  -F "phone_number=012-3456789" \
  -F "complaint_title=Test Complaint" \
  -F "category=Rasuah" \
  -F "complaint_description=This is a test complaint"

# Submit complaint with files
curl -X POST "http://localhost:8000/complaints/submit" \
  -F "phone_number=012-3456789" \
  -F "complaint_title=Test Complaint" \
  -F "category=Rasuah" \
  -F "complaint_description=This is a test complaint" \
  -F "files=@/path/to/document.pdf" \
  -F "files=@/path/to/image.jpg"

# Get complaint details
curl "http://localhost:8000/complaints/1"

# List complaints
curl "http://localhost:8000/complaints?status=processed&limit=10"
```

### 2. Using Postman

1. Set method to `POST`
2. URL: `http://localhost:8000/complaints/submit`
3. Body → form-data
4. Add text fields and file fields
5. Send request

---

## Production Considerations

### 1. File Upload Limits

Currently accepts PDF, PNG, JPG, JPEG up to 10MB each. Adjust in code if needed:

```python
# In src/main.py
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg'}
```

### 2. CORS Configuration

Update allowed origins in `src/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Database Connection Pool

Adjust pool size in `src/database.py` based on expected load:

```python
self.pool = SimpleConnectionPool(
    minconn=5,
    maxconn=20,  # Increase for production
    ...
)
```

### 4. File Storage

For production, consider using cloud storage (S3, Azure Blob, etc.) instead of local `uploads/` directory.

---

## Monitoring

The API logs all important events:

```
✅ Complaint 123 saved to database
✅ File uploaded: evidence.pdf (524288 bytes)
✅ Background processing completed for complaint 123
   Classification: CORRUPTION (87.43%)
   Similar cases found: 5
```

Monitor these logs to track complaint processing status.
