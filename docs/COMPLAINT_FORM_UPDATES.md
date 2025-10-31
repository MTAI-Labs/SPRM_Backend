# Complaint Form Frontend Updates

## Changes Summary

**Date:** 2025-10-31

### What Changed in Backend

1. **All complainant fields are now OPTIONAL** (allows anonymous complaints)
   - `full_name` - Optional
   - `ic_number` - Optional
   - `phone_number` - Optional
   - `email` - Optional

2. **Removed fields:**
   - `category` - Removed completely
   - `urgency_level` - Removed completely

3. **Required fields (unchanged):**
   - `complaint_title` - Still required
   - `complaint_description` - Still required
   - `files` - Optional (can be empty array)

---

## Frontend Changes Required

### 1. Update Form Fields

**Remove these fields:**
```jsx
// DELETE THESE
<FormField name="category" label="Category" required />
<FormField name="urgency_level" label="Urgency Level" required />
```

**Update these fields to optional:**
```jsx
// BEFORE (required)
<FormField name="full_name" label="Full Name" required />
<FormField name="ic_number" label="IC/Passport Number" required />
<FormField name="phone_number" label="Phone Number" required />
<FormField name="email" label="Email" type="email" required />

// AFTER (optional)
<FormField name="full_name" label="Full Name (Optional)" />
<FormField name="ic_number" label="IC/Passport Number (Optional)" />
<FormField name="phone_number" label="Phone Number (Optional)" />
<FormField name="email" label="Email (Optional)" />
```

### 2. Update Form Validation

```javascript
// BEFORE
const validationSchema = Yup.object({
  full_name: Yup.string().required('Name is required'),
  ic_number: Yup.string().required('IC number is required'),
  phone_number: Yup.string().required('Phone number is required'),
  email: Yup.string().email('Invalid email').required('Email is required'),
  category: Yup.string().required('Category is required'),
  urgency_level: Yup.string().required('Urgency level is required'),
  complaint_title: Yup.string().required('Title is required'),
  complaint_description: Yup.string().min(10, 'At least 10 characters').required('Description is required'),
});

// AFTER
const validationSchema = Yup.object({
  full_name: Yup.string().optional(),
  ic_number: Yup.string().optional(),
  phone_number: Yup.string().optional(),
  email: Yup.string().email('Invalid email').optional(),
  // category - REMOVED
  // urgency_level - REMOVED
  complaint_title: Yup.string().required('Title is required'),
  complaint_description: Yup.string().min(10, 'At least 10 characters').required('Description is required'),
});
```

### 3. Update API Call (FormData)

```javascript
// BEFORE
const formData = new FormData();
formData.append('full_name', values.full_name);
formData.append('ic_number', values.ic_number);
formData.append('phone_number', values.phone_number);
formData.append('email', values.email);
formData.append('category', values.category);              // REMOVE
formData.append('urgency_level', values.urgency_level);    // REMOVE
formData.append('complaint_title', values.complaint_title);
formData.append('complaint_description', values.complaint_description);

// AFTER
const formData = new FormData();
// Only append if values exist (allow empty for anonymous)
if (values.full_name) formData.append('full_name', values.full_name);
if (values.ic_number) formData.append('ic_number', values.ic_number);
if (values.phone_number) formData.append('phone_number', values.phone_number);
if (values.email) formData.append('email', values.email);
// category - REMOVED
// urgency_level - REMOVED
formData.append('complaint_title', values.complaint_title);
formData.append('complaint_description', values.complaint_description);

// Files (unchanged)
files.forEach(file => {
  formData.append('files', file);
});
```

### 4. Update Initial Form Values

```javascript
// BEFORE
const initialValues = {
  full_name: '',
  ic_number: '',
  phone_number: '',
  email: '',
  category: '',           // REMOVE
  urgency_level: '',      // REMOVE
  complaint_title: '',
  complaint_description: '',
};

// AFTER
const initialValues = {
  full_name: '',
  ic_number: '',
  phone_number: '',
  email: '',
  // category - REMOVED
  // urgency_level - REMOVED
  complaint_title: '',
  complaint_description: '',
};
```

### 5. Add Anonymous Complaint Helper Text

```jsx
<Box sx={{ mb: 3, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
  <Typography variant="body2">
    ℹ️ You may submit an anonymous complaint by leaving personal information fields empty.
    Only the complaint title and description are required.
  </Typography>
</Box>
```

---

## API Endpoint (Unchanged)

```
POST /complaints/submit
```

**Request Format (multipart/form-data):**
```
full_name: string (optional)
ic_number: string (optional)
phone_number: string (optional)
email: string (optional)
complaint_title: string (required)
complaint_description: string (required)
files: File[] (optional)
```

**Response:**
```json
{
  "id": 123,
  "reference_number": "SPRM2025123",
  "status": "pending",
  "message": "Complaint submitted successfully"
}
```

---

## Database Changes

**No frontend database queries affected** - all handled by backend.

**Migration applied:**
- `phone_number` column: NOT NULL constraint removed
- `category` column: NOT NULL constraint removed (deprecated)
- All complainant fields now allow NULL values

---

## Testing Checklist

- [ ] Submit complaint with all fields filled (traditional)
- [ ] Submit complaint with NO personal info (anonymous)
- [ ] Submit complaint with partial personal info (mixed)
- [ ] Verify category and urgency_level are not sent to backend
- [ ] Verify form validation only requires title and description
- [ ] Verify optional fields show "(Optional)" label
- [ ] Verify anonymous complaint helper text is visible
- [ ] Verify file upload still works (unchanged)
- [ ] Check that old required field styling is removed

---

## Visual Changes Needed

1. **Remove** asterisks (*) from personal info fields
2. **Add** "(Optional)" text to field labels
3. **Remove** Category dropdown/field
4. **Remove** Urgency Level dropdown/field
5. **Add** info box explaining anonymous complaints
6. **Update** form layout if needed (less fields now)

---

## Example: Complete Updated Form Component

```jsx
<Form onSubmit={handleSubmit}>
  {/* Anonymous Complaint Info */}
  <Alert severity="info" sx={{ mb: 3 }}>
    You may submit anonymously by leaving personal information empty.
    Only title and description are required.
  </Alert>

  {/* Personal Information (All Optional) */}
  <Typography variant="h6" gutterBottom>
    Personal Information (Optional)
  </Typography>

  <TextField
    name="full_name"
    label="Full Name (Optional)"
    fullWidth
    margin="normal"
  />

  <TextField
    name="ic_number"
    label="IC/Passport Number (Optional)"
    fullWidth
    margin="normal"
  />

  <TextField
    name="phone_number"
    label="Phone Number (Optional)"
    fullWidth
    margin="normal"
  />

  <TextField
    name="email"
    label="Email (Optional)"
    type="email"
    fullWidth
    margin="normal"
  />

  {/* Complaint Details (Required) */}
  <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
    Complaint Details *
  </Typography>

  <TextField
    name="complaint_title"
    label="Complaint Title *"
    fullWidth
    margin="normal"
    required
  />

  <TextField
    name="complaint_description"
    label="Complaint Description *"
    fullWidth
    multiline
    rows={6}
    margin="normal"
    required
  />

  {/* File Upload (Optional) */}
  <FileUpload
    label="Attach Evidence (Optional)"
    accept="image/*,application/pdf"
    multiple
  />

  <Button type="submit" variant="contained" color="primary">
    Submit Complaint
  </Button>
</Form>
```

---

## Questions?

If you encounter any issues implementing these changes, check:

1. API endpoint is still `POST /complaints/submit`
2. Only title and description are required
3. No need to send category or urgency_level
4. Empty/null values are allowed for all personal info fields
