# Letter Generation & History - Frontend Guide

## Overview

This guide covers:
1. Viewing letter history for a complaint
2. Generating new letters with editable templates
3. Viewing and printing generated letters

---

## API Endpoints

### 1. Get Available Letter Types

```http
GET /letters/types
```

**Response:**
```json
[
  {
    "type": "rujuk_jabatan",
    "name": "Surat Rujuk Jabatan",
    "description": "Surat merujuk aduan kepada jabatan berkaitan"
  }
]
```

### 2. Get Template Fields (Pre-filled)

```http
GET /letters/template/{letter_type}?complaint_id={id}
```

**Example:**
```http
GET /letters/template/rujuk_jabatan?complaint_id=45
```

**Response:**
```json
{
  "letter_type": "rujuk_jabatan",
  "complaint_id": 45,
  "fields": {
    "auto_filled": {
      "rujukan_kami": {
        "label": "Rujukan Kami",
        "value": "SPRM. BPRM. 600-2/3/2 Jld.5(45)",
        "readonly": false
      },
      "tarikh_surat": {
        "label": "Tarikh",
        "value": "31 October 2025",
        "readonly": false
      },
      "subject_line": {
        "label": "Tajuk Surat",
        "value": "ADUAN BERHUBUNG POTENTIALLY BRIBING",
        "readonly": false
      }
    },
    "recipient": {
      "recipient_title": {
        "label": "Gelaran Penerima",
        "value": "YBhg. Dato',",
        "options": ["YBhg. Dato',", "YBrs. Dato',", "Tuan", "Puan", "Encik"],
        "required": true
      },
      "recipient_name": {
        "label": "Nama Penerima",
        "value": "",
        "required": true
      }
    },
    "officer": {
      "officer_title": {
        "label": "Jawatan Pegawai",
        "value": "Pengarah",
        "required": true
      }
    }
  },
  "template_preview": "IBU PEJABAT\nSURUHANJAYA..."
}
```

### 3. Generate Letter

```http
POST /complaints/{complaint_id}/letters/generate
```

**Request Body:**
```json
{
  "letter_type": "rujuk_jabatan",
  "fields": {
    "rujukan_tuan": "",
    "rujukan_kami": "SPRM. BPRM. 600-2/3/2 Jld.5(45)",
    "tarikh_surat": "31 Oktober 2025",
    "recipient_title": "YBhg. Dato',",
    "recipient_name": "Datuk Bandar",
    "recipient_organization": "Majlis Bandaraya Johor Bahru",
    "recipient_address_line1": "Menara MBJB, No. 1",
    "recipient_address_line2": "Jalan Lingkaran Dalam",
    "recipient_address_line3": "Bukit Senyum, 80300 Johor Bahru",
    "recipient_state": "JOHOR",
    "salutation": "YBhg. Dato',",
    "subject_line": "ADUAN BERHUBUNG RASUAH",
    "officer_title": "Pengarah",
    "officer_department": "Bahagian Pengurusan Rekod & Maklumat",
    "cc_line1": "Setiausaha Kerajaan Negeri Johor",
    "cc_line2": "",
    "cc_line3": "",
    "cc_line4": ""
  },
  "generated_by": "officer_ahmad"
}
```

**Response:**
```json
{
  "letter_id": 1,
  "letter_content": "IBU PEJABAT\nSURUHANJAYA PENCEGAHAN RASUAH MALAYSIA...",
  "letter_type": "rujuk_jabatan",
  "generated_at": "2025-10-31T17:30:00",
  "complaint_id": 45
}
```

### 4. Get Letter History

```http
GET /complaints/{complaint_id}/letters
```

**Response:**
```json
{
  "complaint_id": 45,
  "total_letters": 2,
  "letters": [
    {
      "id": 2,
      "complaint_id": 45,
      "letter_type": "rujuk_jabatan",
      "letter_content": "IBU PEJABAT...",
      "generated_by": "officer_ahmad",
      "generated_at": "2025-10-31T17:30:00"
    },
    {
      "id": 1,
      "complaint_id": 45,
      "letter_type": "rujuk_jabatan",
      "letter_content": "IBU PEJABAT...",
      "generated_by": "officer_john",
      "generated_at": "2025-10-31T15:20:00"
    }
  ]
}
```

### 5. Get Specific Letter

```http
GET /letters/{letter_id}
```

**Response:**
```json
{
  "id": 1,
  "complaint_id": 45,
  "letter_type": "rujuk_jabatan",
  "letter_content": "IBU PEJABAT...",
  "generated_by": "officer_ahmad",
  "generated_at": "2025-10-31T17:30:00"
}
```

---

## Complete React Implementation

### 1. Letter History Component

```jsx
import React, { useState, useEffect } from 'react';

function LetterHistory({ complaintId }) {
  const [letters, setLetters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadLetterHistory();
  }, [complaintId]);

  const loadLetterHistory = async () => {
    try {
      setLoading(true);
      setError(null);

      // Validate complaint ID
      if (!complaintId || complaintId <= 0) {
        setError('Invalid complaint ID');
        return;
      }

      const response = await fetch(`http://localhost:8000/complaints/${complaintId}/letters`);

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      const data = await response.json();
      setLetters(data.letters || []);

    } catch (err) {
      console.error('Error loading letter history:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const viewLetter = (letterId) => {
    // Open letter in new window
    window.open(`/letters/${letterId}/view`, '_blank');
  };

  const printLetter = async (letterId) => {
    try {
      const response = await fetch(`http://localhost:8000/letters/${letterId}`);
      const data = await response.json();

      // Open print dialog with letter content
      const printWindow = window.open('', '_blank');
      printWindow.document.write(`
        <html>
          <head>
            <title>Letter ${letterId}</title>
            <style>
              body { font-family: Arial, sans-serif; margin: 20mm; }
              pre { white-space: pre-wrap; font-family: 'Courier New', monospace; }
            </style>
          </head>
          <body>
            <pre>${data.letter_content}</pre>
            <script>
              window.onload = () => window.print();
            </script>
          </body>
        </html>
      `);
      printWindow.document.close();

    } catch (err) {
      console.error('Error printing letter:', err);
      alert('Failed to print letter');
    }
  };

  if (loading) {
    return <div className="loading">Loading letter history...</div>;
  }

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  if (letters.length === 0) {
    return (
      <div className="no-letters">
        <p>No letters generated yet</p>
        <button onClick={() => window.location.href = `/complaints/${complaintId}/generate-letter`}>
          Generate First Letter
        </button>
      </div>
    );
  }

  return (
    <div className="letter-history">
      <h3>Letter History ({letters.length})</h3>

      <div className="letters-list">
        {letters.map(letter => (
          <div key={letter.id} className="letter-card">
            <div className="letter-header">
              <h4>{getLetterTypeName(letter.letter_type)}</h4>
              <span className="letter-id">#{letter.id}</span>
            </div>

            <div className="letter-info">
              <p><strong>Generated by:</strong> {letter.generated_by}</p>
              <p><strong>Generated at:</strong> {new Date(letter.generated_at).toLocaleString()}</p>
            </div>

            <div className="letter-actions">
              <button onClick={() => viewLetter(letter.id)} className="btn-view">
                View Letter
              </button>
              <button onClick={() => printLetter(letter.id)} className="btn-print">
                Print
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function getLetterTypeName(type) {
  const types = {
    'rujuk_jabatan': 'Surat Rujuk Jabatan',
    'notification': 'Surat Notifikasi',
    'summon': 'Surat Panggilan',
    'closure': 'Surat Penutupan',
    'nfa': 'Surat NFA'
  };
  return types[type] || type;
}

export default LetterHistory;
```

### 2. Letter Generation Form Component

```jsx
import React, { useState, useEffect } from 'react';

function LetterGenerationForm({ complaintId, onSuccess }) {
  const [letterTypes, setLetterTypes] = useState([]);
  const [selectedType, setSelectedType] = useState('rujuk_jabatan');
  const [templateFields, setTemplateFields] = useState(null);
  const [formData, setFormData] = useState({});
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadLetterTypes();
  }, []);

  useEffect(() => {
    if (selectedType) {
      loadTemplateFields(selectedType);
    }
  }, [selectedType, complaintId]);

  const loadLetterTypes = async () => {
    try {
      const response = await fetch('http://localhost:8000/letters/types');
      const data = await response.json();
      setLetterTypes(data);
    } catch (err) {
      console.error('Error loading letter types:', err);
    }
  };

  const loadTemplateFields = async (letterType) => {
    try {
      const url = `http://localhost:8000/letters/template/${letterType}?complaint_id=${complaintId}`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error('Failed to load template');
      }

      const data = await response.json();
      setTemplateFields(data.fields);

      // Initialize form data with default values
      const initialData = {};
      Object.keys(data.fields).forEach(section => {
        Object.keys(data.fields[section]).forEach(fieldName => {
          initialData[fieldName] = data.fields[section][fieldName].value || '';
        });
      });
      setFormData(initialData);

    } catch (err) {
      console.error('Error loading template fields:', err);
      setError(err.message);
    }
  };

  const handleFieldChange = (fieldName, value) => {
    setFormData(prev => ({
      ...prev,
      [fieldName]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setGenerating(true);
    setError(null);

    try {
      const response = await fetch(
        `http://localhost:8000/complaints/${complaintId}/letters/generate`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            letter_type: selectedType,
            fields: formData,
            generated_by: 'officer_current' // Replace with actual officer ID
          })
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate letter');
      }

      const result = await response.json();

      // Show success message
      alert('Letter generated successfully!');

      // Call success callback
      if (onSuccess) {
        onSuccess(result);
      }

      // Optionally redirect or show letter
      viewGeneratedLetter(result.letter_content);

    } catch (err) {
      console.error('Error generating letter:', err);
      setError(err.message);
    } finally {
      setGenerating(false);
    }
  };

  const viewGeneratedLetter = (letterContent) => {
    const previewWindow = window.open('', '_blank');
    previewWindow.document.write(`
      <html>
        <head>
          <title>Generated Letter</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 20mm; }
            pre { white-space: pre-wrap; font-family: 'Courier New', monospace; line-height: 1.6; }
            .actions { margin-bottom: 20px; }
            button { padding: 10px 20px; margin-right: 10px; }
          </style>
        </head>
        <body>
          <div class="actions">
            <button onclick="window.print()">Print</button>
            <button onclick="window.close()">Close</button>
          </div>
          <pre>${letterContent}</pre>
        </body>
      </html>
    `);
    previewWindow.document.close();
  };

  if (!templateFields) {
    return <div className="loading">Loading template...</div>;
  }

  return (
    <div className="letter-generation-form">
      <h3>Generate Letter</h3>

      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* Letter Type Selection */}
        <div className="form-group">
          <label>Letter Type</label>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            disabled={generating}
          >
            {letterTypes.map(type => (
              <option key={type.type} value={type.type}>
                {type.name}
              </option>
            ))}
          </select>
        </div>

        {/* Auto-filled Fields */}
        {templateFields.auto_filled && (
          <div className="form-section">
            <h4>Auto-filled Information</h4>
            {Object.keys(templateFields.auto_filled).map(fieldName => {
              const field = templateFields.auto_filled[fieldName];
              return (
                <div key={fieldName} className="form-group">
                  <label>{field.label}</label>
                  <input
                    type="text"
                    value={formData[fieldName] || ''}
                    onChange={(e) => handleFieldChange(fieldName, e.target.value)}
                    disabled={generating}
                  />
                </div>
              );
            })}
          </div>
        )}

        {/* Recipient Fields */}
        {templateFields.recipient && (
          <div className="form-section">
            <h4>Recipient Information</h4>
            {Object.keys(templateFields.recipient).map(fieldName => {
              const field = templateFields.recipient[fieldName];
              return (
                <div key={fieldName} className="form-group">
                  <label>
                    {field.label}
                    {field.required && <span className="required">*</span>}
                  </label>
                  {field.options ? (
                    <select
                      value={formData[fieldName] || ''}
                      onChange={(e) => handleFieldChange(fieldName, e.target.value)}
                      required={field.required}
                      disabled={generating}
                    >
                      <option value="">-- Select --</option>
                      {field.options.map(opt => (
                        <option key={opt} value={opt}>{opt}</option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type="text"
                      value={formData[fieldName] || ''}
                      onChange={(e) => handleFieldChange(fieldName, e.target.value)}
                      required={field.required}
                      disabled={generating}
                    />
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Officer Fields */}
        {templateFields.officer && (
          <div className="form-section">
            <h4>Officer Information</h4>
            {Object.keys(templateFields.officer).map(fieldName => {
              const field = templateFields.officer[fieldName];
              return (
                <div key={fieldName} className="form-group">
                  <label>
                    {field.label}
                    {field.required && <span className="required">*</span>}
                  </label>
                  <input
                    type="text"
                    value={formData[fieldName] || ''}
                    onChange={(e) => handleFieldChange(fieldName, e.target.value)}
                    required={field.required}
                    disabled={generating}
                  />
                </div>
              );
            })}
          </div>
        )}

        {/* Carbon Copy Fields */}
        {templateFields.carbon_copy && (
          <div className="form-section">
            <h4>Carbon Copy (Optional)</h4>
            {Object.keys(templateFields.carbon_copy).map(fieldName => {
              const field = templateFields.carbon_copy[fieldName];
              return (
                <div key={fieldName} className="form-group">
                  <label>{field.label}</label>
                  <input
                    type="text"
                    value={formData[fieldName] || ''}
                    onChange={(e) => handleFieldChange(fieldName, e.target.value)}
                    disabled={generating}
                  />
                </div>
              );
            })}
          </div>
        )}

        <div className="form-actions">
          <button type="submit" disabled={generating} className="btn-primary">
            {generating ? 'Generating...' : 'Generate Letter'}
          </button>
          <button type="button" onClick={() => window.history.back()} disabled={generating}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

export default LetterGenerationForm;
```

### 3. CSS Styling

```css
/* Letter History */
.letter-history {
  margin: 20px 0;
}

.letters-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.letter-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
  background: white;
}

.letter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.letter-header h4 {
  margin: 0;
  color: #333;
}

.letter-id {
  background: #f0f0f0;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
}

.letter-info {
  margin: 15px 0;
  font-size: 14px;
  color: #666;
}

.letter-info p {
  margin: 5px 0;
}

.letter-actions {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

.btn-view, .btn-print {
  flex: 1;
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-view {
  background: #007bff;
  color: white;
}

.btn-view:hover {
  background: #0056b3;
}

.btn-print {
  background: #28a745;
  color: white;
}

.btn-print:hover {
  background: #218838;
}

/* Letter Generation Form */
.letter-generation-form {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.form-section {
  margin: 30px 0;
  padding: 20px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #f9f9f9;
}

.form-section h4 {
  margin-top: 0;
  color: #333;
  border-bottom: 2px solid #007bff;
  padding-bottom: 10px;
}

.form-group {
  margin: 15px 0;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #555;
}

.required {
  color: red;
  margin-left: 4px;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #007bff;
}

.form-actions {
  margin-top: 30px;
  display: flex;
  gap: 15px;
}

.btn-primary {
  flex: 1;
  padding: 12px 24px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
}

.btn-primary:hover {
  background: #0056b3;
}

.btn-primary:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.alert-error {
  background: #f8d7da;
  color: #721c24;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

.no-letters {
  text-align: center;
  padding: 40px;
  background: #f5f5f5;
  border-radius: 8px;
}

.no-letters button {
  margin-top: 20px;
  padding: 12px 24px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
```

---

## Usage in Complaint Details Page

```jsx
import React from 'react';
import LetterHistory from './components/LetterHistory';
import LetterGenerationForm from './components/LetterGenerationForm';

function ComplaintDetailsPage({ complaintId }) {
  const [showGenerateForm, setShowGenerateForm] = useState(false);

  const handleLetterGenerated = (result) => {
    console.log('Letter generated:', result);
    setShowGenerateForm(false);
    // Refresh letter history
    window.location.reload();
  };

  return (
    <div className="complaint-details">
      {/* ... other complaint details ... */}

      <section className="letters-section">
        <div className="section-header">
          <h2>Letters</h2>
          <button onClick={() => setShowGenerateForm(!showGenerateForm)}>
            {showGenerateForm ? 'Cancel' : 'Generate New Letter'}
          </button>
        </div>

        {showGenerateForm ? (
          <LetterGenerationForm
            complaintId={complaintId}
            onSuccess={handleLetterGenerated}
          />
        ) : (
          <LetterHistory complaintId={complaintId} />
        )}
      </section>
    </div>
  );
}
```

---

## Troubleshooting

### Issue: Receiving "undefined" in generated letter

**Check:**
1. All required fields in form have values
2. Field names match exactly (case-sensitive)
3. Check browser console for errors
4. Verify API response contains `letter_content`

**Debug:**
```javascript
console.log('Form data being sent:', formData);
console.log('API response:', result);

// Check if letter_content exists
if (!result.letter_content) {
  console.error('letter_content is missing in response');
}
```

### Issue: Letter history not loading

**Check:**
1. Complaint ID is valid (> 0)
2. Backend endpoint returns 200 OK
3. Response contains `letters` array

---

## Summary

- Use `LetterHistory` component to display all generated letters
- Use `LetterGenerationForm` for creating new letters with editable fields
- Letters are automatically saved to database
- Print functionality opens letter in new window for printing
- All fields from template are editable by officer before generation
