# File Access Architecture - Suggestion & Structure

## Current Situation

**Files are stored:**
- Location: `uploads/` folder on server filesystem
- Naming: `complaint_{id}_{timestamp}_{original_filename}`
- Database: Only metadata stored (file_path, file_size, file_type)
- Example: `uploads/complaint_45_20251031_171554_Case4.pdf`

**Database (documents table):**
```sql
- id
- complaint_id
- filename (unique_filename)
- original_filename (user's original name)
- file_path (relative path: uploads/complaint_45_...)
- file_size
- file_type (mime type)
- uploaded_at
```

---

## Problem

Frontend cannot directly access files in `uploads/` folder because:
1. Security: Direct filesystem access is blocked
2. CORS: Browser cannot read local server files
3. No HTTP endpoint to serve files

---

## Solution Options

### **Option 1: Static File Serving (Simple & Recommended)**

**Architecture:**
```
Frontend Request:
GET /uploads/{filename}
    ↓
FastAPI Static Files Middleware
    ↓
Read file from uploads/ folder
    ↓
Return file with proper headers
```

**Pros:**
- ✅ Simple to implement (1 line of code)
- ✅ Fast (direct file serving)
- ✅ No database queries needed
- ✅ Works with any file type (PDF, images, etc.)
- ✅ Built-in caching support

**Cons:**
- ⚠️ Less secure (anyone with URL can access)
- ⚠️ No access control (can't restrict by user/role)
- ⚠️ Files exposed if someone guesses filename

**Backend Structure:**
```python
# In main.py
from fastapi.staticfiles import StaticFiles

# Mount uploads folder as static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
```

**Frontend Access:**
```javascript
// Direct access via URL
const fileUrl = `http://localhost:8000/uploads/complaint_45_20251031_171554_Case4.pdf`;

// Display in iframe
<iframe src={fileUrl} width="100%" height="600px"></iframe>

// Display image
<img src={fileUrl} alt="Evidence" />

// Download link
<a href={fileUrl} download>Download File</a>
```

---

### **Option 2: Secure File Endpoint (Recommended for Production)**

**Architecture:**
```
Frontend Request:
GET /complaints/{complaint_id}/files/{document_id}
    ↓
Backend validates access (check if user has permission)
    ↓
Query database for file metadata
    ↓
Read file from filesystem
    ↓
Return file with secure headers
```

**Pros:**
- ✅ Secure (access control per request)
- ✅ Can restrict by user role/permissions
- ✅ Audit trail (log who accessed what)
- ✅ Can add rate limiting
- ✅ Can check if complaint is assigned to officer

**Cons:**
- ⚠️ More code to write
- ⚠️ Slightly slower (database query + validation)
- ⚠️ Need to handle different file types

**Backend Structure:**
```python
# Endpoint 1: Get list of files for a complaint
GET /complaints/{complaint_id}/documents
Response: [
  {
    "id": 1,
    "filename": "complaint_45_20251031_171554_Case4.pdf",
    "original_filename": "Case4.pdf",
    "file_size": 125000,
    "file_type": "application/pdf",
    "uploaded_at": "2025-10-31T17:15:54"
  }
]

# Endpoint 2: Download specific file
GET /complaints/{complaint_id}/documents/{document_id}/download
Response: <file binary data>
Headers:
  Content-Type: application/pdf
  Content-Disposition: inline; filename="Case4.pdf"
  Content-Length: 125000

# Endpoint 3: Stream file (for preview)
GET /complaints/{complaint_id}/documents/{document_id}/stream
Response: <streamed file data>
Headers:
  Content-Type: application/pdf
  Accept-Ranges: bytes
```

**Frontend Access:**
```javascript
// 1. Get list of files
const response = await fetch(`/complaints/${complaintId}/documents`);
const documents = await response.json();

// 2. Build download URL for each file
documents.forEach(doc => {
  const downloadUrl = `/complaints/${complaintId}/documents/${doc.id}/download`;
  const previewUrl = `/complaints/${complaintId}/documents/${doc.id}/stream`;

  // Display download link
  <a href={downloadUrl} download={doc.original_filename}>
    Download {doc.original_filename}
  </a>

  // Display in iframe (for PDF preview)
  <iframe src={previewUrl} width="100%" height="600px"></iframe>
});
```

---

### **Option 3: Base64 Encoding (Not Recommended)**

**Architecture:**
```
Backend reads file → Encode to Base64 → Return in JSON → Frontend decodes
```

**Pros:**
- ✅ No separate file endpoint needed

**Cons:**
- ❌ Very slow for large files
- ❌ 33% larger file size
- ❌ High memory usage
- ❌ Not suitable for PDFs > 1MB

**Not recommended for SPRM system** (files can be large PDFs)

---

## Recommended Approach

### **Development/Testing: Option 1 (Static Files)**
Use for quick development and testing.

### **Production: Option 2 (Secure Endpoint)**
Use for actual deployment with proper access control.

---

## Detailed Structure for Option 2 (Recommended)

### Backend Implementation Structure

```python
# main.py

# 1. Endpoint to list documents
@app.get("/complaints/{complaint_id}/documents")
async def get_complaint_documents(complaint_id: int):
    """Get all documents for a complaint"""
    # Query database for documents
    # Return metadata (NOT file content)
    return [
        {
            "id": doc_id,
            "filename": filename,
            "original_filename": original_name,
            "file_size": size,
            "file_type": mime_type,
            "uploaded_at": timestamp
        }
    ]

# 2. Endpoint to download file
@app.get("/complaints/{complaint_id}/documents/{document_id}/download")
async def download_document(complaint_id: int, document_id: int):
    """Download a specific document"""
    # 1. Validate complaint exists
    # 2. Query database for document metadata
    # 3. Check if file exists on disk
    # 4. Return file with proper headers

    return FileResponse(
        path=file_path,
        media_type=file_type,
        filename=original_filename,
        headers={
            "Content-Disposition": f"attachment; filename={original_filename}"
        }
    )

# 3. Endpoint to stream/preview file (in browser)
@app.get("/complaints/{complaint_id}/documents/{document_id}/stream")
async def stream_document(complaint_id: int, document_id: int):
    """Stream a document for preview"""
    # Similar to download, but with 'inline' disposition

    return FileResponse(
        path=file_path,
        media_type=file_type,
        headers={
            "Content-Disposition": f"inline; filename={original_filename}"
        }
    )

# Optional: Thumbnail for images
@app.get("/complaints/{complaint_id}/documents/{document_id}/thumbnail")
async def get_document_thumbnail(document_id: int):
    """Get thumbnail for image files"""
    # Only for images
    # Resize image and return thumbnail
    pass
```

### Frontend Implementation Structure

```javascript
// ComplaintDocuments.jsx

function ComplaintDocuments({ complaintId }) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDocuments();
  }, [complaintId]);

  const loadDocuments = async () => {
    const response = await fetch(`/complaints/${complaintId}/documents`);
    const data = await response.json();
    setDocuments(data);
    setLoading(false);
  };

  const downloadFile = (docId, filename) => {
    const url = `/complaints/${complaintId}/documents/${docId}/download`;
    // Trigger browser download
    window.open(url, '_blank');
  };

  const previewFile = (docId, fileType) => {
    const url = `/complaints/${complaintId}/documents/${docId}/stream`;

    if (fileType === 'application/pdf') {
      // Open PDF in new tab
      window.open(url, '_blank');
    } else if (fileType.startsWith('image/')) {
      // Show in modal
      setPreviewUrl(url);
      setShowModal(true);
    }
  };

  return (
    <div className="documents">
      <h3>Uploaded Documents ({documents.length})</h3>

      {documents.map(doc => (
        <div key={doc.id} className="document-card">
          <div className="document-icon">
            {getFileIcon(doc.file_type)}
          </div>

          <div className="document-info">
            <h4>{doc.original_filename}</h4>
            <p>Size: {formatFileSize(doc.file_size)}</p>
            <p>Uploaded: {new Date(doc.uploaded_at).toLocaleString()}</p>
          </div>

          <div className="document-actions">
            <button onClick={() => previewFile(doc.id, doc.file_type)}>
              Preview
            </button>
            <button onClick={() => downloadFile(doc.id, doc.original_filename)}>
              Download
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

// Helper functions
function getFileIcon(fileType) {
  if (fileType === 'application/pdf') return '📄';
  if (fileType.startsWith('image/')) return '🖼️';
  return '📎';
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}
```

---

## Security Considerations

### For Option 1 (Static Files):
```python
# Add authentication middleware
@app.middleware("http")
async def check_file_access(request: Request, call_next):
    if request.url.path.startswith("/uploads/"):
        # Check if user is authenticated
        # Check if user has permission to access this complaint
        pass
    return await call_next(request)
```

### For Option 2 (Secure Endpoint):
```python
@app.get("/complaints/{complaint_id}/documents/{document_id}/download")
async def download_document(
    complaint_id: int,
    document_id: int,
    current_user: User = Depends(get_current_user)  # Require authentication
):
    # Check if user has permission
    if not has_access_to_complaint(current_user, complaint_id):
        raise HTTPException(status_code=403, detail="Access denied")

    # ... rest of code
```

---

## File Size Considerations

### Large Files (> 10MB):
```python
# Use StreamingResponse for large files
from fastapi.responses import StreamingResponse

@app.get("/documents/{document_id}/stream")
async def stream_large_file(document_id: int):
    def file_generator(file_path):
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):  # 8KB chunks
                yield chunk

    return StreamingResponse(
        file_generator(file_path),
        media_type=file_type,
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )
```

---

## Summary Table

| Feature | Option 1 (Static) | Option 2 (Secure) |
|---------|-------------------|-------------------|
| **Implementation** | 1 line | ~50 lines |
| **Security** | ❌ Low | ✅ High |
| **Speed** | ⚡ Fast | ⚡ Fast |
| **Access Control** | ❌ None | ✅ Yes |
| **Audit Trail** | ❌ No | ✅ Yes |
| **Best For** | Development | Production |

---

## My Recommendation

**Phase 1 (Now):** Use **Option 1** for quick development
- Add 1 line to mount static files
- Frontend can immediately access files
- Good for testing and development

**Phase 2 (Before Production):** Migrate to **Option 2**
- Add secure endpoints
- Implement access control
- Add audit logging
- Remove static file mounting

This gives you quick progress now while maintaining a clear path to production-ready security.
