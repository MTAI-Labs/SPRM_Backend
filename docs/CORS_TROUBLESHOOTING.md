# CORS Troubleshooting Guide

## Problem Fixed ✅

The backend had a CORS configuration issue that has been fixed. The problem was:

```python
# ❌ WRONG - This causes CORS errors in modern browsers
allow_origins=["*"],      # Wildcard
allow_credentials=True,    # Can't use both together!
```

Modern browsers **block** this combination for security reasons.

## ✅ Solution Applied

The backend now uses specific allowed origins:

```python
# ✅ CORRECT - Specific origins with credentials
allow_origins=[
    "http://localhost:3000",   # React
    "http://localhost:5173",   # Vite
    "http://localhost:8080",   # Vue
    # ... etc
]
allow_credentials=True,
```

---

## 🔧 Configuration

### Backend Setup

**Option 1: Use Default (Development)**

The backend automatically allows common development ports:
- `http://localhost:3000` (React default)
- `http://localhost:5173` (Vite default)
- `http://localhost:8080` (Vue default)
- `http://localhost:4200` (Angular default)

**No configuration needed for local development!**

---

**Option 2: Custom Ports (Add to .env)**

If your frontend runs on a different port, add to `.env`:

```bash
# Single origin
ALLOWED_ORIGINS=http://localhost:3001

# Multiple origins (comma-separated, NO SPACES)
ALLOWED_ORIGINS=http://localhost:3001,http://localhost:4000
```

Then restart the backend:
```bash
python src/main.py
```

---

**Option 3: Production (Required)**

For production deployment, **MUST** set in `.env`:

```bash
# Production frontend URL
ALLOWED_ORIGINS=https://your-frontend-domain.com

# Multiple domains
ALLOWED_ORIGINS=https://app.sprm.gov.my,https://admin.sprm.gov.my
```

---

## 🧪 Testing CORS

### 1. Check Backend Server

Make sure backend is running and CORS is configured:

```bash
# Start backend
cd SPRM_Backend
python src/main.py

# You should see in logs:
# CORS middleware configured with origins: ['http://localhost:3000', ...]
```

### 2. Test from Browser Console

Open your frontend in browser, then in Console:

```javascript
// Test basic fetch
fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(data => console.log('✅ CORS working:', data))
  .catch(err => console.error('❌ CORS error:', err));

// Test with credentials
fetch('http://localhost:8000/health', {
  credentials: 'include'
})
  .then(r => r.json())
  .then(data => console.log('✅ Credentials working:', data))
  .catch(err => console.error('❌ Credentials error:', err));
```

### 3. Check Network Tab

1. Open browser DevTools → Network tab
2. Make a request from frontend
3. Check the Response Headers:

**Should see:**
```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: *
Access-Control-Allow-Headers: *
```

**Should NOT see:**
```
Access-Control-Allow-Origin: *  ← BAD with credentials
```

---

## 🐛 Common Issues & Solutions

### Issue 1: "CORS policy: No 'Access-Control-Allow-Origin' header"

**Cause:** Backend not running or wrong URL

**Solution:**
```bash
# 1. Check backend is running
curl http://localhost:8000/health

# 2. Check frontend is calling correct URL
# In frontend code, verify:
const API_URL = 'http://localhost:8000';  // Correct
// NOT: 'http://127.0.0.1:8000' (different origin!)
```

---

### Issue 2: "CORS policy: The value of 'Access-Control-Allow-Origin' header must not be '*' when credentials are true"

**Cause:** Old backend code (before fix)

**Solution:**
```bash
# Pull latest backend code
git pull

# Restart backend
python src/main.py
```

---

### Issue 3: "CORS policy: The 'Access-Control-Allow-Origin' header has a value 'http://localhost:3000' that is not equal to the supplied origin"

**Cause:** Frontend running on different port

**Solution:**

Check frontend port:
```bash
# React
npm start  # Usually runs on 3000

# Vite
npm run dev  # Usually runs on 5173
```

Add to backend `.env`:
```bash
ALLOWED_ORIGINS=http://localhost:5173  # Your actual port
```

Restart backend.

---

### Issue 4: Preflight OPTIONS request fails

**Cause:** Missing OPTIONS method support

**Solution:** Backend already configured to allow all methods (`allow_methods=["*"]`)

If still failing, check:
```javascript
// Frontend - Make sure you're not sending custom headers without proper setup
fetch('http://localhost:8000/complaints/submit', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',  // ✅ OK
    'X-Custom-Header': 'value'           // ❌ May trigger preflight
  },
  body: JSON.stringify(data)
});
```

---

### Issue 5: Works in browser but fails in production

**Cause:** Production URL not in allowed origins

**Solution:**

Backend `.env` for production:
```bash
# Add production frontend URL
ALLOWED_ORIGINS=https://app.sprm.gov.my
```

---

## 📋 Frontend Checklist

### ✅ For React/Vite/Vue Developers

**1. Use Environment Variables**

Create `.env` in frontend:
```bash
# Development
VITE_API_URL=http://localhost:8000
# or for React:
REACT_APP_API_URL=http://localhost:8000
```

**2. Use Consistent URLs**

```javascript
// ✅ GOOD - Use env variable
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ❌ BAD - Hardcoded, inconsistent
const API_URL = 'http://127.0.0.1:8000';  // Different origin!
```

**3. Include Credentials (if using cookies/auth)**

```javascript
// With fetch
fetch(`${API_URL}/complaints`, {
  credentials: 'include'  // Send cookies
});

// With axios
axios.defaults.withCredentials = true;
```

**4. Handle CORS Errors**

```javascript
try {
  const response = await fetch(`${API_URL}/complaints/submit`, {
    method: 'POST',
    body: formData
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  const data = await response.json();
} catch (error) {
  if (error.message.includes('CORS')) {
    console.error('CORS Error - Check backend is running on http://localhost:8000');
  }
  console.error('Error:', error);
}
```

---

## 🚀 Quick Fix Summary

**If you're getting CORS errors:**

1. ✅ **Backend is running?** `curl http://localhost:8000/health`
2. ✅ **Using latest code?** `git pull` + restart backend
3. ✅ **Frontend port correct?** Check port in browser URL, add to `.env` if needed
4. ✅ **Using consistent URLs?** Use `http://localhost:8000` everywhere, not `127.0.0.1`
5. ✅ **Check browser console** for specific CORS error message

**Still stuck?** Share the exact error message from browser console.

---

## 📞 Support

**Backend Logs:**
Check console where backend is running for CORS configuration:
```
CORS middleware configured with origins: [...]
```

**Browser Console:**
Look for red CORS errors with details about what failed

**Test Endpoint:**
```bash
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     http://localhost:8000/complaints/submit -v
```

Should return CORS headers in response.

---

**Last Updated:** 2025-11-02
**Backend Version:** 2.3.0
