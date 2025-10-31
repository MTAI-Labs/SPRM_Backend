# File Access Frontend Guide - Static Files

## ✅ Backend Setup Complete

Files are now accessible via static URL:
```
http://localhost:8000/uploads/{filename}
```

---

## How to Access Uploaded Files

### Step 1: Get Document List

```javascript
// Fetch documents for a complaint
const response = await fetch(`http://localhost:8000/complaints/${complaintId}`);
const complaint = await response.json();

// Documents are in complaint.documents array
const documents = complaint.documents;

console.log(documents);
// Output:
// [
//   {
//     "id": 1,
//     "filename": "complaint_45_20251031_171554_Case4.pdf",
//     "original_filename": "Case4.pdf",
//     "file_size": 125000,
//     "file_type": "application/pdf",
//     "uploaded_at": "2025-10-31T17:15:54"
//   }
// ]
```

### Step 2: Build File URL

```javascript
// Build URL from filename
documents.forEach(doc => {
  const fileUrl = `http://localhost:8000/uploads/${doc.filename}`;
  console.log(fileUrl);
  // Output: http://localhost:8000/uploads/complaint_45_20251031_171554_Case4.pdf
});
```

---

## Display Files in Frontend

### 1. PDF Files - Display in Iframe

```jsx
function PDFViewer({ filename }) {
  const fileUrl = `http://localhost:8000/uploads/${filename}`;

  return (
    <div className="pdf-viewer">
      <iframe
        src={fileUrl}
        width="100%"
        height="600px"
        title="PDF Viewer"
        style={{ border: '1px solid #ccc' }}
      />
    </div>
  );
}

// Usage
<PDFViewer filename="complaint_45_20251031_171554_Case4.pdf" />
```

### 2. Image Files - Display as Image

```jsx
function ImageViewer({ filename, alt }) {
  const fileUrl = `http://localhost:8000/uploads/${filename}`;

  return (
    <div className="image-viewer">
      <img
        src={fileUrl}
        alt={alt}
        style={{ maxWidth: '100%', height: 'auto' }}
      />
    </div>
  );
}

// Usage
<ImageViewer
  filename="complaint_45_20251031_171554_evidence.jpg"
  alt="Evidence photo"
/>
```

### 3. Download Link

```jsx
function DownloadButton({ filename, originalFilename }) {
  const fileUrl = `http://localhost:8000/uploads/${filename}`;

  return (
    <a
      href={fileUrl}
      download={originalFilename}
      className="btn-download"
    >
      Download {originalFilename}
    </a>
  );
}

// Usage
<DownloadButton
  filename="complaint_45_20251031_171554_Case4.pdf"
  originalFilename="Case4.pdf"
/>
```

### 4. Open in New Tab

```jsx
function OpenInNewTabButton({ filename, originalFilename }) {
  const fileUrl = `http://localhost:8000/uploads/${filename}`;

  const handleOpen = () => {
    window.open(fileUrl, '_blank');
  };

  return (
    <button onClick={handleOpen} className="btn-view">
      View {originalFilename}
    </button>
  );
}
```

---

## Complete Document List Component

```jsx
import React, { useState, useEffect } from 'react';

function ComplaintDocuments({ complaintId }) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [previewDoc, setPreviewDoc] = useState(null);

  useEffect(() => {
    loadDocuments();
  }, [complaintId]);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8000/complaints/${complaintId}`);

      if (!response.ok) {
        throw new Error('Failed to load complaint');
      }

      const complaint = await response.json();
      setDocuments(complaint.documents || []);
    } catch (err) {
      console.error('Error loading documents:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getFileUrl = (filename) => {
    return `http://localhost:8000/uploads/${filename}`;
  };

  const getFileIcon = (fileType) => {
    if (fileType === 'application/pdf') return '📄';
    if (fileType.startsWith('image/')) return '🖼️';
    if (fileType.includes('word')) return '📝';
    if (fileType.includes('excel') || fileType.includes('spreadsheet')) return '📊';
    return '📎';
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  const handlePreview = (doc) => {
    if (doc.file_type === 'application/pdf' || doc.file_type.startsWith('image/')) {
      setPreviewDoc(doc);
    } else {
      // For non-previewable files, just download
      handleDownload(doc);
    }
  };

  const handleDownload = (doc) => {
    const url = getFileUrl(doc.filename);
    const link = document.createElement('a');
    link.href = url;
    link.download = doc.original_filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleOpenInNewTab = (doc) => {
    const url = getFileUrl(doc.filename);
    window.open(url, '_blank');
  };

  if (loading) {
    return <div className="loading">Loading documents...</div>;
  }

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  if (documents.length === 0) {
    return <div className="no-documents">No documents uploaded</div>;
  }

  return (
    <div className="complaint-documents">
      <h3>Uploaded Documents ({documents.length})</h3>

      <div className="documents-grid">
        {documents.map(doc => (
          <div key={doc.id} className="document-card">
            <div className="document-icon">
              {getFileIcon(doc.file_type)}
            </div>

            <div className="document-info">
              <h4 className="document-name" title={doc.original_filename}>
                {doc.original_filename}
              </h4>
              <p className="document-meta">
                <span>{formatFileSize(doc.file_size)}</span>
                <span className="separator">•</span>
                <span>{new Date(doc.uploaded_at).toLocaleDateString()}</span>
              </p>
            </div>

            <div className="document-actions">
              <button
                onClick={() => handlePreview(doc)}
                className="btn btn-preview"
                title="Preview"
              >
                👁️ Preview
              </button>

              <button
                onClick={() => handleOpenInNewTab(doc)}
                className="btn btn-open"
                title="Open in new tab"
              >
                🔗 Open
              </button>

              <button
                onClick={() => handleDownload(doc)}
                className="btn btn-download"
                title="Download"
              >
                ⬇️ Download
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Preview Modal */}
      {previewDoc && (
        <div className="modal-overlay" onClick={() => setPreviewDoc(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{previewDoc.original_filename}</h3>
              <button onClick={() => setPreviewDoc(null)} className="btn-close">
                ✕
              </button>
            </div>

            <div className="modal-body">
              {previewDoc.file_type === 'application/pdf' ? (
                <iframe
                  src={getFileUrl(previewDoc.filename)}
                  width="100%"
                  height="600px"
                  title="PDF Preview"
                />
              ) : previewDoc.file_type.startsWith('image/') ? (
                <img
                  src={getFileUrl(previewDoc.filename)}
                  alt={previewDoc.original_filename}
                  style={{ maxWidth: '100%', height: 'auto' }}
                />
              ) : null}
            </div>

            <div className="modal-footer">
              <button onClick={() => handleDownload(previewDoc)} className="btn btn-download">
                Download
              </button>
              <button onClick={() => handleOpenInNewTab(previewDoc)} className="btn btn-open">
                Open in New Tab
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ComplaintDocuments;
```

---

## CSS Styling

```css
/* Document Grid */
.complaint-documents {
  margin: 20px 0;
}

.documents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.document-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
  background: white;
  transition: box-shadow 0.2s;
}

.document-card:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.document-icon {
  font-size: 48px;
  text-align: center;
  margin-bottom: 10px;
}

.document-info {
  margin-bottom: 15px;
}

.document-name {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 8px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.document-meta {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.separator {
  margin: 0 8px;
}

.document-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.btn {
  padding: 8px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: background-color 0.2s;
}

.btn-preview {
  background: #007bff;
  color: white;
  flex: 1;
}

.btn-preview:hover {
  background: #0056b3;
}

.btn-open {
  background: #28a745;
  color: white;
  flex: 1;
}

.btn-open:hover {
  background: #218838;
}

.btn-download {
  background: #6c757d;
  color: white;
  flex: 1;
}

.btn-download:hover {
  background: #5a6268;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 1000px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #ddd;
}

.modal-header h3 {
  margin: 0;
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
}

.btn-close:hover {
  color: #000;
}

.modal-body {
  flex: 1;
  overflow: auto;
  padding: 20px;
}

.modal-footer {
  padding: 20px;
  border-top: 1px solid #ddd;
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.loading, .error, .no-documents {
  padding: 40px;
  text-align: center;
  color: #666;
}

.error {
  color: #dc3545;
  background: #f8d7da;
  border-radius: 4px;
}
```

---

## Usage in Complaint Details Page

```jsx
import ComplaintDocuments from './components/ComplaintDocuments';

function ComplaintDetailsPage({ complaintId }) {
  return (
    <div className="complaint-details">
      {/* Other complaint details */}

      <section className="documents-section">
        <ComplaintDocuments complaintId={complaintId} />
      </section>
    </div>
  );
}
```

---

## Quick Test

Test if files are accessible:

1. Open browser
2. Go to: `http://localhost:8000/uploads/`
3. You should see directory listing or an error (depends on FastAPI version)

Or directly access a file:
```
http://localhost:8000/uploads/complaint_45_20251031_171554_Case4.pdf
```

---

## Important Notes

### Security
⚠️ **This approach has NO access control**
- Anyone with the URL can access files
- Good for development/testing
- NOT recommended for production with sensitive data

### CORS
✅ Already configured in backend:
```python
allow_origins=["*"]
```
Files will be accessible from any frontend domain.

### File Not Found
If file URL returns 404:
- Check if file exists in `uploads/` folder
- Verify filename matches exactly (case-sensitive)
- Check backend console for errors

---

## Example URLs

Assuming backend is running on `http://localhost:8000`:

```
PDF File:
http://localhost:8000/uploads/complaint_45_20251031_171554_Case4.pdf

Image File:
http://localhost:8000/uploads/complaint_46_20251031_180000_evidence.jpg

Word Document:
http://localhost:8000/uploads/complaint_47_20251031_190000_report.docx
```

---

## Next Steps (For Production)

When ready for production, migrate to secure endpoints:
1. Remove static file mounting
2. Add authentication
3. Implement access control
4. Add audit logging

See `FILE_ACCESS_ARCHITECTURE.md` for details on secure implementation.
