# SPRM Analytics System Guide

## Overview

The new analytics system provides **meaningful pattern detection** and **actionable insights** for SPRM officers, going beyond basic counts to show real corruption patterns.

### What Officers Get

Instead of useless stats like "100 complaints total", officers now see:
- ✅ **"3 complaints about tender bribery involving gold"**
- ✅ **"4 complaints about gold-related corruption in schools"**
- ✅ **"2 complaints about cash payments to police officers"**
- ✅ **AI-generated insights in Bahasa Malaysia**

---

## Analytics Endpoints

### 1. **Dashboard (Comprehensive View)**

```
GET /analytics/dashboard?days=30
```

**Returns everything in one call:**
- Entity analytics (names, orgs, locations)
- Pattern detection (2-word and 3-word combinations)
- Trending keywords
- Case statistics
- AI-generated insights in Bahasa Malaysia

**Example Response:**
```json
{
  "period": {
    "days": 30,
    "from": "2025-09-30T10:00:00",
    "to": "2025-10-30T10:00:00"
  },
  "entity_analytics": {
    "top_names": [
      {"name": "Ahmad", "count": 5},
      {"name": "Siti", "count": 3}
    ],
    "top_organizations": [
      {"org": "Jabatan Pendidikan", "count": 8},
      {"org": "JKR", "count": 6}
    ],
    "top_locations": [
      {"location": "Kuala Lumpur", "count": 12},
      {"location": "Selangor", "count": 9}
    ],
    "sectors": [
      {"sector": "Pendidikan", "count": 15},
      {"sector": "Pembinaan", "count": 10}
    ]
  },
  "patterns": {
    "two_keyword_patterns": [
      {
        "pattern": "tender + gold",
        "count": 3,
        "example": "3 complaints involve both tender + gold"
      },
      {
        "pattern": "school + bribery",
        "count": 4,
        "example": "4 complaints involve both school + bribery"
      }
    ],
    "three_keyword_patterns": [
      {
        "pattern": "construction + contract + cash",
        "count": 2,
        "example": "2 complaints involve construction + contract + cash"
      }
    ]
  },
  "ai_insights": "Berdasarkan analisis 30 hari kebelakangan, terdapat peningkatan aduan melibatkan tender dan emas (3 kes). Sektor pendidikan mencatatkan bilangan aduan tertinggi (15 kes), terutamanya melibatkan rasuah di peringkat sekolah. Jabatan Pendidikan dan JKR adalah organisasi yang paling kerap disebut. Disyorkan untuk fokus siasatan kepada kes-kes tender di sektor pendidikan dan pembinaan."
}
```

---

### 2. **Entity Analytics**

```
GET /analytics/entities?days=30
```

**Returns:**
- Top 10 names mentioned
- Top 10 organizations/departments
- Top 10 locations
- Top amounts/items (gold, cash, etc.)
- Breakdown by sector and category

**Use Case:** Find who and what are most frequently involved in complaints.

**Example Response:**
```json
{
  "total_complaints_analyzed": 45,
  "top_names": [
    {"name": "Ahmad bin Ali", "count": 5},
    {"name": "Dr. Siti", "count": 3}
  ],
  "top_organizations": [
    {"org": "Jabatan Pendidikan Negeri Selangor", "count": 8},
    {"org": "JKR Wilayah Persekutuan", "count": 6}
  ],
  "top_locations": [
    {"location": "Kuala Lumpur", "count": 12},
    {"location": "Petaling Jaya", "count": 7}
  ],
  "top_amounts": [
    {"amount": "RM 50,000", "count": 3},
    {"amount": "10kg emas", "count": 2}
  ],
  "sectors": [
    {"sector": "Pendidikan", "count": 15},
    {"sector": "Pembinaan & Infrastruktur", "count": 10},
    {"sector": "Kesihatan", "count": 8}
  ]
}
```

---

### 3. **Pattern Detection**

```
GET /analytics/patterns?min_occurrences=2
```

**Returns:**
- 2-keyword patterns (e.g., "tender + gold")
- 3-keyword patterns (e.g., "school + bribery + cash")
- Only shows patterns that appear at least `min_occurrences` times

**Use Case:** Discover common corruption patterns and modus operandi.

**Example Response:**
```json
{
  "two_keyword_patterns": [
    {
      "pattern": "tender + gold",
      "count": 3,
      "example": "3 complaints involve both tender + gold"
    },
    {
      "pattern": "school + bribery",
      "count": 4,
      "example": "4 complaints involve both school + bribery"
    },
    {
      "pattern": "police + cash",
      "count": 2,
      "example": "2 complaints involve both police + cash"
    }
  ],
  "three_keyword_patterns": [
    {
      "pattern": "construction + project + commission",
      "count": 2,
      "example": "2 complaints involve construction + project + commission"
    }
  ],
  "total_complaints_analyzed": 45
}
```

---

### 4. **Trending Keywords**

```
GET /analytics/trending?days=30&top_n=15
```

**Returns:**
- Top N most frequent keywords in complaints
- Percentage of complaints containing each keyword
- Useful for spotting emerging trends

**Example Response:**
```json
{
  "period_days": 30,
  "total_complaints": 45,
  "trending_keywords": [
    {"keyword": "tender", "count": 12, "percentage": 26.7},
    {"keyword": "bribery", "count": 10, "percentage": 22.2},
    {"keyword": "gold", "count": 8, "percentage": 17.8},
    {"keyword": "school", "count": 7, "percentage": 15.6},
    {"keyword": "cash", "count": 6, "percentage": 13.3}
  ]
}
```

---

### 5. **Case Analytics**

```
GET /analytics/cases
```

**Returns:**
- Total cases and complaints
- Average complaints per case
- Breakdown by status, priority, classification
- Top 10 largest cases

**Use Case:** Understand how complaints are grouped and prioritized.

**Example Response:**
```json
{
  "total_cases": 25,
  "total_complaints_in_cases": 89,
  "average_complaints_per_case": 3.56,
  "by_status": {
    "open": 15,
    "investigating": 8,
    "closed": 2
  },
  "by_priority": {
    "high": 10,
    "medium": 12,
    "low": 3
  },
  "by_classification": {
    "CRIS": 18,
    "NFA": 7
  },
  "largest_cases": [
    {
      "case_number": "CASE-2025-0023",
      "case_title": "Kes Tender Jabatan Pendidikan",
      "complaint_count": 8,
      "classification": "CRIS",
      "priority": "high",
      "status": "investigating"
    }
  ]
}
```

---

## How It Works

### Data Sources

The analytics system extracts information from:

1. **`extracted_data` field** (JSONB)
   - Names, organizations, locations, amounts
   - Extracted by AI during complaint processing

2. **5W1H fields** (structured)
   - `w1h_who` → Names and people involved
   - `w1h_where` → Locations
   - `w1h_what` → Corruption type
   - `w1h_how` → Method/modus operandi

3. **Metadata fields**
   - `sector` → Government sector
   - `category` → Complaint category
   - `classification` → CRIS/NFA

### Pattern Detection Algorithm

```python
# For each complaint:
1. Extract keywords from description, 5W1H, entities
2. Normalize keywords (e.g., "rasuah" → "bribery", "emas" → "gold")
3. Build keyword set for each complaint

# Find combinations:
4. For all complaint pairs, find common keywords
5. Count how many times each combination appears
6. Filter by minimum occurrences (e.g., ≥2)
7. Rank by frequency
```

**Example:**
- Complaint A: ["tender", "gold", "education"]
- Complaint B: ["tender", "gold", "contract"]
- Complaint C: ["tender", "gold", "school"]

**Result:** Pattern "tender + gold" appears 3 times

### AI Insights Generation

The system sends all analytics data to AI (OpenRouter) with this prompt:

```
Berdasarkan data analitik di bawah, hasilkan ringkasan insight yang berguna:

[Analytics data in JSON]

Hasilkan 4-6 ayat yang merangkumi:
1. Pola atau trend utama
2. Entiti yang paling kerap disebut
3. Kombinasi corruption yang biasa
4. Cadangan tindakan untuk siasatan
```

AI returns natural language insights in Bahasa Malaysia.

---

## Frontend Implementation Guide

### 1. Dashboard Page

```jsx
// Fetch comprehensive analytics
const response = await fetch('/analytics/dashboard?days=30');
const data = await response.json();

// Display sections:
<Dashboard>
  <AIInsights text={data.ai_insights} />

  <PatternSection>
    {data.patterns.two_keyword_patterns.map(p => (
      <PatternCard key={p.pattern}>
        <strong>{p.pattern}</strong>
        <Badge>{p.count} complaints</Badge>
      </PatternCard>
    ))}
  </PatternSection>

  <EntitySection>
    <TopNames data={data.entity_analytics.top_names} />
    <TopOrgs data={data.entity_analytics.top_organizations} />
    <TopLocations data={data.entity_analytics.top_locations} />
  </EntitySection>

  <SectorBreakdown data={data.entity_analytics.sectors} />
</Dashboard>
```

### 2. Visual Representations

**Pattern Detection:**
```
┌─────────────────────────────────────────────┐
│ 🔍 Common Patterns Detected                 │
├─────────────────────────────────────────────┤
│ ■■■■■■■■ tender + gold (3)                  │
│ ■■■■■■■■■■ school + bribery (4)             │
│ ■■■■■ police + cash (2)                     │
└─────────────────────────────────────────────┘
```

**Entity Analytics:**
```
┌─────────────────────────────────────────────┐
│ 👥 Most Mentioned Names                     │
├─────────────────────────────────────────────┤
│ 1. Ahmad bin Ali (5 complaints)             │
│ 2. Dr. Siti Nurhaliza (3 complaints)        │
│ 3. Encik Rahman (2 complaints)              │
└─────────────────────────────────────────────┘
```

**Sector Breakdown (Pie Chart):**
```
     Pendidikan (33%)
     Pembinaan (22%)
     Kesihatan (18%)
     Others (27%)
```

### 3. Time Period Selector

```jsx
<DateRangeSelector
  options={[
    { label: "Last 7 days", value: 7 },
    { label: "Last 30 days", value: 30 },
    { label: "Last 90 days", value: 90 },
    { label: "Last year", value: 365 }
  ]}
  onChange={(days) => refetchAnalytics(days)}
/>
```

### 4. Drilldown Navigation

When user clicks on a pattern:
```jsx
onClick={(pattern) => {
  // e.g., pattern = "tender + gold"
  navigate(`/complaints?keywords=tender,gold`)
}}
```

This shows all complaints matching that pattern.

---

## Advanced Use Cases

### 1. **Alert System**

Monitor for concerning patterns:
```javascript
// Check if any pattern has increased significantly
if (pattern.count > threshold) {
  sendAlert("High frequency pattern detected: " + pattern.pattern)
}
```

### 2. **Network Analysis**

Find connections between entities:
```javascript
// "Ahmad" + "Jabatan Pendidikan" appear together 3 times
// Suggests ongoing relationship to investigate
```

### 3. **Temporal Trends**

Compare patterns across time periods:
```javascript
const last30Days = await fetch('/analytics/patterns?days=30');
const last60Days = await fetch('/analytics/patterns?days=60');

// Compare which patterns are increasing/decreasing
```

### 4. **Export Reports**

Generate PDF reports from analytics:
```javascript
const analytics = await fetch('/analytics/dashboard?days=90');
generatePDFReport(analytics);
```

---

## Database Performance

### Indexes Recommended

```sql
-- Speed up entity extraction
CREATE INDEX idx_complaints_extracted_data
ON complaints USING GIN (extracted_data);

-- Speed up date filtering
CREATE INDEX idx_complaints_submitted_at
ON complaints (submitted_at DESC);

-- Speed up sector/category analytics
CREATE INDEX idx_complaints_sector ON complaints (sector);
CREATE INDEX idx_complaints_category ON complaints (category);
```

---

## Future Enhancements

1. **Geolocation Mapping**
   - Plot complaints on map by location
   - Show heatmaps of corruption hotspots

2. **Time Series Analysis**
   - Show trends over time (weekly/monthly)
   - Predict future complaint volumes

3. **Network Graphs**
   - Visualize connections between entities
   - Show relationships between cases

4. **Comparison Mode**
   - Compare two time periods side-by-side
   - Year-over-year analysis

5. **Custom Alerts**
   - Officers set thresholds for patterns
   - Email/SMS notifications for alerts

---

## Summary

✅ **What We Built:**
- Entity-based analytics (names, orgs, locations, items)
- Pattern detection (2-word and 3-word combinations)
- Trending keyword analysis
- Case-level statistics
- AI-powered natural language insights

✅ **What Officers Get:**
- "3 complaints about tender + gold"
- "4 complaints about school + bribery"
- Actionable insights instead of useless counts
- AI-generated recommendations in Bahasa Malaysia

✅ **Frontend Can Display:**
- Interactive dashboard with charts
- Pattern cards with complaint counts
- Entity rankings and breakdowns
- AI insights prominently at the top
- Drilldown to specific complaints

**This transforms analytics from "100 complaints total" to "Here's what you need to investigate"!** 🎯
