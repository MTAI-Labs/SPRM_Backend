# Frontend Quick Start Guide - SPRM Dashboard

**Last Updated**: January 2025
**Backend Version**: 2.3.0

---

## 🚀 Quick Start (5 Minutes)

### 1. Start Backend Server

```bash
cd SPRM_Backend
python src/main.py
```

✅ **Server URL**: `http://localhost:8000`
📚 **API Docs**: `http://localhost:8000/docs`

### 2. Test Connection

```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "model_loaded": true
}
```

---

## 📋 What You Need to Build: Dashboard Features

Your dashboard should have these main features:

### 1. **Complaint Submission Form**
- Users submit complaints with optional file uploads
- Background processing handles AI analysis
- Returns complaint ID immediately

### 2. **Complaint List View**
- Display all complaints with filters (status, category)
- Show sector and akta (legislation) for each complaint
- Show classification (CRIS/NFA) with confidence
- Pagination support

### 3. **Case Management Dashboard** ⭐ **NEW**
- View cases (groups of related complaints)
- Each case contains multiple complaints
- Auto-grouped by AI or manually created
- Case status tracking (open, investigating, closed)

### 4. **Case Details View**
- View all complaints in a case
- See similarity scores
- Move complaints between cases
- Update case status/priority

---

## 🎯 Core API Endpoints

### 1️⃣ Submit Complaint (with Files)

**Endpoint**: `POST /complaints/submit`
**Content-Type**: `multipart/form-data`

**JavaScript Example**:
```javascript
const submitComplaint = async (formData) => {
  const form = new FormData();

  // Required fields
  form.append('phone_number', '012-3456789');
  form.append('complaint_title', 'Rasuah di JKR');
  form.append('category', 'Rasuah');
  form.append('complaint_description', 'Pegawai menerima rasuah RM50,000...');

  // Optional fields
  form.append('full_name', 'Ahmad bin Ali');
  form.append('email', 'ahmad@example.com');
  form.append('urgency_level', 'Tinggi');

  // Files (can be multiple)
  const fileInput = document.getElementById('fileInput');
  for (let file of fileInput.files) {
    form.append('files', file);
  }

  const response = await fetch('http://localhost:8000/complaints/submit', {
    method: 'POST',
    body: form
  });

  const result = await response.json();
  console.log(result);
  // {
  //   "complaint_id": 1,
  //   "status": "submitted",
  //   "message": "Aduan berjaya diterima...",
  //   "submitted_at": "2025-01-27T10:30:00",
  //   "document_count": 2
  // }

  return result.complaint_id;
};
```

**⚡ Important - Background Processing:**
- API returns immediately (1-2 seconds) with `status: "submitted"`
- AI processing happens in background (5W1H, sector, akta, classification)
- System processes up to 5 complaints simultaneously
- Multiple users can submit at the same time without blocking
- Poll `GET /complaints/{id}` to check when `status` becomes `"processed"`

**React Hook Example with Status Polling**:
```jsx
const [uploading, setUploading] = useState(false);
const [processingStatus, setProcessingStatus] = useState(null);

const pollComplaintStatus = async (complaintId) => {
  // Check status every 3 seconds until processed
  const interval = setInterval(async () => {
    const response = await fetch(`http://localhost:8000/complaints/${complaintId}`);
    const complaint = await response.json();

    setProcessingStatus(complaint.status);

    if (complaint.status === 'processed') {
      clearInterval(interval);
      console.log('Processing complete!', complaint);
      // Show notification or update UI
    }
  }, 3000);

  // Stop polling after 5 minutes
  setTimeout(() => clearInterval(interval), 300000);
};

const handleSubmit = async (e) => {
  e.preventDefault();
  setUploading(true);

  const formData = new FormData(e.target);

  try {
    const response = await fetch('http://localhost:8000/complaints/submit', {
      method: 'POST',
      body: formData
    });

    const result = await response.json();
    alert(`Complaint ${result.complaint_id} submitted successfully! Processing in background...`);

    // Start polling for status
    pollComplaintStatus(result.complaint_id);

    // Navigate to complaint details page
    // router.push(`/complaints/${result.complaint_id}`);
  } catch (error) {
    alert('Error: ' + error.message);
  } finally {
    setUploading(false);
  }
};
```

---

### 2️⃣ Get Complaint Details

**Endpoint**: `GET /complaints/{complaint_id}`

**JavaScript Example**:
```javascript
const getComplaintDetails = async (complaintId) => {
  const response = await fetch(`http://localhost:8000/complaints/${complaintId}`);
  const complaint = await response.json();

  console.log(complaint);
  // {
  //   "id": 1,
  //   "complaint_title": "Rasuah di JKR",
  //   "complaint_description": "...",
  //   "sector": "Pembinaan & Infrastruktur",
  //   "akta": "Akta SPRM 2009",
  //   "classification": "CRIS",
  //   "classification_confidence": 0.92,
  //   "status": "processed",
  //   "extracted_data": {
  //     "entities": {
  //       "names": ["Ahmad", "Dato' Rashid"],
  //       "locations": ["Kuala Lumpur"],
  //       "amounts": ["RM 50,000"]
  //     }
  //   },
  //   "w1h_summary": "**WHAT:** Pegawai menerima rasuah...",
  //   "documents": [
  //     {
  //       "id": 1,
  //       "filename": "evidence.jpg",
  //       "file_size": 524288
  //     }
  //   ],
  //   "submitted_at": "2025-01-27T10:30:00"
  // }

  return complaint;
};
```

---

### 3️⃣ List All Complaints

**Endpoint**: `GET /complaints?status=processed&limit=50&offset=0`

**JavaScript Example**:
```javascript
const listComplaints = async (filters = {}) => {
  const params = new URLSearchParams({
    limit: filters.limit || 50,
    offset: filters.offset || 0,
    ...(filters.status && { status: filters.status }),
    ...(filters.category && { category: filters.category })
  });

  const response = await fetch(`http://localhost:8000/complaints?${params}`);
  const data = await response.json();

  return data.complaints;
};

// Usage
const complaints = await listComplaints({
  status: 'processed',
  limit: 20
});
```

---

### 4️⃣ Update Complaint (Edit 5W1H) ⭐ **NEW**

**Endpoint**: `PUT /complaints/{complaint_id}`

**Description**: Update complaint fields, especially useful for editing AI-generated 5W1H summaries.

**JavaScript Example**:
```javascript
const updateComplaint = async (complaintId, updates) => {
  const response = await fetch(`http://localhost:8000/complaints/${complaintId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates)
  });

  const updatedComplaint = await response.json();
  return updatedComplaint;
};

// Example: Update 5W1H fields
await updateComplaint(1, {
  w1h_what: "Pegawai kerajaan menerima wang rasuah RM100,000",
  w1h_who: "En. Ahmad bin Ali (Pegawai JKR) dan Dato' Rashid",
  w1h_when: "15 Januari 2024",
  classification: "CRIS"
});

// Example: Update complaint title and description
await updateComplaint(1, {
  complaint_title: "Updated Title",
  complaint_description: "Updated description"
});
```

**Editable Fields**:
- `complaint_title`, `complaint_description`, `category`, `urgency_level`
- `w1h_what`, `w1h_who`, `w1h_when`, `w1h_where`, `w1h_why`, `w1h_how`
- `w1h_summary` (full text)
- `classification`, `classification_confidence`, `status`

**React Example - Edit 5W1H Form**:
```jsx
const Edit5W1HForm = ({ complaint, onSave }) => {
  const [w1h, setW1h] = useState({
    w1h_what: complaint.w1h_what || '',
    w1h_who: complaint.w1h_who || '',
    w1h_when: complaint.w1h_when || '',
    w1h_where: complaint.w1h_where || '',
    w1h_why: complaint.w1h_why || '',
    w1h_how: complaint.w1h_how || ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();

    const response = await fetch(`http://localhost:8000/complaints/${complaint.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(w1h)
    });

    const updated = await response.json();
    onSave(updated);
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label>WHAT (Apa)</label>
        <textarea
          value={w1h.w1h_what}
          onChange={(e) => setW1h({...w1h, w1h_what: e.target.value})}
          rows={3}
        />
      </div>
      <div>
        <label>WHO (Siapa)</label>
        <textarea
          value={w1h.w1h_who}
          onChange={(e) => setW1h({...w1h, w1h_who: e.target.value})}
          rows={3}
        />
      </div>
      {/* Similar fields for when, where, why, how */}
      <button type="submit">Save Changes</button>
    </form>
  );
};
```

---

### 5️⃣ Download/Preview Document

**Endpoint**: `GET /documents/{document_id}/download`

**Description**: Download or preview uploaded files (images, PDFs, etc.)

**Frontend Usage**:

**Image Preview (HTML)**:
```html
<!-- Complaint details page showing evidence -->
<div className="complaint-documents">
  {complaint.documents?.map(doc => (
    <div key={doc.id} className="document-card">
      <img
        src={`http://localhost:8000/documents/${doc.id}/download`}
        alt={doc.original_filename}
        style={{ maxWidth: '400px' }}
      />
      <p>{doc.original_filename} ({(doc.file_size / 1024).toFixed(1)} KB)</p>
    </div>
  ))}
</div>
```

**Download Link**:
```html
<a href={`http://localhost:8000/documents/${doc.id}/download`} download>
  📥 Download {doc.original_filename}
</a>
```

**JavaScript Fetch (for programmatic download)**:
```javascript
const downloadDocument = async (documentId, filename) => {
  const response = await fetch(`http://localhost:8000/documents/${documentId}/download`);
  const blob = await response.blob();

  // Create temporary link and trigger download
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
};

// Usage
downloadDocument(123, 'evidence.pdf');
```

**React Component Example**:
```jsx
const DocumentViewer = ({ documents }) => {
  return (
    <div className="documents-grid">
      {documents.map(doc => {
        const isImage = doc.file_type.startsWith('image/');
        const downloadUrl = `http://localhost:8000/documents/${doc.id}/download`;

        return (
          <div key={doc.id} className="document-item">
            {isImage ? (
              <img src={downloadUrl} alt={doc.original_filename} />
            ) : (
              <div className="file-icon">📄 {doc.original_filename}</div>
            )}
            <a href={downloadUrl} download className="download-btn">
              Download
            </a>
          </div>
        );
      })}
    </div>
  );
};
```

---

### 6️⃣ List All Cases ⭐ **NEW**

**Endpoint**: `GET /cases?status=open&limit=50`

**JavaScript Example**:
```javascript
const listCases = async (filters = {}) => {
  const params = new URLSearchParams({
    limit: filters.limit || 50,
    offset: filters.offset || 0,
    ...(filters.status && { status: filters.status })
  });

  const response = await fetch(`http://localhost:8000/cases?${params}`);
  const data = await response.json();

  console.log(data);
  // {
  //   "total": 25,
  //   "cases": [
  //     {
  //       "id": 1,
  //       "case_number": "CASE-2025-0001",
  //       "case_title": "JKR Rasuah Tender",
  //       "status": "open",
  //       "priority": "high",
  //       "classification": "CRIS",
  //       "complaint_count": 3,
  //       "auto_grouped": true,
  //       "created_at": "2025-01-27T10:30:00"
  //     }
  //   ]
  // }

  return data.cases;
};
```

---

### 7️⃣ Get Case Details ⭐ **NEW**

**Endpoint**: `GET /cases/{case_id}`

**JavaScript Example**:
```javascript
const getCaseDetails = async (caseId) => {
  const response = await fetch(`http://localhost:8000/cases/${caseId}`);
  const caseData = await response.json();

  console.log(caseData);
  // {
  //   "id": 1,
  //   "case_number": "CASE-2025-0001",
  //   "case_title": "JKR Rasuah Tender",
  //   "status": "open",
  //   "priority": "high",
  //   "classification": "CRIS",
  //   "complaint_count": 3,
  //   "complaints": [
  //     {
  //       "id": 1,
  //       "complaint_title": "Pegawai JKR terima rasuah",
  //       "similarity_score": 1.0,
  //       "added_by": "system",
  //       "submitted_at": "2025-01-27T10:30:00"
  //     },
  //     {
  //       "id": 3,
  //       "complaint_title": "Saksi rasuah JKR",
  //       "similarity_score": 0.85,
  //       "added_by": "system"
  //     }
  //   ]
  // }

  return caseData;
};
```

---

### 8️⃣ Create Case Manually ⭐ **NEW**

**Endpoint**: `POST /cases`

**JavaScript Example**:
```javascript
const createCase = async (complaintIds, title, addedBy = 'user') => {
  const response = await fetch('http://localhost:8000/cases', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      complaint_ids: complaintIds,
      case_title: title,
      added_by: addedBy
    })
  });

  const result = await response.json();
  console.log(result);
  // {
  //   "message": "Case created successfully",
  //   "case_id": 1,
  //   "case_number": "CASE-2025-0001",
  //   "case": { /* full case details */ }
  // }

  return result.case_id;
};

// Usage: Group complaints 1, 3, 5 into new case
await createCase([1, 3, 5], 'JKR Tender Scandal', 'officer_ahmad');
```

---

### 9️⃣ Update Case ⭐ **NEW**

**Endpoint**: `PUT /cases/{case_id}`

**JavaScript Example**:
```javascript
const updateCase = async (caseId, updates) => {
  const response = await fetch(`http://localhost:8000/cases/${caseId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates)
  });

  return await response.json();
};

// Update case status
await updateCase(1, {
  status: 'investigating',
  priority: 'critical'
});

// Update case title
await updateCase(1, {
  case_title: 'Updated Title'
});
```

---

### 🔟 Move Complaint to Case ⭐ **NEW**

**Endpoint**: `POST /cases/{case_id}/complaints`

**JavaScript Example**:
```javascript
const addComplaintToCase = async (caseId, complaintId, addedBy = 'user') => {
  const response = await fetch(`http://localhost:8000/cases/${caseId}/complaints`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      complaint_id: complaintId,
      added_by: addedBy
    })
  });

  return await response.json();
};

// Move complaint #7 to case #1
await addComplaintToCase(1, 7, 'officer_fatimah');
```

---

### 🔟 Remove Complaint from Case ⭐ **NEW**

**Endpoint**: `DELETE /cases/{case_id}/complaints/{complaint_id}`

**JavaScript Example**:
```javascript
const removeComplaintFromCase = async (caseId, complaintId) => {
  const response = await fetch(
    `http://localhost:8000/cases/${caseId}/complaints/${complaintId}`,
    { method: 'DELETE' }
  );

  return await response.json();
};

// Remove complaint #7 from case #1
await removeComplaintFromCase(1, 7);
```

---

## 🎨 Complete React Dashboard Example

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

function SPRMDashboard() {
  const [cases, setCases] = useState([]);
  const [selectedCase, setSelectedCase] = useState(null);
  const [loading, setLoading] = useState(false);

  // Load all cases
  useEffect(() => {
    loadCases();
  }, []);

  const loadCases = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/cases?status=open`);
      setCases(response.data.cases);
    } catch (error) {
      console.error('Error loading cases:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCaseDetails = async (caseId) => {
    try {
      const response = await axios.get(`${API_URL}/cases/${caseId}`);
      setSelectedCase(response.data);
    } catch (error) {
      console.error('Error loading case details:', error);
    }
  };

  const updateCaseStatus = async (caseId, newStatus) => {
    try {
      await axios.put(`${API_URL}/cases/${caseId}`, {
        status: newStatus
      });
      alert('Case status updated!');
      loadCases();
    } catch (error) {
      alert('Error updating case: ' + error.message);
    }
  };

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      {/* Cases List */}
      <div style={{ width: '300px', borderRight: '1px solid #ddd', padding: '20px', overflowY: 'auto' }}>
        <h2>Cases ({cases.length})</h2>

        {loading ? (
          <p>Loading...</p>
        ) : (
          cases.map(c => (
            <div
              key={c.id}
              onClick={() => loadCaseDetails(c.id)}
              style={{
                padding: '10px',
                marginBottom: '10px',
                border: '1px solid #ddd',
                cursor: 'pointer',
                backgroundColor: selectedCase?.id === c.id ? '#e3f2fd' : 'white'
              }}
            >
              <div style={{ fontWeight: 'bold' }}>{c.case_number}</div>
              <div style={{ fontSize: '14px' }}>{c.case_title}</div>
              <div style={{ fontSize: '12px', color: '#666' }}>
                {c.complaint_count} complaints • {c.classification}
              </div>
              <div style={{ fontSize: '12px' }}>
                <span style={{
                  padding: '2px 6px',
                  borderRadius: '3px',
                  backgroundColor: c.status === 'open' ? '#4caf50' : '#ff9800',
                  color: 'white'
                }}>
                  {c.status.toUpperCase()}
                </span>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Case Details */}
      <div style={{ flex: 1, padding: '20px', overflowY: 'auto' }}>
        {selectedCase ? (
          <>
            <h1>{selectedCase.case_number}</h1>
            <h2>{selectedCase.case_title}</h2>

            <div style={{ marginBottom: '20px' }}>
              <strong>Status:</strong> {selectedCase.status} |
              <strong> Priority:</strong> {selectedCase.priority} |
              <strong> Classification:</strong> {selectedCase.classification}
            </div>

            <div style={{ marginBottom: '20px' }}>
              <button onClick={() => updateCaseStatus(selectedCase.id, 'investigating')}>
                Mark as Investigating
              </button>
              <button onClick={() => updateCaseStatus(selectedCase.id, 'closed')} style={{ marginLeft: '10px' }}>
                Close Case
              </button>
            </div>

            <h3>Complaints in this Case ({selectedCase.complaint_count})</h3>
            {selectedCase.complaints.map(complaint => (
              <div key={complaint.id} style={{ padding: '15px', border: '1px solid #ddd', marginBottom: '10px' }}>
                <h4>Complaint #{complaint.id}: {complaint.complaint_title}</h4>
                <p>{complaint.complaint_description?.substring(0, 200)}...</p>
                <div style={{ fontSize: '12px', color: '#666' }}>
                  Similarity: {(complaint.similarity_score * 100).toFixed(1)}% •
                  Added by: {complaint.added_by} •
                  Classification: {complaint.classification}
                </div>
              </div>
            ))}
          </>
        ) : (
          <div style={{ textAlign: 'center', marginTop: '100px', color: '#999' }}>
            <h2>Select a case to view details</h2>
          </div>
        )}
      </div>
    </div>
  );
}

export default SPRMDashboard;
```

---

## 🎯 TypeScript Definitions

```typescript
// Complaint Types
export interface Complaint {
  id: number;
  full_name?: string;
  phone_number: string;
  complaint_title: string;
  category: string;
  complaint_description: string;
  classification?: 'CRIS' | 'NFA';
  classification_confidence?: number;
  status: 'pending' | 'submitted' | 'processed';
  extracted_data?: {
    entities: {
      names: string[];
      organizations: string[];
      locations: string[];
      dates: string[];
      amounts: string[];
    };
  };
  w1h_summary?: string;  // Full text format
  w1h_what?: string;     // Structured: What happened
  w1h_who?: string;      // Structured: Who involved
  w1h_when?: string;     // Structured: When
  w1h_where?: string;    // Structured: Where
  w1h_why?: string;      // Structured: Why
  w1h_how?: string;      // Structured: How
  sector?: string;       // Government sector (10 categories)
  akta?: string;         // Relevant Malaysian legislation
  submitted_at: string;
  processed_at?: string;
  has_documents: boolean;
  document_count: number;
  documents?: ComplaintDocument[];
}

export interface ComplaintDocument {
  id: number;
  filename: string;
  original_filename: string;
  file_size: number;
  file_type: string;
  uploaded_at: string;
}

// Case Types
export interface Case {
  id: number;
  case_number: string;
  case_title: string;
  case_description?: string;
  primary_complaint_id: number;
  common_keywords: string[];
  status: 'open' | 'investigating' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'critical';
  classification?: 'CRIS' | 'NFA';
  complaint_count: number;
  auto_grouped: boolean;
  created_at: string;
  updated_at: string;
  complaints?: CaseComplaint[];
}

export interface CaseComplaint extends Complaint {
  similarity_score: number;
  added_by: string;
  added_at: string;
}

// API Client
import axios, { AxiosInstance } from 'axios';

class SPRMApiClient {
  private client: AxiosInstance;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.client = axios.create({ baseURL });
  }

  // Complaints
  async submitComplaint(formData: FormData): Promise<{ complaint_id: number }> {
    const { data } = await this.client.post('/complaints/submit', formData);
    return data;
  }

  async getComplaint(id: number): Promise<Complaint> {
    const { data } = await this.client.get(`/complaints/${id}`);
    return data;
  }

  async listComplaints(params?: {
    status?: string;
    category?: string;
    limit?: number;
    offset?: number;
  }): Promise<Complaint[]> {
    const { data } = await this.client.get('/complaints', { params });
    return data.complaints;
  }

  async updateComplaint(id: number, updates: Partial<Complaint>): Promise<Complaint> {
    const { data } = await this.client.put(`/complaints/${id}`, updates);
    return data;
  }

  // Documents
  getDocumentUrl(documentId: number): string {
    return `${this.client.defaults.baseURL}/documents/${documentId}/download`;
  }

  async downloadDocument(documentId: number, filename: string): Promise<void> {
    const response = await fetch(this.getDocumentUrl(documentId));
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }

  // Cases
  async listCases(params?: {
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<Case[]> {
    const { data } = await this.client.get('/cases', { params });
    return data.cases;
  }

  async getCase(id: number): Promise<Case> {
    const { data } = await this.client.get(`/cases/${id}`);
    return data;
  }

  async createCase(complaintIds: number[], title?: string, addedBy?: string): Promise<Case> {
    const { data } = await this.client.post('/cases', {
      complaint_ids: complaintIds,
      case_title: title,
      added_by: addedBy
    });
    return data.case;
  }

  async updateCase(id: number, updates: Partial<Case>): Promise<Case> {
    const { data } = await this.client.put(`/cases/${id}`, updates);
    return data.case;
  }

  async deleteCase(id: number): Promise<void> {
    await this.client.delete(`/cases/${id}`);
  }

  async addComplaintToCase(caseId: number, complaintId: number, addedBy?: string): Promise<Case> {
    const { data } = await this.client.post(`/cases/${caseId}/complaints`, {
      complaint_id: complaintId,
      added_by: addedBy
    });
    return data.case;
  }

  async removeComplaintFromCase(caseId: number, complaintId: number): Promise<void> {
    await this.client.delete(`/cases/${caseId}/complaints/${complaintId}`);
  }
}

export default SPRMApiClient;
```

---

## 📊 Dashboard Features Checklist

### Essential Features
- [ ] **Complaint Submission Form** with file upload
- [ ] **Complaint List** with filters (status, category)
- [ ] **Complaint Details** page showing 5W1H summary
- [ ] **Cases Dashboard** showing all cases
- [ ] **Case Details** showing grouped complaints
- [ ] **Status Updates** for cases (open → investigating → closed)

### Advanced Features
- [ ] **Manual Case Creation** - Group selected complaints
- [ ] **Move Complaints** between cases (drag & drop?)
- [ ] **Search/Filter** - Search by keywords, dates, entities
- [ ] **Statistics** - Charts showing CRIS vs NFA, cases by status
- [ ] **Real-time Updates** - Polling or WebSocket for status changes
- [ ] **Export** - Export case details to PDF/Excel

---

## 🐛 Common Issues

### Issue: "Backend error: Files validation error"
**Solution**: Ensure you're sending `files` as `multipart/form-data`, not JSON

### Issue: Complaint shows "pending" forever
**Solution**: Check backend logs - AI processing might have failed. Files may be too large.

### Issue: No cases showing up
**Solution**: System needs at least 2 processed complaints to start grouping. Submit more complaints first.

### Issue: CORS Error
**Solution**: Backend already has CORS enabled. Clear browser cache or check backend is running.

---

## 🎉 You're Ready to Build!

Your dashboard should show:
1. **Complaints** - Individual reports from public
2. **Cases** - Grouped related complaints (auto or manual)
3. **Processing Pipeline** - Status tracking for each complaint
4. **Case Management** - Officers can organize and investigate

**Questions?** Check `/docs` endpoint at http://localhost:8000/docs for interactive API testing!

**Good luck! 🚀**
