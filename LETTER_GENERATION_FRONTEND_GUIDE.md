# Letter Generation - Frontend Implementation Guide

## ✅ System Ready with Actual SPRM Letter Template!

Based on the actual SPRM "Surat Rujuk Jabatan" template from rj-1.pdf and rj-2.pdf.

---

## 🎯 How It Works

1. **Officer opens complaint** details page
2. **Clicks "Generate Letter"** button
3. **Selects letter type** (e.g., "Surat Rujuk Jabatan")
4. **Form appears** with editable fields (some pre-filled from complaint)
5. **Officer fills/edits** recipient info, officer details, etc.
6. **Clicks "Generate"** → Full letter created
7. **Letter displays** → Ready to print/save

---

## 📡 API Endpoints

### **1. Get Available Letter Types**

```
GET /letters/types
```

**Response:**
```json
{
  "letter_types": [
    {
      "type": "rujuk_jabatan",
      "name": "Surat Rujuk Jabatan",
      "description": "Surat merujuk aduan kepada jabatan berkaitan untuk tindakan lanjut"
    }
  ]
}
```

### **2. Get Template with Editable Fields**

```
GET /letters/template/rujuk_jabatan?complaint_id=123
```

**Response:**
```json
{
  "letter_type": "rujuk_jabatan",
  "complaint_id": 123,
  "fields": {
    "auto_filled": {
      "rujukan_tuan": {"label": "Rujukan Tuan", "value": "", "readonly": false},
      "rujukan_kami": {"label": "Rujukan Kami", "value": "SPRM. BPRM. 600-2/3/2 Jld.5(123)", "readonly": false},
      "tarikh_surat": {"label": "Tarikh", "value": "30 Oktober 2025\n08 Rabiulakhir 1447", "readonly": false},
      "subject_line": {"label": "Tajuk Surat", "value": "ADUAN BERHUBUNG ...", "readonly": false}
    },
    "recipient": {
      "recipient_title": {
        "label": "Gelaran Penerima",
        "value": "YBhg. Dato',",
        "options": ["YBhg. Dato',", "YBrs. Dato',", "Tuan", "Puan", "Encik"],
        "required": true
      },
      "recipient_name": {"label": "Nama Penerima", "value": "", "required": true},
      "recipient_organization": {"label": "Organisasi", "value": "", "required": true},
      "recipient_address_line1": {"label": "Alamat Baris 1", "value": "", "required": true},
      "recipient_address_line2": {"label": "Alamat Baris 2", "value": "", "required": false},
      "recipient_address_line3": {"label": "Alamat Baris 3", "value": "", "required": false},
      "recipient_state": {"label": "Negeri", "value": "", "required": true},
      "salutation": {
        "label": "Kata Aluan",
        "value": "YBhg. Dato',",
        "options": ["YBhg. Dato',", "YBrs. Dato',", "Tuan", "Puan", "Encik"],
        "required": true
      }
    },
    "officer": {
      "officer_title": {"label": "Jawatan Pegawai", "value": "Pengarah", "required": true},
      "officer_department": {"label": "Bahagian", "value": "Bahagian Pengurusan Rekod & Maklumat", "required": true}
    },
    "carbon_copy": {
      "cc_line1": {"label": "SK Baris 1", "value": "Setiausaha Kerajaan", "required": false},
      "cc_line2": {"label": "SK Baris 2", "value": "", "required": false},
      "cc_line3": {"label": "SK Baris 3", "value": "", "required": false},
      "cc_line4": {"label": "SK Baris 4", "value": "", "required": false}
    }
  },
  "template_preview": "IBU PEJABAT\nSURUHANJAYA PENCEGAHAN RASUAH MALAYSIA\n..."
}
```

### **3. Generate Letter**

```
POST /complaints/123/letters/generate
```

**Request Body:**
```json
{
  "letter_type": "rujuk_jabatan",
  "fields": {
    "rujukan_tuan": "",
    "rujukan_kami": "SPRM. BPRM. 600-2/3/2 Jld.5(123)",
    "tarikh_surat": "30 Oktober 2025\n08 Rabiulakhir 1447",
    "recipient_title": "YBhg. Dato',",
    "recipient_name": "Datuk Bandar",
    "recipient_organization": "Majlis Bandaraya Johor Bahru",
    "recipient_address_line1": "Menara MBJB, No. 1, Jalan Lingkaran Dalam",
    "recipient_address_line2": "Bukit Senyum, 80300 Johor Bahru",
    "recipient_address_line3": "",
    "recipient_state": "JOHOR",
    "salutation": "YBhg. Dato',",
    "subject_line": "ADUAN KETIDAKPUASAN HATI PENGURUSAN PENYELENGGARAAN APARTMENT",
    "officer_title": "Pengarah",
    "officer_department": "Bahagian Pengurusan Rekod & Maklumat",
    "cc_line1": "Setiausaha Kerajaan",
    "cc_line2": "Setiausaha Kerajaan Negeri Johor",
    "cc_line3": "Ketua Unit Integriti",
    "cc_line4": "Setiausaha Kerajaan Negeri Johor"
  },
  "generated_by": "officer_ahmad"
}
```

**Response:**
```json
{
  "letter_id": 45,
  "letter_content": "IBU PEJABAT\nSURUHANJAYA PENCEGAHAN RASUAH MALAYSIA\n...",
  "letter_type": "rujuk_jabatan",
  "generated_at": "2025-10-31T12:30:00",
  "complaint_id": 123
}
```

---

## 💻 Complete React Implementation

```javascript
import React, { useState, useEffect } from 'react';

function LetterGeneratorDialog({ complaintId, onClose }) {
  const [letterTypes, setLetterTypes] = useState([]);
  const [selectedType, setSelectedType] = useState('');
  const [fields, setFields] = useState(null);
  const [formData, setFormData] = useState({});
  const [generatedLetter, setGeneratedLetter] = useState(null);
  const [loading, setLoading] = useState(false);

  // Step 1: Load available letter types
  useEffect(() => {
    fetch('http://localhost:8000/letters/types')
      .then(r => r.json())
      .then(data => setLetterTypes(data.letter_types));
  }, []);

  // Step 2: Load template fields when type selected
  const loadTemplate = async (letterType) => {
    setSelectedType(letterType);
    setLoading(true);

    const response = await fetch(
      `http://localhost:8000/letters/template/${letterType}?complaint_id=${complaintId}`
    );
    const data = await response.json();

    setFields(data.fields);

    // Pre-fill form data with default values
    const initialData = {};
    Object.entries(data.fields).forEach(([section, sectionFields]) => {
      Object.entries(sectionFields).forEach(([key, field]) => {
        initialData[key] = field.value || '';
      });
    });
    setFormData(initialData);
    setLoading(false);
  };

  // Step 3: Generate letter
  const generateLetter = async () => {
    setLoading(true);

    const response = await fetch(
      `http://localhost:8000/complaints/${complaintId}/letters/generate`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          letter_type: selectedType,
          fields: formData,
          generated_by: 'officer_ahmad' // Get from logged-in user
        })
      }
    );

    const result = await response.json();
    setGeneratedLetter(result);
    setLoading(false);
  };

  // Handle field change
  const handleFieldChange = (key, value) => {
    setFormData({ ...formData, [key]: value });
  };

  return (
    <div className="dialog-overlay">
      <div className="dialog-container">
        <h2>Generate Letter</h2>

        {/* Step 1: Select Letter Type */}
        {!selectedType && (
          <div>
            <h3>Select Letter Type</h3>
            <div className="letter-types">
              {letterTypes.map(type => (
                <button
                  key={type.type}
                  onClick={() => loadTemplate(type.type)}
                  className="letter-type-btn"
                >
                  <strong>{type.name}</strong>
                  <p>{type.description}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 2: Fill Form */}
        {selectedType && !generatedLetter && (
          <div className="letter-form">
            <button onClick={() => setSelectedType('')} className="back-btn">
              ← Back
            </button>

            <h3>{letterTypes.find(t => t.type === selectedType)?.name}</h3>

            {loading ? (
              <p>Loading form...</p>
            ) : (
              <>
                {/* Auto-filled Section */}
                {fields?.auto_filled && (
                  <div className="form-section">
                    <h4>Auto-filled Fields</h4>
                    {Object.entries(fields.auto_filled).map(([key, field]) => (
                      <div key={key} className="form-field">
                        <label>{field.label}</label>
                        <textarea
                          value={formData[key] || ''}
                          onChange={e => handleFieldChange(key, e.target.value)}
                          rows={2}
                        />
                      </div>
                    ))}
                  </div>
                )}

                {/* Recipient Section */}
                {fields?.recipient && (
                  <div className="form-section">
                    <h4>Recipient Information *</h4>
                    {Object.entries(fields.recipient).map(([key, field]) => (
                      <div key={key} className="form-field">
                        <label>
                          {field.label} {field.required && '*'}
                        </label>
                        {field.options ? (
                          <select
                            value={formData[key] || ''}
                            onChange={e => handleFieldChange(key, e.target.value)}
                            required={field.required}
                          >
                            <option value="">-- Select --</option>
                            {field.options.map(opt => (
                              <option key={opt} value={opt}>{opt}</option>
                            ))}
                          </select>
                        ) : (
                          <input
                            type="text"
                            value={formData[key] || ''}
                            onChange={e => handleFieldChange(key, e.target.value)}
                            required={field.required}
                          />
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Officer Section */}
                {fields?.officer && (
                  <div className="form-section">
                    <h4>Officer Information</h4>
                    {Object.entries(fields.officer).map(([key, field]) => (
                      <div key={key} className="form-field">
                        <label>{field.label}</label>
                        <input
                          type="text"
                          value={formData[key] || ''}
                          onChange={e => handleFieldChange(key, e.target.value)}
                        />
                      </div>
                    ))}
                  </div>
                )}

                {/* Carbon Copy Section */}
                {fields?.carbon_copy && (
                  <div className="form-section">
                    <h4>Carbon Copy (SK)</h4>
                    {Object.entries(fields.carbon_copy).map(([key, field]) => (
                      <div key={key} className="form-field">
                        <label>{field.label}</label>
                        <input
                          type="text"
                          value={formData[key] || ''}
                          onChange={e => handleFieldChange(key, e.target.value)}
                        />
                      </div>
                    ))}
                  </div>
                )}

                <button onClick={generateLetter} className="btn-primary">
                  Generate Letter
                </button>
              </>
            )}
          </div>
        )}

        {/* Step 3: Display Generated Letter */}
        {generatedLetter && (
          <div className="letter-preview">
            <h3>Generated Letter</h3>

            <div className="letter-content">
              <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                {generatedLetter.letter_content}
              </pre>
            </div>

            <div className="letter-actions">
              <button onClick={() => window.print()} className="btn-primary">
                🖨️ Print
              </button>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(generatedLetter.letter_content);
                  alert('Letter copied to clipboard!');
                }}
                className="btn-secondary"
              >
                📋 Copy
              </button>
              <button onClick={() => setGeneratedLetter(null)} className="btn-secondary">
                ← Edit
              </button>
              <button onClick={onClose} className="btn-secondary">
                Close
              </button>
            </div>

            <p className="text-muted">
              Letter ID: {generatedLetter.letter_id} |
              Generated: {new Date(generatedLetter.generated_at).toLocaleString()}
            </p>
          </div>
        )}

        {!generatedLetter && (
          <button onClick={onClose} className="btn-close">
            Cancel
          </button>
        )}
      </div>
    </div>
  );
}

export default LetterGeneratorDialog;
```

---

## 🎨 CSS Styling

```css
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog-container {
  background: white;
  padding: 24px;
  border-radius: 8px;
  max-width: 900px;
  max-height: 90vh;
  overflow-y: auto;
  width: 100%;
}

.letter-types {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.letter-type-btn {
  padding: 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  text-align: left;
  transition: all 0.2s;
}

.letter-type-btn:hover {
  border-color: #2196f3;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.letter-type-btn strong {
  display: block;
  font-size: 16px;
  margin-bottom: 8px;
  color: #333;
}

.letter-type-btn p {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.form-section {
  margin: 24px 0;
  padding: 16px;
  background: #f9f9f9;
  border-radius: 8px;
}

.form-section h4 {
  margin-top: 0;
  color: #2196f3;
}

.form-field {
  margin-bottom: 16px;
}

.form-field label {
  display: block;
  font-weight: 500;
  margin-bottom: 4px;
  color: #333;
}

.form-field input,
.form-field select,
.form-field textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-field input:focus,
.form-field select:focus,
.form-field textarea:focus {
  outline: none;
  border-color: #2196f3;
}

.letter-content {
  background: #f5f5f5;
  padding: 24px;
  border-radius: 8px;
  margin: 16px 0;
  max-height: 500px;
  overflow-y: auto;
}

.letter-content pre {
  margin: 0;
  line-height: 1.6;
}

.letter-actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}

.btn-primary {
  background: #2196f3;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.btn-primary:hover {
  background: #1976d2;
}

.btn-secondary {
  background: #fff;
  color: #333;
  border: 1px solid #ddd;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
}

.btn-secondary:hover {
  background: #f5f5f5;
}

.back-btn {
  background: none;
  border: none;
  color: #2196f3;
  cursor: pointer;
  padding: 8px 0;
  margin-bottom: 16px;
}
```

---

## 📱 Usage in Complaint Details Page

```javascript
function ComplaintDetailsPage({ complaintId }) {
  const [showLetterDialog, setShowLetterDialog] = useState(false);

  return (
    <div>
      {/* Complaint details */}
      <h1>Complaint #{complaintId}</h1>
      {/* ... other details ... */}

      {/* Generate Letter Button */}
      <button
        onClick={() => setShowLetterDialog(true)}
        className="btn-primary"
      >
        📝 Generate Letter
      </button>

      {/* Letter Generator Dialog */}
      {showLetterDialog && (
        <LetterGeneratorDialog
          complaintId={complaintId}
          onClose={() => setShowLetterDialog(false)}
        />
      )}
    </div>
  );
}
```

---

## ✅ What Your Frontend Gets

1. **Pre-filled form** with complaint data
2. **Editable fields** for recipient, officer, carbon copy
3. **Dropdown options** where applicable (gelaran, etc.)
4. **Live generation** with all fields filled
5. **Print/Copy/Save** functionality
6. **Letter history** tracking

---

## 🚀 Setup Steps

1. **Run migration:**
   ```bash
   python run_letters_migration.py
   ```

2. **Test API:**
   ```bash
   curl http://localhost:8000/letters/types
   ```

3. **Implement frontend** using the React component above

4. **Done!** Officers can generate letters instantly

---

**Ready to use!** 🎉