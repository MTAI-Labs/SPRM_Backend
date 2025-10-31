# Frontend Implementation Guide - Related Cases Feature

## Overview

This guide explains how to implement the **Related Cases** feature in your frontend application. This feature allows officers to see if a new complaint is similar to previously closed cases, helping them identify recurring patterns and make informed decisions.

---

## 🎯 User Flow

### Scenario: New Complaint Similar to Closed Case

1. **Citizen submits complaint** → Backend processes it
2. **Backend checks for similar complaints**:
   - First searches **open cases** (adds to existing if similar)
   - Then searches **closed cases** (stores as reference)
3. **Officer opens case dashboard** → Sees warning if related cases exist
4. **Officer clicks "View Related Cases"** → Reviews closed case history
5. **Officer decides**: Continue with new case OR reopen old case

---

## 📊 API Integration

### 1. Get Case Details (includes related_cases field)

**Endpoint:** `GET /cases/{case_id}`

**Response:**
```json
{
  "id": 42,
  "case_number": "CASE-2025-0042",
  "case_title": "Kes: Tender JKR",
  "status": "open",
  "related_cases": [
    {
      "case_id": 15,
      "case_number": "CASE-2024-0015",
      "case_title": "Kes: Rasuah Tender",
      "similarity_score": 0.87,
      "status": "closed",
      "closed_at": "2024-12-15T10:30:00",
      "detected_at": "2025-10-30T16:45:00"
    }
  ],
  "complaints": [ /* array of complaints */ ]
}
```

### 2. Get Related Cases (dedicated endpoint)

**Endpoint:** `GET /cases/{case_id}/related`

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
    }
  ]
}
```

---

## 🎨 UI Components to Implement

### 1. Warning Banner (Case Detail Page)

Display when a case has related closed cases:

```jsx
// Example: React Component
function RelatedCasesWarning({ relatedCases }) {
  if (!relatedCases || relatedCases.length === 0) return null;

  return (
    <div className="alert alert-warning" style={{
      backgroundColor: '#fff3cd',
      border: '1px solid #ffc107',
      borderRadius: '8px',
      padding: '16px',
      marginBottom: '20px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span style={{ fontSize: '24px' }}>⚠️</span>
        <div>
          <h4 style={{ margin: 0, marginBottom: '8px' }}>
            Similar Closed Cases Detected
          </h4>
          <p style={{ margin: 0 }}>
            This case appears similar to {relatedCases.length} previously closed case(s).
            Review the related cases to check for recurring patterns or repeat offenders.
          </p>
          <button
            className="btn btn-link"
            style={{ padding: '8px 0', marginTop: '8px' }}
            onClick={() => openRelatedCasesModal(relatedCases)}
          >
            View Related Cases →
          </button>
        </div>
      </div>
    </div>
  );
}
```

### 2. Related Cases List (Modal/Sidebar)

Display list of related closed cases with details:

```jsx
function RelatedCasesList({ caseId }) {
  const [relatedCases, setRelatedCases] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`http://localhost:8000/cases/${caseId}/related`)
      .then(res => res.json())
      .then(data => {
        setRelatedCases(data.related_cases || []);
        setLoading(false);
      });
  }, [caseId]);

  if (loading) return <Spinner />;
  if (relatedCases.length === 0) return <p>No related cases found.</p>;

  return (
    <div className="related-cases-list">
      <h3>Related Closed Cases</h3>
      {relatedCases.map(rc => (
        <div key={rc.case_id} className="related-case-card" style={{
          border: '1px solid #ddd',
          borderRadius: '8px',
          padding: '16px',
          marginBottom: '16px',
          backgroundColor: '#f8f9fa'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
            <div>
              <h4 style={{ margin: 0, marginBottom: '4px' }}>
                {rc.case_number}
              </h4>
              <p style={{ margin: 0, color: '#666', marginBottom: '8px' }}>
                {rc.case_title}
              </p>
              <div style={{ fontSize: '14px', color: '#666' }}>
                <p style={{ margin: '4px 0' }}>
                  <strong>Status:</strong> <span className="badge badge-secondary">Closed</span>
                </p>
                <p style={{ margin: '4px 0' }}>
                  <strong>Closed:</strong> {new Date(rc.closed_at).toLocaleDateString('en-MY')}
                </p>
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{
                fontSize: '24px',
                fontWeight: 'bold',
                color: rc.similarity_score >= 0.85 ? '#d32f2f' : '#ff9800'
              }}>
                {Math.round(rc.similarity_score * 100)}%
              </div>
              <div style={{ fontSize: '12px', color: '#666' }}>Similarity</div>
            </div>
          </div>
          <div style={{ marginTop: '12px' }}>
            <button
              className="btn btn-sm btn-primary"
              onClick={() => window.open(`/cases/${rc.case_id}`, '_blank')}
            >
              View Case Details
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
```

### 3. Case Dashboard Indicator

Add visual indicator on case cards in dashboard:

```jsx
function CaseCard({ caseData }) {
  const hasRelatedCases = caseData.related_cases && caseData.related_cases.length > 0;

  return (
    <div className="case-card">
      <div className="case-header">
        <h3>{caseData.case_number}</h3>
        {hasRelatedCases && (
          <span className="badge badge-warning" style={{
            backgroundColor: '#ffc107',
            color: '#000',
            padding: '4px 8px',
            borderRadius: '4px',
            fontSize: '12px',
            marginLeft: '8px'
          }}>
            ⚠️ Similar to {caseData.related_cases.length} closed case(s)
          </span>
        )}
      </div>
      <p>{caseData.case_title}</p>
      {/* ... rest of card ... */}
    </div>
  );
}
```

---

## 🔧 Implementation Checklist

### Backend Setup (Already Done ✅)
- [x] Database migration added (`add_related_cases_migration.sql`)
- [x] API endpoint created (`GET /cases/{case_id}/related`)
- [x] Auto-grouping logic updated to check closed cases
- [x] Documentation updated

### Frontend Tasks (Your Work 📝)

#### 1. **Case Detail Page**
- [ ] Fetch case data including `related_cases` field
- [ ] Display warning banner if `related_cases` array is not empty
- [ ] Add "View Related Cases" button/link
- [ ] Show similarity percentage with color coding:
  - 🔴 Red (≥85%): Very high similarity
  - 🟠 Orange (70-84%): High similarity
  - 🟡 Yellow (<70%): Moderate similarity

#### 2. **Related Cases Modal/Section**
- [ ] Create modal or sidebar to display related cases
- [ ] Show case number, title, closed date
- [ ] Display similarity score prominently
- [ ] Add "View Case" button to open closed case details in new tab
- [ ] Consider adding "Reopen Case" option for officers

#### 3. **Case Dashboard/List**
- [ ] Add visual indicator (badge/icon) for cases with related closed cases
- [ ] Show count: "⚠️ Similar to 2 closed cases"
- [ ] Consider adding filter: "Show only cases with related history"

#### 4. **Optional Enhancements**
- [ ] Add timeline view showing when similar cases occurred
- [ ] Show common entities (names, locations) across related cases
- [ ] Add analytics: "This is the 3rd complaint about this entity"
- [ ] Email notification to supervisor when high-similarity case detected

---

## 💡 UI/UX Recommendations

### Visual Design

**1. Color Coding for Similarity:**
- **85-100%**: Red - "Very Similar" - Requires immediate attention
- **70-84%**: Orange - "Similar" - Review recommended
- **60-69%**: Yellow - "Possibly Related" - Optional review

**2. Placement:**
- Show warning banner at **top of case detail page** (hard to miss)
- Add small badge in **case list/dashboard** (awareness)
- Create dedicated **"Related Cases" tab** in case details (detailed view)

**3. Iconography:**
- ⚠️ Warning triangle for alert banner
- 🔗 Link icon for "related" badge
- 📊 Graph icon for similarity percentage
- 🔍 Magnifying glass for "View Details"

### User Actions

**1. Primary Actions:**
- "View Related Cases" → Opens modal/panel with details
- "View Case [CASE-2024-0015]" → Opens closed case in new tab
- "Dismiss" → Hide warning (but keep in history)

**2. Secondary Actions:**
- "Compare Cases" → Side-by-side comparison
- "Reopen Old Case" → Reopen closed case instead of continuing with new
- "Mark as Different" → AI learns this isn't actually related

---

## 📱 Example Layouts

### Option 1: Top Banner (Recommended)
```
┌─────────────────────────────────────────────────────┐
│ ⚠️  Similar Closed Cases Detected                   │
│ This case appears similar to 2 previously closed    │
│ cases. [View Related Cases →]                       │
└─────────────────────────────────────────────────────┘

Case: CASE-2025-0042
Title: Kes Tender JKR
Status: Open
...
```

### Option 2: Sidebar Panel
```
┌───────────────┬─────────────────────────────────┐
│               │ Case: CASE-2025-0042            │
│               │ Title: Kes Tender JKR           │
│               │ Status: Open                     │
│  Related      │                                  │
│  Cases (2)    │ Details:                         │
│               │ ...                              │
│  CASE-2024-   │                                  │
│  0015 (87%)   │                                  │
│               │                                  │
│  CASE-2024-   │                                  │
│  0023 (79%)   │                                  │
└───────────────┴─────────────────────────────────┘
```

### Option 3: Tabbed Interface
```
┌─ Details ─ Timeline ─ Related Cases (2) ─ Documents ──┐
│                                                         │
│  ⚠️ 2 Similar Closed Cases Found                       │
│                                                         │
│  ┌─────────────────────────────────────────┐          │
│  │ CASE-2024-0015 | Kes: Rasuah Tender     │          │
│  │ Similarity: 87% | Closed: Dec 15, 2024  │          │
│  │ [View Details]                           │          │
│  └─────────────────────────────────────────┘          │
│  ...                                                    │
└────────────────────────────────────────────────────────┘
```

---

## 🧪 Testing Scenarios

### Test Case 1: New Case with Related Closed Case
1. Submit complaint about "Rasuah tender JKR"
2. Backend creates new case (no open cases match)
3. Backend finds closed case "CASE-2024-0015" is 87% similar
4. Frontend displays warning banner
5. Officer clicks "View Related Cases"
6. Modal shows CASE-2024-0015 details
7. Officer reviews and decides to continue with new case

### Test Case 2: Case with No Related Cases
1. Submit unique complaint
2. Backend creates new case
3. No closed cases match
4. Frontend shows normal case view (no warning)

### Test Case 3: High Similarity (85%+)
1. Submit nearly identical complaint to closed case
2. Warning banner shows with red indicator
3. Officer reviews closed case
4. Officer may choose to reopen old case

---

## 🚀 Quick Start (React Example)

```jsx
// 1. Fetch case with related cases
const [caseData, setCaseData] = useState(null);

useEffect(() => {
  fetch(`http://localhost:8000/cases/${caseId}`)
    .then(res => res.json())
    .then(data => setCaseData(data));
}, [caseId]);

// 2. Check if related cases exist
const hasRelatedCases = caseData?.related_cases?.length > 0;

// 3. Render warning banner
return (
  <div className="case-detail-page">
    {hasRelatedCases && (
      <RelatedCasesWarning relatedCases={caseData.related_cases} />
    )}

    <h1>{caseData.case_number}: {caseData.case_title}</h1>
    {/* ... rest of case details ... */}
  </div>
);
```

---

## ❓ FAQ

**Q: When does the system check for related cases?**
A: Automatically when a new complaint is processed and grouped into a case.

**Q: Can officers manually add related cases?**
A: Not currently implemented, but could be added as a feature.

**Q: What if officer disagrees with the similarity?**
A: They can ignore the warning and proceed normally. The related cases are informational only.

**Q: Can we search for related cases after case creation?**
A: Yes! Use `GET /cases/{case_id}/related` anytime to check for related cases.

**Q: What happens if a related case is reopened?**
A: The status changes to "open" but it remains in the `related_cases` array of the new case for historical reference.

---

## 📞 Support

For backend issues or questions, check:
- [Backend README](Backend_README.md) - Full API documentation
- FastAPI Docs: `http://localhost:8000/docs` - Interactive API testing
- Database Schema: See "Cases Table" section in Backend README

---

**Last Updated:** 2025-10-30
**Backend Version:** 2.0.0 (with Related Cases feature)
