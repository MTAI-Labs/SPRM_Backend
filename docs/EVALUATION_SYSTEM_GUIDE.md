# Complaint Evaluation System - Complete Guide

## 📋 Overview

The **Evaluation System** allows officers to review and confirm AI-generated data before finalizing a complaint for investigation. Officers fill out a two-part evaluation form:

1. **Basic Information** (AI pre-filled, officer reviews/edits)
2. **CRIS Details** (Only if classification = YES, officer fills manually)

---

## 🎯 Workflow

```
Complaint Submitted
        ↓
AI Processing (Auto)
  - Extract 5W1H
  - Classify (YES/NO)
  - Determine Sector
  - Suggest Akta
        ↓
Officer Reviews
  - Views AI-generated data
  - Clicks "Evaluate"
        ↓
Evaluation Form
  - Part 1: Basic Info (edit AI data)
  - Part 2: Classification (select dropdowns)
  - Part 3: CRIS Details (if YES)
        ↓
Officer Saves
  - Data stored in database
  - Complaint marked as "Evaluated"
        ↓
Ready for Investigation
```

---

## 🔧 Backend Setup

### **Step 1: Run Database Migration**

```sql
-- Run in pgAdmin or psql:
psql -U postgres -d sprm_db -f add_evaluation_fields_migration.sql
```

Or manually:
```sql
ALTER TABLE complaints
ADD COLUMN IF NOT EXISTS type_of_information VARCHAR(50),
ADD COLUMN IF NOT EXISTS source_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS sub_sector VARCHAR(200),
ADD COLUMN IF NOT EXISTS currency_type VARCHAR(10),
ADD COLUMN IF NOT EXISTS property_value NUMERIC(15, 2),
ADD COLUMN IF NOT EXISTS cris_details_others TEXT,
ADD COLUMN IF NOT EXISTS akta_sections TEXT[],
ADD COLUMN IF NOT EXISTS evaluated_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS evaluated_by VARCHAR(100);
```

### **Step 2: Test API Endpoints**

Visit: `http://localhost:8000/docs`

1. **GET `/config/evaluation-options`** - Get dropdown options
2. **GET `/complaints/{id}`** - Get complaint with AI data
3. **PUT `/complaints/{id}/evaluation`** - Save evaluation

---

## 📊 API Reference

### **1. Get Evaluation Options**

**Endpoint:** `GET /config/evaluation-options`

**Response:**
```json
{
  "main_sectors": [
    "Business and Industry / Perniagaan dan Industri",
    "Procurement / Perolehan",
    "...9 more"
  ],
  "sub_sectors": [
    "Perundangan Sistem Prosedur dan Peraturan",
    "Umum / Pelbagai",
    "...19 more"
  ],
  "type_of_information_options": [
    "Intelligence",
    "Complaint",
    "Report",
    "Whistleblower",
    "Anonymous Tip",
    "Media Report",
    "Others"
  ],
  "source_type_options": [
    "Public / Walk-in",
    "Government Agency",
    "Media",
    "Online Portal",
    "Hotline / Phone",
    "Letter / Mail",
    "Social Media",
    "Others"
  ],
  "currency_types": ["MYR", "USD", "SGD", "EUR", "GBP", "CNY", "Others"]
}
```

### **2. Get Complaint Data (with AI pre-fills)**

**Endpoint:** `GET /complaints/{complaint_id}`

**Response:**
```json
{
  "id": 42,
  "complaint_title": "Pegawai JKR meminta rasuah",

  // AI-generated 5W1H
  "w1h_what": "Pegawai JKR meminta RM5000 untuk meluluskan tender",
  "w1h_when": "Pada bulan September 2024",
  "w1h_where": "Di pejabat JKR Kuala Lumpur",
  "w1h_how": "Secara lisan semasa mesyuarat tender",
  "w1h_why": "Untuk kepentingan peribadi",
  "w1h_who": "Pegawai Tender JKR bernama Ahmad",

  // AI-generated classification
  "classification": "YES",
  "classification_confidence": 0.95,
  "sector": "Procurement / Perolehan",
  "akta": "Seksyen 161 - Mengambil suapan bersangkut perbuatan resmi",

  // AI-extracted data
  "extracted_data": {
    "entities": {
      "names": ["Ahmad"],
      "organizations": ["JKR"],
      "locations": ["Kuala Lumpur"],
      "amounts": ["RM5000"]
    }
  },

  // Evaluation fields (empty before evaluation)
  "type_of_information": null,
  "source_type": null,
  "sub_sector": null,
  "currency_type": null,
  "property_value": null,
  "akta_sections": null,
  "evaluated_at": null,
  "evaluated_by": null
}
```

### **3. Save Evaluation**

**Endpoint:** `PUT /complaints/{complaint_id}/evaluation`

**Request Body:**
```json
{
  // Part 1: Basic Information (edited from AI)
  "title": "Pegawai JKR meminta rasuah RM5000",
  "what_happened": "Pegawai JKR meminta RM5000 untuk meluluskan tender pembinaan jalan",
  "when_happened": "September 2024",
  "where_happened": "Pejabat JKR Kuala Lumpur",
  "how_happened": "Secara lisan semasa mesyuarat tender",
  "why_done": "Untuk kepentingan peribadi pegawai",

  // Part 2: Classification (required)
  "type_of_information": "Complaint",
  "source_type": "Public / Walk-in",
  "sector": "Procurement / Perolehan",
  "sub_sector": "Bekalan",

  // Part 3: CRIS Details (if classification = YES)
  "currency_type": "MYR",
  "property_value": 5000.00,
  "cris_details_others": "Pegawai juga meminta 10% daripada nilai kontrak",
  "organizations": ["JKR"],
  "akta_sections": [
    "Seksyen 161 - Mengambil suapan bersangkut perbuatan resmi",
    "Seksyen 165 - Menerima barang berharga"
  ],

  // Metadata
  "evaluated_by": "officer_fatimah"
}
```

**Response:**
```json
{
  "message": "Evaluation saved successfully",
  "complaint_id": 42,
  "evaluated_at": "2025-10-30T16:45:00",
  "evaluated_by": "officer_fatimah"
}
```

---

## 🎨 Frontend Implementation

### **Page 1: Complaint Detail (Read-Only View)**

```jsx
function ComplaintDetailPage({ complaintId }) {
  const [complaint, setComplaint] = useState(null);

  useEffect(() => {
    fetch(`/api/complaints/${complaintId}`)
      .then(res => res.json())
      .then(data => setComplaint(data));
  }, [complaintId]);

  return (
    <div>
      <h1>Complaint #{complaintId}</h1>

      {/* AI-Generated Data */}
      <Section title="AI Analysis">
        <InfoCard label="Classification" value={complaint.classification}
          badge={complaint.classification === 'YES' ? 'CRIS' : 'NFA'}
          badgeColor={complaint.classification === 'YES' ? 'red' : 'gray'} />

        <InfoCard label="Confidence" value={`${complaint.classification_confidence * 100}%`} />
        <InfoCard label="Sector" value={complaint.sector} />
        <InfoCard label="Akta (AI Suggested)" value={complaint.akta} />
      </Section>

      {/* 5W1H */}
      <Section title="5W1H Summary">
        <InfoCard label="What" value={complaint.w1h_what} />
        <InfoCard label="When" value={complaint.w1h_when} />
        <InfoCard label="Where" value={complaint.w1h_where} />
        <InfoCard label="How" value={complaint.w1h_how} />
        <InfoCard label="Why" value={complaint.w1h_why} />
        <InfoCard label="Who" value={complaint.w1h_who} />
      </Section>

      {/* Action Buttons */}
      {!complaint.evaluated_at && (
        <Button onClick={() => navigate(`/evaluate/${complaintId}`)}>
          Evaluate Complaint
        </Button>
      )}

      {complaint.evaluated_at && (
        <Alert variant="success">
          Evaluated by {complaint.evaluated_by} on {complaint.evaluated_at}
        </Alert>
      )}
    </div>
  );
}
```

### **Page 2: Evaluation Form**

```jsx
function ComplaintEvaluationForm({ complaintId }) {
  const [complaint, setComplaint] = useState(null);
  const [options, setOptions] = useState(null);
  const [formData, setFormData] = useState({});

  useEffect(() => {
    // Load complaint data
    fetch(`/api/complaints/${complaintId}`)
      .then(res => res.json())
      .then(data => {
        setComplaint(data);
        // Pre-fill form with AI data
        setFormData({
          title: data.complaint_title,
          what_happened: data.w1h_what,
          when_happened: data.w1h_when,
          where_happened: data.w1h_where,
          how_happened: data.w1h_how,
          why_done: data.w1h_why,
          sector: data.sector,
          akta_sections: [data.akta],
          // Empty fields
          type_of_information: '',
          source_type: '',
          sub_sector: '',
          currency_type: 'MYR',
          property_value: extractAmount(data.extracted_data),
          organizations: data.extracted_data?.entities?.organizations || []
        });
      });

    // Load dropdown options
    fetch('/api/config/evaluation-options')
      .then(res => res.json())
      .then(data => setOptions(data));
  }, [complaintId]);

  const handleSubmit = async () => {
    const response = await fetch(`/api/complaints/${complaintId}/evaluation`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...formData,
        evaluated_by: getCurrentOfficerUsername() // Get from auth context
      })
    });

    if (response.ok) {
      alert('Evaluation saved!');
      navigate(`/complaints/${complaintId}`);
    }
  };

  return (
    <Form>
      {/* Section 1: Basic Information */}
      <Section title="Basic Information" subtitle="AI Pre-filled - Review and Edit">
        <TextField
          label="Title"
          value={formData.title}
          onChange={(e) => setFormData({...formData, title: e.target.value})}
          helperText="✨ AI suggested"
        />
        <TextArea
          label="What happened"
          value={formData.what_happened}
          onChange={(e) => setFormData({...formData, what_happened: e.target.value})}
          rows={3}
          helperText="✨ From AI 5W1H"
        />
        <TextField label="When" value={formData.when_happened} onChange={...} />
        <TextField label="Where" value={formData.where_happened} onChange={...} />
        <TextArea label="How" value={formData.how_happened} onChange={...} />
        <TextArea label="Why" value={formData.why_done} onChange={...} />
      </Section>

      {/* Section 2: Classification */}
      <Section title="Classification" subtitle="Required Fields">
        <Select
          label="Type of Information *"
          value={formData.type_of_information}
          options={options?.type_of_information_options}
          onChange={(e) => setFormData({...formData, type_of_information: e.target.value})}
          required
        />
        <Select
          label="Source *"
          value={formData.source_type}
          options={options?.source_type_options}
          onChange={(e) => setFormData({...formData, source_type: e.target.value})}
          required
        />
        <Select
          label="Sector *"
          value={formData.sector}
          options={options?.main_sectors}
          onChange={(e) => setFormData({...formData, sector: e.target.value})}
          helperText={`✨ AI suggested: ${complaint.sector}`}
        />
        <Select
          label="Sub-Sector *"
          value={formData.sub_sector}
          options={options?.sub_sectors}
          onChange={(e) => setFormData({...formData, sub_sector: e.target.value})}
          required
        />
      </Section>

      {/* Section 3: CRIS Details (Only if YES) */}
      {complaint.classification === 'YES' && (
        <Section title="CRIS Details" variant="warning" subtitle="Required for CRIS cases">
          <Select
            label="Currency Type"
            value={formData.currency_type}
            options={options?.currency_types}
            onChange={(e) => setFormData({...formData, currency_type: e.target.value})}
          />
          <NumberField
            label="Property Value"
            value={formData.property_value}
            onChange={(e) => setFormData({...formData, property_value: e.target.value})}
            helperText={
              complaint.extracted_data?.entities?.amounts?.length > 0
                ? `✨ AI found: ${complaint.extracted_data.entities.amounts.join(', ')}`
                : null
            }
          />
          <TextArea
            label="Others"
            value={formData.cris_details_others}
            onChange={(e) => setFormData({...formData, cris_details_others: e.target.value})}
            rows={3}
            placeholder="Additional CRIS information..."
          />
          <MultiSelect
            label="Organizations"
            value={formData.organizations}
            onChange={(values) => setFormData({...formData, organizations: values})}
            options={complaint.extracted_data?.entities?.organizations || []}
            helperText="✨ From AI extracted data"
          />
          <MultiSelect
            label="Akta Sections *"
            value={formData.akta_sections}
            onChange={(values) => setFormData({...formData, akta_sections: values})}
            options={getAktaOptions()} // Fetch from /akta-sections endpoint
            searchable
            helperText={`✨ AI suggested: ${complaint.akta}`}
            required
          />
        </Section>
      )}

      {/* Action Buttons */}
      <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
        <Button variant="secondary" onClick={() => navigate(-1)}>
          Cancel
        </Button>
        <Button variant="primary" onClick={handleSubmit}>
          Save Evaluation
        </Button>
      </div>
    </Form>
  );
}
```

---

## 📝 Updating Options (Future)

### **Where to Edit:**

**File:** `src/subsector_mapping.py`

```python
# To add new Type of Information option:
TYPE_OF_INFORMATION_OPTIONS = [
    "Intelligence",
    "Complaint",
    "Report",
    "Whistleblower",
    "NEW_OPTION_HERE",  # ← Add here
]

# To add new Source Type:
SOURCE_TYPE_OPTIONS = [
    "Public / Walk-in",
    "Government Agency",
    "NEW_SOURCE_HERE",  # ← Add here
]

# To add new Sub-Sector:
SUB_SECTORS = [
    "Perundangan Sistem Prosedur dan Peraturan",
    "NEW_SUBSECTOR_HERE",  # ← Add here
]
```

**After editing:**
1. Restart backend server
2. Frontend automatically gets updated options from `/config/evaluation-options`

---

## ✅ Summary

### **AI Auto-Fills (90%):**
✅ Title
✅ 5W1H (What, When, Where, How, Why, Who)
✅ Sector
✅ Akta (single suggestion)
✅ Organizations (from extraction)
✅ Property values (if mentioned)

### **Officer Fills (10%):**
⚠️ Type of Information
⚠️ Source Type
⚠️ Sub-Sector
⚠️ Currency Type (if applicable)
⚠️ Additional CRIS details

### **Officer Reviews/Edits:**
✏️ All AI-generated fields (editable)
✏️ Can add multiple Akta sections
✏️ Can modify property values

---

## 🔍 Database Fields

| Field | Type | AI Fills | Officer Action | Required |
|-------|------|----------|----------------|----------|
| `complaint_title` | VARCHAR | ✅ Yes | Review/Edit | ✅ |
| `w1h_what` | TEXT | ✅ Yes | Review/Edit | ✅ |
| `w1h_when` | TEXT | ✅ Yes | Review/Edit | ✅ |
| `w1h_where` | TEXT | ✅ Yes | Review/Edit | ✅ |
| `w1h_how` | TEXT | ✅ Yes | Review/Edit | ✅ |
| `w1h_why` | TEXT | ✅ Yes | Review/Edit | ✅ |
| `sector` | VARCHAR | ✅ Yes | Review/Change | ✅ |
| `akta` | VARCHAR | ✅ Yes | For reference | - |
| `type_of_information` | VARCHAR | ❌ No | Manual select | ✅ |
| `source_type` | VARCHAR | ❌ No | Manual select | ✅ |
| `sub_sector` | VARCHAR | ❌ No | Manual select | ✅ |
| `currency_type` | VARCHAR | ❌ No | Manual select | If YES |
| `property_value` | NUMERIC | 🟡 Maybe | Verify/Edit | If YES |
| `cris_details_others` | TEXT | ❌ No | Manual input | - |
| `akta_sections` | TEXT[] | 🟡 Suggests 1 | Select multiple | ✅ |
| `evaluated_at` | TIMESTAMP | ❌ No | Auto (on save) | - |
| `evaluated_by` | VARCHAR | ❌ No | Auto (from auth) | ✅ |

---

**Last Updated:** 2025-10-30
**Version:** 1.0.0 (Evaluation System)
