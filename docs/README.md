# SPRM Backend API - Documentation Index

**Malaysian Anti-Corruption Commission (SPRM) - AI-Powered Complaint Management System**

---

## 📦 What's This Project?

A complete backend API system for processing corruption complaints with AI-powered features including:
- Document extraction (PDF/Image text analysis)
- 5W1H summary generation in Bahasa Malaysia
- Automatic corruption classification (YES/NO)
- Case management with auto-grouping
- Officer evaluation system
- Related cases detection

---

## 📚 Documentation Files

### 🎯 For Backend Developers

#### **Backend_README.md** - Complete Backend Guide
**Purpose:** Full backend documentation with setup, deployment, API reference
**When to read:** Setting up the backend, understanding the full system
**Contains:**
- Installation and setup instructions
- Complete API endpoint reference
- Database schema details
- Configuration options
- Deployment guide
- Troubleshooting

---

### 🖥️ For Frontend Developers

#### **FRONTEND_QUICKSTART.md** - Quick Start Guide ⭐ START HERE
**Purpose:** Get started with frontend integration in 5 minutes
**When to read:** First time integrating with the API
**Contains:**
- Quick setup steps
- Basic API usage examples (React, Vue, vanilla JS)
- Common patterns
- Quick reference

#### **COMPLAINT_API.md** - Complaint System Guide ⭐ ESSENTIAL
**Purpose:** Complete guide for complaint submission and display
**When to read:** Building complaint forms, displaying complaints
**Contains:**
- Complaint submission flow
- File upload examples
- Form field reference
- Response formats
- Code examples in React/Vue/JavaScript

#### **FRONTEND_GUIDE.md** - Related Cases Feature Guide
**Purpose:** Implement related cases detection UI
**When to read:** Building case management features
**Contains:**
- Related cases API usage
- UI examples with screenshots
- Warning banners
- API endpoints
- Complete React component examples

#### **EVALUATION_SYSTEM_GUIDE.md** - Officer Evaluation Guide ⭐ ESSENTIAL
**Purpose:** Implement officer evaluation forms
**When to read:** Building officer review/evaluation screens
**Contains:**
- Two-part evaluation form structure
- API endpoints for evaluation
- Dropdown options (sectors, sub-sectors, etc.)
- Complete form examples in React
- Field descriptions and requirements
- Submit evaluation flow

---

### 📖 Reference Documentation

#### **API_SPECIFICATION.md** - Detailed API Reference
**Purpose:** Comprehensive API documentation
**When to read:** Need detailed information about specific endpoints
**Contains:**
- All API endpoints with parameters
- Request/response schemas
- Error codes
- Pagination details
- Filtering options

#### **USAGE_GUIDE.md** - Backend Usage Examples
**Purpose:** Python code examples for backend operations
**When to read:** Working on backend features, writing scripts
**Contains:**
- Python API usage
- Command-line examples
- Backend service usage
- Testing examples

#### **PROJECT_STRUCTURE.md** - Technical Architecture
**Purpose:** Understanding the codebase structure
**When to read:** Onboarding new developers, making architectural changes
**Contains:**
- Project folder structure
- Service layer overview
- Database design
- Integration points
- Technology stack

---

### 📊 Feature-Specific Guides

#### **analytics_guide.md** - Analytics Dashboard Guide
**Purpose:** Build analytics and reporting features
**When to read:** Implementing dashboard, statistics, charts
**Contains:**
- Analytics API endpoints
- Pattern detection
- Trending keywords
- Entity analytics
- AI-powered insights
- Chart/dashboard examples

#### **analytics_caching_guide.md** - Analytics Performance
**Purpose:** Optimize analytics performance
**When to read:** Analytics queries are slow, need caching
**Contains:**
- Caching strategy
- Performance optimization
- Background refresh
- Cache invalidation

#### **complaint_case_management.md** - Case Management Design
**Purpose:** Understanding case auto-grouping and management
**When to read:** Working on case features, understanding grouping logic
**Contains:**
- Auto-grouping algorithm
- Case management workflow
- Manual case operations
- Move complaints between cases

---

## 🚀 Getting Started (Frontend Developers)

### Step 1: Read This First
1. **FRONTEND_QUICKSTART.md** - Get familiar with API basics (10 minutes)

### Step 2: Build Core Features
2. **COMPLAINT_API.md** - Implement complaint submission form
3. **Backend_README.md** - Reference specific endpoints as needed

### Step 3: Build Advanced Features
4. **EVALUATION_SYSTEM_GUIDE.md** - Implement officer evaluation forms
5. **FRONTEND_GUIDE.md** - Add related cases warnings
6. **analytics_guide.md** - Build analytics dashboard

---

## 📡 Essential API Endpoints (Quick Reference)

### Complaints
- `POST /complaints/submit` - Submit new complaint with files
- `GET /complaints/{id}` - Get complaint details
- `GET /complaints` - List complaints (with filters)
- `PUT /complaints/{id}` - Update complaint
- `PUT /complaints/{id}/evaluation` - Submit officer evaluation

### Cases
- `GET /cases` - List all cases
- `GET /cases/{id}` - Get case details with all complaints
- `POST /cases` - Create case manually
- `GET /cases/{id}/related` - Get related closed cases

### Analytics
- `GET /analytics/dashboard` - Complete analytics dashboard
- `GET /analytics/entities` - Top entities (names, orgs, locations)
- `GET /analytics/patterns` - Pattern detection

### Configuration
- `GET /config/evaluation-options` - Get all dropdown options for evaluation forms

### Utilities
- `GET /health` - Health check
- `GET /documents/{id}/download` - Download/preview documents

---

## 🎯 Which File Do I Need?

### **I want to...**

#### Build complaint submission form
→ **COMPLAINT_API.md** (sections: Submit Complaint, File Upload)

#### Display complaint details
→ **COMPLAINT_API.md** (section: Get Complaint Details)

#### Build officer evaluation form
→ **EVALUATION_SYSTEM_GUIDE.md** (complete guide)

#### Show related cases warning
→ **FRONTEND_GUIDE.md** (complete guide)

#### Build analytics dashboard
→ **analytics_guide.md** (all sections)

#### List/filter complaints
→ **API_SPECIFICATION.md** (endpoint: GET /complaints)

#### Manage cases (create, edit, delete)
→ **Backend_README.md** (section: Case Management)

#### Download/preview documents
→ **COMPLAINT_API.md** (section: Download Document)

#### Understand database schema
→ **Backend_README.md** (section: Database Schema)

#### Set up backend server
→ **Backend_README.md** (section: Quick Start)

#### Debug API issues
→ **Backend_README.md** (section: Troubleshooting)

---

## 📦 Files to Share with Frontend Team

### **Priority 1: Essential** (Must Read)
1. ✅ **FRONTEND_QUICKSTART.md** - Quick start guide
2. ✅ **COMPLAINT_API.md** - Complaint submission guide
3. ✅ **EVALUATION_SYSTEM_GUIDE.md** - Evaluation forms guide

### **Priority 2: Feature-Specific** (Read When Building Feature)
4. ✅ **FRONTEND_GUIDE.md** - Related cases feature
5. ✅ **analytics_guide.md** - Analytics dashboard
6. ✅ **API_SPECIFICATION.md** - Complete API reference

### **Priority 3: Reference** (Optional)
7. ⚪ **Backend_README.md** - Full backend documentation
8. ⚪ **PROJECT_STRUCTURE.md** - Architecture overview

---

## 🔍 Quick Links

### Live API Documentation
- **Swagger UI:** http://localhost:8000/docs (Interactive API testing)
- **ReDoc:** http://localhost:8000/redoc (Clean API reference)
- **Health Check:** http://localhost:8000/health

### Key Concepts

**5W1H Summary:**
AI-generated summary in 6 parts (What, Who, When, Where, Why, How)

**YES/NO Classification:**
- YES = Corruption case (requires investigation)
- NO = Not corruption (no action needed)

**Auto-Grouping:**
System automatically groups similar complaints into cases (similarity ≥ 0.70)

**Related Cases:**
When creating a new case, system checks for similar closed cases and stores them for reference

**Evaluation System:**
Two-part form for officers to review AI results and add classification details

---

## 💻 Example: Hello World (Frontend)

```javascript
// Step 1: Check if backend is running
fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(d => console.log('Backend is:', d.status));

// Step 2: Submit a complaint
const formData = new FormData();
formData.append('phone_number', '012-3456789');
formData.append('complaint_title', 'Test Complaint');
formData.append('category', 'Rasuah');
formData.append('complaint_description', 'This is a test');

fetch('http://localhost:8000/complaints/submit', {
  method: 'POST',
  body: formData
})
  .then(r => r.json())
  .then(d => console.log('Complaint ID:', d.complaint_id));

// Step 3: Get complaint details
fetch('http://localhost:8000/complaints/1')
  .then(r => r.json())
  .then(d => console.log('Complaint:', d));
```

---

## 🆘 Need Help?

### Common Issues

**Q: API returns CORS error**
A: Backend CORS is enabled for all origins. Check frontend URL.

**Q: File upload fails**
A: Max 10MB per file. Allowed: PDF, PNG, JPG, JPEG

**Q: Response is slow**
A: Background processing takes 8-25 seconds. Poll `/complaints/{id}` to check status.

**Q: Classification is wrong**
A: Officers can edit via evaluation form (PUT /complaints/{id}/evaluation)

### Getting Support

1. Check **Backend_README.md** → Troubleshooting section
2. View API docs at http://localhost:8000/docs
3. Check backend server logs for errors
4. Review request/response in browser DevTools

---

## 📝 What's New

### Latest Updates (2025-10-30)
- ✨ Added evaluation system for officers
- ✨ Added related cases detection for closed cases
- ✨ Changed classification from CRIS/NFA to YES/NO
- ✨ Removed keyword extraction (was generating noise)
- ✨ Updated to 10 bilingual sectors
- ✨ Simplified akta selection (two-step AI approach)
- 🔧 Added PDF text extraction support
- 🔧 Enhanced case management with manual operations

---

## 📄 File Summary

| File | Lines | Purpose | Audience |
|------|-------|---------|----------|
| **Backend_README.md** | 1477 | Complete backend guide | Backend + DevOps |
| **FRONTEND_QUICKSTART.md** | ~300 | Quick start for frontend | Frontend (Priority 1) |
| **COMPLAINT_API.md** | ~400 | Complaint submission guide | Frontend (Priority 1) |
| **EVALUATION_SYSTEM_GUIDE.md** | ~450 | Evaluation forms guide | Frontend (Priority 1) |
| **FRONTEND_GUIDE.md** | ~350 | Related cases feature | Frontend (Priority 2) |
| **analytics_guide.md** | ~400 | Analytics dashboard | Frontend (Priority 2) |
| **API_SPECIFICATION.md** | ~600 | Complete API reference | Frontend (Priority 2) |
| **USAGE_GUIDE.md** | ~350 | Backend usage examples | Backend |
| **PROJECT_STRUCTURE.md** | ~400 | Architecture overview | Backend + Team Leads |
| **analytics_caching_guide.md** | ~250 | Analytics optimization | Backend |
| **complaint_case_management.md** | ~300 | Case management design | Backend + Frontend |

**Total Documentation:** ~5,000 lines

---

## 🎉 Summary

### ✅ What Frontend Developers Get

1. **4 Essential Guides** for building the UI
2. **Complete API Reference** with examples
3. **Code Examples** in React, Vue, vanilla JS
4. **Interactive API Docs** at http://localhost:8000/docs
5. **Clear File Organization** with priority levels

### 📋 Recommended Reading Order

1. **FRONTEND_QUICKSTART.md** (15 min)
2. **COMPLAINT_API.md** (30 min)
3. **EVALUATION_SYSTEM_GUIDE.md** (30 min)
4. **FRONTEND_GUIDE.md** (20 min)
5. **analytics_guide.md** (30 min)

**Total:** ~2 hours to understand entire API

---

**Need the backend documentation?** See [Backend_README.md](Backend_README.md)

**Ready to start?** Begin with [FRONTEND_QUICKSTART.md](FRONTEND_QUICKSTART.md)

**Have questions?** Check http://localhost:8000/docs for interactive API testing
