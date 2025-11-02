# Audit Log System - Frontend Integration Guide

## Overview

The backend now has a complete **audit logging system** that tracks all user actions including:
- Complaint submissions (IP address + documents uploaded)
- Officer actions (evaluations, reviews, updates)
- Case management operations
- Document uploads/downloads

This guide explains how to integrate the audit log features into your frontend.

---

## 🎯 What's Been Implemented

### Backend Features
✅ **Database table**: `audit_logs` with comprehensive tracking fields
✅ **Middleware**: Automatically captures IP address, user-agent, and request context
✅ **Audit logging**: All key endpoints now log actions
✅ **Admin API**: 8 endpoints for viewing and querying audit logs

### Tracked Actions
| Action | Description | IP Tracked | User ID Tracked |
|--------|-------------|------------|-----------------|
| `complaint.create` | New complaint submitted | ✅ | ✅ (if provided) |
| `complaint.update` | Complaint fields edited by officer | ✅ | ✅ |
| `complaint.evaluate` | Officer evaluates complaint | ✅ | ✅ |
| `complaint.review` | Officer reviews and changes status | ✅ | ✅ |
| `document.upload` | Document uploaded to complaint | ✅ | ✅ (if provided) |
| `case.create` | New case created | ✅ | ✅ |
| `case.update` | Case information updated | ✅ | ✅ |
| `case.delete` | Case deleted | ✅ | ✅ |
| `case.add_complaint` | Complaint added to case | ✅ | ✅ |

---

## 🔧 Frontend Changes Required

### 1. **Send User ID in Headers (Optional but Recommended)**

Currently, the system extracts `user_id` from request body fields like `evaluated_by`, `reviewed_by`, etc. For better tracking, you can optionally send the user ID in custom headers:

#### JavaScript Example
```javascript
// When making API calls, add these headers:
const headers = {
  'Content-Type': 'application/json',
  'X-User-ID': 'officer123',        // Officer username/ID
  'X-User-Role': 'officer',         // User role (optional)
};

// Example: Submitting complaint evaluation
fetch('https://your-api.com/complaints/123/evaluation', {
  method: 'PUT',
  headers: headers,
  body: JSON.stringify(evaluationData)
});
```

#### TypeScript Example
```typescript
interface AuditHeaders {
  'X-User-ID'?: string;
  'X-User-Role'?: string;
}

const makeAuthenticatedRequest = async (
  url: string,
  options: RequestInit,
  userId?: string
) => {
  const headers = {
    ...options.headers,
    ...(userId && { 'X-User-ID': userId }),
  };

  return fetch(url, { ...options, headers });
};
```

**Note**: The `X-User-ID` header is **optional**. If not provided, the system will extract the user ID from request body fields.

---

### 2. **Admin Panel - Audit Log Viewer**

You need to create an admin panel page to view audit logs. Here are the available API endpoints:

#### A. **Get All Audit Logs (with filters)**
```
GET /admin/audit-logs
```

**Query Parameters:**
- `user_id` - Filter by officer ID (e.g., `officer123`)
- `action` - Filter by action type (e.g., `complaint.update`)
- `entity_type` - Filter by entity type (`complaint`, `case`, `document`)
- `entity_id` - Filter by specific ID (e.g., complaint #123)
- `start_date` - Start date (ISO format: `2025-01-01T00:00:00`)
- `end_date` - End date (ISO format)
- `ip_address` - Filter by IP address
- `limit` - Max results (default: 100)
- `offset` - Pagination offset

**Example Request:**
```javascript
// Get all complaint updates by officer123
const response = await fetch(
  '/admin/audit-logs?user_id=officer123&action=complaint.update&limit=50'
);
const data = await response.json();

console.log(data);
// {
//   "total": 12,
//   "limit": 50,
//   "offset": 0,
//   "logs": [
//     {
//       "id": 1,
//       "user_id": "officer123",
//       "ip_address": "192.168.1.100",
//       "user_agent": "Mozilla/5.0...",
//       "action": "complaint.update",
//       "entity_type": "complaint",
//       "entity_id": 456,
//       "description": "Complaint updated: w1h_what, sector",
//       "changes": {
//         "before": {"sector": "Kesihatan"},
//         "after": {"sector": "Pendidikan"},
//         "changed_fields": [...]
//       },
//       "timestamp": "2025-01-15T14:30:00",
//       "endpoint": "/complaints/456",
//       "http_method": "PUT",
//       "success": true
//     }
//   ]
// }
```

#### B. **Get Recent Activity**
```
GET /admin/audit-logs/recent?limit=50
```

Returns the 50 most recent actions across all users.

#### C. **Get Activity by User**
```
GET /admin/audit-logs/user/{user_id}?limit=100
```

Example: `GET /admin/audit-logs/user/officer123`

#### D. **Get Activity by IP Address**
```
GET /admin/audit-logs/ip/{ip_address}
```

Example: `GET /admin/audit-logs/ip/192.168.1.100`

Useful for tracking anonymous complaint submissions.

#### E. **Get Entity History**
```
GET /admin/audit-logs/entity/{entity_type}/{entity_id}
```

Example: `GET /admin/audit-logs/entity/complaint/123`

Shows complete history of a complaint (who created, edited, evaluated, reviewed it).

#### F. **Get Statistics**
```
GET /admin/audit-logs/stats
```

Returns:
```json
{
  "statistics": {
    "total_logs": 1523,
    "unique_users": 15,
    "unique_ips": 47,
    "successful_actions": 1498,
    "failed_actions": 25
  }
}
```

#### G. **Get Action Breakdown**
```
GET /admin/audit-logs/breakdown
```

Returns:
```json
{
  "total": 8,
  "breakdown": [
    {
      "action": "complaint.create",
      "entity_type": "complaint",
      "count": 523,
      "success_count": 520,
      "error_count": 3
    },
    {
      "action": "complaint.update",
      "entity_type": "complaint",
      "count": 287,
      "success_count": 287,
      "error_count": 0
    }
  ]
}
```

---

### 3. **UI Components to Build**

#### A. **Audit Log Table Component**
```tsx
// React/TypeScript example
interface AuditLog {
  id: number;
  user_id: string | null;
  ip_address: string | null;
  action: string;
  entity_type: string;
  entity_id: number | null;
  description: string;
  timestamp: string;
  success: boolean;
}

const AuditLogTable: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [filters, setFilters] = useState({
    user_id: '',
    action: '',
    limit: 50
  });

  useEffect(() => {
    fetchAuditLogs();
  }, [filters]);

  const fetchAuditLogs = async () => {
    const params = new URLSearchParams(
      Object.entries(filters).filter(([_, v]) => v)
    );
    const response = await fetch(`/admin/audit-logs?${params}`);
    const data = await response.json();
    setLogs(data.logs);
  };

  return (
    <div>
      {/* Filters */}
      <div className="filters">
        <input
          placeholder="Filter by User ID"
          value={filters.user_id}
          onChange={(e) => setFilters({...filters, user_id: e.target.value})}
        />
        <select
          value={filters.action}
          onChange={(e) => setFilters({...filters, action: e.target.value})}
        >
          <option value="">All Actions</option>
          <option value="complaint.create">Complaint Created</option>
          <option value="complaint.update">Complaint Updated</option>
          <option value="complaint.evaluate">Complaint Evaluated</option>
          <option value="case.create">Case Created</option>
        </select>
      </div>

      {/* Table */}
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>User</th>
            <th>IP Address</th>
            <th>Action</th>
            <th>Description</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {logs.map(log => (
            <tr key={log.id}>
              <td>{new Date(log.timestamp).toLocaleString()}</td>
              <td>{log.user_id || 'Anonymous'}</td>
              <td>{log.ip_address}</td>
              <td>{log.action}</td>
              <td>{log.description}</td>
              <td>{log.success ? '✅' : '❌'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

#### B. **Complaint Portal - Submission Tracker**
Show which IP submitted a complaint and what documents were uploaded:

```tsx
const ComplaintSubmissionInfo: React.FC<{complaintId: number}> = ({complaintId}) => {
  const [logs, setLogs] = useState<AuditLog[]>([]);

  useEffect(() => {
    // Get audit history for this complaint
    fetch(`/admin/audit-logs/entity/complaint/${complaintId}`)
      .then(r => r.json())
      .then(data => setLogs(data.logs));
  }, [complaintId]);

  const submissionLog = logs.find(log => log.action === 'complaint.create');
  const documentLogs = logs.filter(log => log.action === 'document.upload');

  return (
    <div className="submission-info">
      <h3>Submission Information</h3>
      <p><strong>Submitted from IP:</strong> {submissionLog?.ip_address || 'N/A'}</p>
      <p><strong>Submitted at:</strong> {submissionLog?.timestamp}</p>

      <h4>Documents Uploaded:</h4>
      <ul>
        {documentLogs.map(log => (
          <li key={log.id}>
            {log.description} - {new Date(log.timestamp).toLocaleString()}
          </li>
        ))}
      </ul>
    </div>
  );
};
```

#### C. **Officer Activity Dashboard**
Track what each officer has been doing:

```tsx
const OfficerActivityDashboard: React.FC<{officerId: string}> = ({officerId}) => {
  const [activity, setActivity] = useState<AuditLog[]>([]);

  useEffect(() => {
    fetch(`/admin/audit-logs/user/${officerId}?limit=100`)
      .then(r => r.json())
      .then(data => setActivity(data.logs));
  }, [officerId]);

  const actionCounts = activity.reduce((acc, log) => {
    acc[log.action] = (acc[log.action] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div>
      <h2>Officer {officerId} Activity</h2>
      <div className="stats">
        <p>Total Actions: {activity.length}</p>
        <p>Complaints Evaluated: {actionCounts['complaint.evaluate'] || 0}</p>
        <p>Complaints Reviewed: {actionCounts['complaint.review'] || 0}</p>
        <p>Cases Created: {actionCounts['case.create'] || 0}</p>
      </div>

      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Action</th>
            <th>Description</th>
            <th>IP</th>
          </tr>
        </thead>
        <tbody>
          {activity.map(log => (
            <tr key={log.id}>
              <td>{new Date(log.timestamp).toLocaleString()}</td>
              <td>{log.action}</td>
              <td>{log.description}</td>
              <td>{log.ip_address}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

---

## 📊 Sample UI Mockups

### 1. **Admin Audit Log Page**
```
┌─────────────────────────────────────────────────────────────┐
│ 📋 Audit Logs                                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Filters:                                                    │
│ [User ID: ________] [Action: All ▼] [Date: ______ to ______]│
│ [IP Address: _________] [Search]                           │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ Time          │ User      │ IP          │ Action           │
├─────────────────────────────────────────────────────────────┤
│ 2025-01-15    │ officer1  │ 192.168.1.5 │ complaint.update │
│ 14:30:22      │           │             │ Complaint #123   │
│               │           │             │ ✅ Success       │
├─────────────────────────────────────────────────────────────┤
│ 2025-01-15    │ Anonymous │ 103.10.5.2  │ complaint.create │
│ 14:25:10      │           │             │ New complaint    │
│               │           │             │ ✅ Success       │
└─────────────────────────────────────────────────────────────┘
```

### 2. **Complaint Submission Info Panel**
```
┌──────────────────────────────────────────┐
│ 📝 Complaint #123 - Submission Info      │
├──────────────────────────────────────────┤
│ Submitted from IP: 103.10.28.15          │
│ Submitted at: 2025-01-15 09:30 AM        │
│ User Agent: Chrome/Windows               │
│                                          │
│ Documents Uploaded:                      │
│  • evidence.pdf (2.3 MB) - 09:30 AM     │
│  • photo.jpg (1.1 MB) - 09:31 AM        │
│                                          │
│ Officer Actions:                         │
│  • Evaluated by officer1 - 10:00 AM     │
│    IP: 192.168.1.5                      │
│  • Reviewed by officer2 - 14:30 PM      │
│    IP: 192.168.1.10                     │
│    Status changed to: Escalated         │
└──────────────────────────────────────────┘
```

---

## 🔒 Security Notes

1. **Authentication**: The audit log endpoints are under `/admin/` but currently have NO authentication. You should add authentication middleware in the frontend (check user role) before allowing access to these pages.

2. **IP Privacy**: Consider data privacy laws when storing IP addresses. You may want to:
   - Hash IP addresses for anonymity
   - Add data retention policies (delete logs older than X months)
   - Comply with GDPR/local privacy regulations

3. **User ID**: Since there's no built-in authentication system, user IDs are manually entered. Consider implementing proper authentication with JWT tokens in the future.

---

## 🚀 Testing the Implementation

### 1. **Test Database Table Creation**
```bash
# The audit_logs table should be created automatically when the app starts
# Check if it exists:
psql -U postgres -d sprm_db -c "\d audit_logs"
```

### 2. **Test Audit Logging**
```bash
# Submit a complaint and check if audit log is created
curl -X POST http://localhost:8000/complaints/submit \
  -H "X-User-ID: test_user" \
  -F "complaint_title=Test" \
  -F "complaint_description=Testing audit logs"

# Then check audit logs
curl http://localhost:8000/admin/audit-logs/recent?limit=5
```

### 3. **Test IP Tracking**
```bash
# Submit from different IP (use proxy or VPN)
curl -X POST http://localhost:8000/complaints/submit \
  -H "X-Forwarded-For: 203.10.5.100" \
  -F "complaint_title=Test" \
  -F "complaint_description=Test"

# Check if IP was logged
curl http://localhost:8000/admin/audit-logs/ip/203.10.5.100
```

---

## 📝 Summary of Frontend Tasks

### Must Do:
1. ✅ Create an **Admin Panel page** with audit log viewer
2. ✅ Add **filters** for viewing logs (user, action, date, IP)
3. ✅ Display **complaint submission info** (IP + documents) in complaint details page

### Optional (Recommended):
1. Send `X-User-ID` header in API requests for better tracking
2. Add **officer activity dashboard** showing what each officer has done
3. Add **statistics dashboard** showing audit log stats
4. Implement **real-time notifications** for critical actions
5. Add **export to CSV** functionality for audit reports

### Future Enhancements:
1. Implement proper **JWT authentication** system
2. Add **role-based access control** (only admins can view audit logs)
3. Add **search functionality** for searching through logs
4. Add **date range picker** for filtering by date
5. Add **IP geolocation** to show where complaints came from (map view)

---

## 🛠️ Need Help?

If you encounter any issues or need clarification on any endpoint, check:
- FastAPI Interactive Docs: `http://your-api-url/docs`
- Look for endpoints under **"AUDIT LOG ENDPOINTS (ADMIN PANEL)"** section

All audit endpoints start with `/admin/audit-logs/`
