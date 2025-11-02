# Document Access Guide for Frontend

## Problem
When clicking "preview uploaded documents" in complaint details, you may see errors like "refused to connect" because the document URL is incorrect.

## Solution: Use the `download_url` Field

### ✅ **Recommended Approach**

When you fetch complaint details from `GET /complaints/{id}`, each document in the `documents` array now includes a `download_url` field:

```json
{
  "id": 123,
  "documents": [
    {
      "id": 456,
      "original_filename": "evidence.pdf",
      "file_type": "application/pdf",
      "file_size": 12345,
      "download_url": "/documents/456/download"  // ✅ Use this!
    }
  ]
}
```

### Frontend Implementation

**React Example:**
```jsx
function DocumentPreview({ document }) {
  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
  const fileUrl = `${backendUrl}${document.download_url}`;

  return (
    <a href={fileUrl} target="_blank" rel="noopener noreferrer">
      Preview {document.original_filename}
    </a>
  );
}
```

**Image Preview:**
```jsx
{document.file_type.startsWith('image/') && (
  <img
    src={`${backendUrl}${document.download_url}`}
    alt={document.original_filename}
  />
)}
```

**PDF Viewer:**
```jsx
{document.file_type === 'application/pdf' && (
  <iframe
    src={`${backendUrl}${document.download_url}`}
    width="100%"
    height="600px"
  />
)}
```

## ❌ **Don't Use These Approaches**

### Wrong #1: Using `file_path` directly
```jsx
// ❌ WRONG - file_path is server-side only
const wrongUrl = `${backendUrl}/${document.file_path}`;
// Results in: http://localhost:8000/uploads/complaint_1_file.pdf
// This might work but is not reliable
```

### Wrong #2: Hardcoded localhost
```jsx
// ❌ WRONG - hardcoded URL won't work in production
const wrongUrl = `http://localhost:8000/documents/${document.id}/download`;
```

## Environment Configuration

Create a `.env` file in your frontend project:

```env
# Development
REACT_APP_BACKEND_URL=http://localhost:8000

# Production (update when deploying)
# REACT_APP_BACKEND_URL=https://api.sprm.gov.my
```

## API Reference

### Get Complaint Details
**Endpoint:** `GET /complaints/{complaint_id}`

**Response:**
```json
{
  "id": 1,
  "complaint_title": "Corruption Case",
  "documents": [
    {
      "id": 1,
      "filename": "complaint_1_20251102_123456_evidence.pdf",
      "original_filename": "evidence.pdf",
      "file_path": "uploads/complaint_1_20251102_123456_evidence.pdf",
      "file_size": 12345,
      "file_type": "application/pdf",
      "uploaded_at": "2025-11-02T12:34:56",
      "download_url": "/documents/1/download"  // ✅ Use this
    }
  ]
}
```

### Download Document
**Endpoint:** `GET /documents/{document_id}/download`

**Description:** Returns the actual file with proper headers for download/preview

**Response:** File stream with appropriate content-type

## Troubleshooting

### Error: "refused to connect"
**Cause:** Wrong backend URL or CORS issue

**Solution:**
1. Check that backend is running: `curl http://localhost:8000/health`
2. Verify CORS is enabled (already configured in backend)
3. Check your `REACT_APP_BACKEND_URL` environment variable

### Error: 404 Not Found
**Cause:** Document doesn't exist or wrong ID

**Solution:**
1. Check the `download_url` value in the API response
2. Verify the document exists: `GET /documents/{id}/download`
3. Check browser console for the actual URL being requested

### PDF/Image not displaying
**Cause:** Wrong MIME type or CORS headers

**Solution:**
1. Backend already sets correct `Content-Type` headers
2. Use `target="_blank"` for PDFs to open in new tab
3. For inline display, ensure browser supports the file type

## Summary

✅ **Always use:** `document.download_url` from the API response
✅ **Configure:** Backend URL via environment variables
✅ **Construct:** `${backendUrl}${document.download_url}`

❌ **Never use:** Hardcoded URLs or direct file paths
