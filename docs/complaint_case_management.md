# Complaint Case Management Design

## Design Decision: Standalone Complaints vs "Removed" Case

### Question
Should removed complaints be moved to a special "Removed/Uncategorized" case, or should they exist as standalone complaints without case assignment?

### Decision: **Allow Standalone Complaints** ✅

### Rationale

1. **Better Semantics**
   - A complaint without a case ≠ a "removed" complaint
   - More accurately reflects the workflow: complaints exist first, then get grouped into cases
   - Officers can temporarily leave complaints unassigned while reviewing

2. **Flexibility**
   - Officers can review unassigned complaints separately
   - No artificial "removed" case that grows indefinitely
   - Cleaner data model

3. **Current Architecture Support**
   - Database already supports this (LEFT JOIN relationship)
   - No migration needed
   - Simpler implementation

---

## Implementation

### Backend Features

#### 1. Case Assignment Tracking
Every complaint now includes case information in the response:
```json
{
  "id": 123,
  "complaint_title": "...",
  "case_id": 456,          // null if not assigned
  "case_number": "CASE-2025-0001"  // null if not assigned
}
```

#### 2. New Endpoints

**List Unassigned Complaints**
```
GET /complaints/unassigned?limit=50&offset=0
```
Returns complaints that are not assigned to any case.

**Enhanced List Complaints with Filter**
```
GET /complaints?assigned=false&status=processed
```
Parameters:
- `assigned=true` - Only complaints in cases
- `assigned=false` - Only complaints NOT in cases
- `assigned` (omitted) - All complaints

**Move Complaint Operations**
```
POST /complaints/{id}/move-to-case/{case_id}     # Move to existing case
POST /complaints/{id}/move-to-new-case           # Create new case
```

#### 3. Automatic Handling
- When a complaint is removed from a case, it becomes standalone (no case assignment)
- If a case becomes empty after removal, the case is automatically deleted
- Officers can easily find and reassign standalone complaints

---

## Frontend Implementation Suggestions

### 1. Dashboard View
Show three sections:
```
┌─────────────────────────────────────────────┐
│ 📊 Dashboard                                │
├─────────────────────────────────────────────┤
│ ⚠️  Unassigned Complaints (23)              │
│    [View All] [Auto-Group]                  │
├─────────────────────────────────────────────┤
│ 📁 Active Cases (45)                        │
│    [View All]                               │
├─────────────────────────────────────────────┤
│ ✅ Processed Complaints (234)               │
│    [View All]                               │
└─────────────────────────────────────────────┘
```

### 2. Complaint List Page
Add filters:
```
┌─────────────────────────────────────────────┐
│ Filters:                                    │
│ [Status ▼] [Category ▼] [Assignment ▼]     │
│                                             │
│ Assignment options:                         │
│ ○ All Complaints                            │
│ ○ Assigned to Cases                         │
│ ● Not Assigned (23 items)                   │
└─────────────────────────────────────────────┘
```

### 3. Complaint Detail Page
Show case assignment prominently:
```
┌─────────────────────────────────────────────┐
│ Complaint #123                              │
├─────────────────────────────────────────────┤
│ Case Assignment:                            │
│ ✅ CASE-2025-0001: Kes Rasuah Jabatan XYZ  │
│    [View Case] [Move to Another Case] [Remove]│
│                                             │
│ OR (if not assigned):                       │
│ ⚠️  Not assigned to any case                │
│    [Assign to Existing Case] [Create New Case]│
└─────────────────────────────────────────────┘
```

### 4. Context Actions
When viewing a complaint:
- **If assigned**: Show "Move to Another Case" or "Remove from Case"
- **If not assigned**: Show "Assign to Case" or "Create New Case"

### 5. Bulk Operations (Future Enhancement)
```
☐ Complaint 120
☐ Complaint 121
☐ Complaint 122

[Group Selected into Case]
```

---

## API Usage Examples

### Get Unassigned Complaints
```bash
GET /complaints/unassigned

Response:
{
  "total": 23,
  "complaints": [...],
  "message": "Found 23 unassigned complaint(s)"
}
```

### Filter by Assignment Status
```bash
# Only unassigned
GET /complaints?assigned=false

# Only assigned
GET /complaints?assigned=true

# All complaints (default)
GET /complaints
```

### Check Complaint's Case Assignment
```bash
GET /complaints/123

Response:
{
  "id": 123,
  "complaint_title": "...",
  "case_id": null,           # Not assigned
  "case_number": null
}
```

### Move Complaint to Case
```bash
POST /complaints/123/move-to-case/456
Response:
{
  "message": "Complaint 123 moved to case CASE-2025-0001",
  "previous_case": null,
  "target_case": { ... }
}
```

---

## Database Schema

No changes needed! The existing schema already supports this:

```sql
-- Complaints can exist independently
CREATE TABLE complaints (
    id SERIAL PRIMARY KEY,
    ...
);

-- Optional many-to-many relationship with cases
CREATE TABLE case_complaints (
    case_id INT REFERENCES cases(id) ON DELETE CASCADE,
    complaint_id INT REFERENCES complaints(id) ON DELETE CASCADE,
    ...
);
```

A complaint not in `case_complaints` is simply unassigned.

---

## Workflow Example

1. **Complaint Submitted** → Status: `unassigned`, case_id: `null`
2. **AI Auto-Groups** → Status: `assigned`, case_id: `123`, case_number: `CASE-2025-0001`
3. **Officer Reviews** → "This doesn't belong here"
4. **Officer Removes** → Status: `unassigned`, case_id: `null` (back to step 1)
5. **Officer Assigns Correctly** → Move to proper case or create new case

---

## Advantages Summary

✅ **Flexibility**: Complaints can be temporarily unassigned
✅ **Clean Data**: No artificial "removed" case
✅ **Easy Review**: Officers can filter and find unassigned complaints
✅ **Accurate Tracking**: Case statistics reflect real groupings
✅ **Simple Implementation**: No schema changes needed

---

## Implementation Complete

- ✅ Added `case_id` and `case_number` to `ComplaintDetail` model
- ✅ Enhanced `/complaints` endpoint with `assigned` filter
- ✅ New `/complaints/unassigned` endpoint
- ✅ Updated `/complaints/{id}` to include case assignment
- ✅ Existing move operations already handle removal properly

**Frontend can now easily implement filtering, assignment tracking, and case management UI!**
