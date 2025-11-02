# HTTPS Setup Guide for SPRM Backend

## Problem

Your frontend is on **HTTPS** (`https://sprm.mtailabs.ai`) but backend is on **HTTP** (`http://192.168.120.110:8000`).

**Error:**
```
Mixed Content: The page at 'https://sprm.mtailabs.ai/...' was loaded over HTTPS,
but requested an insecure resource 'http://192.168.120.110:8000/...'.
This request has been blocked; the content must be served over HTTPS.
```

Browsers **block HTTP requests from HTTPS pages** for security.

---

## ✅ Solution: Setup HTTPS on Backend

You have **3 options**:

---

## Option 1: Nginx Reverse Proxy with Let's Encrypt SSL (RECOMMENDED) 🌟

**Best for production. FREE SSL certificate, auto-renewal.**

### Prerequisites
- A domain/subdomain pointing to your server (e.g., `api.sprm.mtailabs.ai`)
- Port 80 and 443 open on firewall

### Steps

#### 1. Setup domain DNS

Point subdomain to your server:
```
Type: A Record
Name: api.sprm.mtailabs.ai
Value: 192.168.120.110
```

Wait 5-10 minutes for DNS propagation.

#### 2. Run the setup script

```bash
cd /home/kiesun/SPRM_Backend
chmod +x nginx-ssl-setup.sh
sudo ./nginx-ssl-setup.sh
```

#### 3. Edit the nginx config

```bash
sudo nano /etc/nginx/sites-available/sprm-backend
```

Change `api.sprm.mtailabs.ai` to your actual domain.

#### 4. Get FREE SSL certificate

```bash
sudo certbot --nginx -d api.sprm.mtailabs.ai
```

Enter your email when prompted. Certificate will auto-renew!

#### 5. Restart services

```bash
# Restart nginx
sudo systemctl restart nginx

# Keep backend running on localhost:8000
# Nginx will proxy requests to it
```

#### 6. Update frontend

Change API URL in frontend:
```javascript
// OLD ❌
const API_URL = 'http://192.168.120.110:8000';

// NEW ✅
const API_URL = 'https://api.sprm.mtailabs.ai';
```

### Test

```bash
# Should return healthy status
curl https://api.sprm.mtailabs.ai/health
```

✅ **DONE!** Frontend can now call backend over HTTPS.

---

## Option 2: Deploy Backend on Same Domain (EASIEST)

If your backend can be on the same domain as frontend.

### Current Setup
- Frontend: `https://sprm.mtailabs.ai`
- Backend: `http://192.168.120.110:8000` ❌

### Target Setup
- Frontend: `https://sprm.mtailabs.ai`
- Backend: `https://sprm.mtailabs.ai/api` ✅ (same domain!)

### Steps

#### 1. Configure nginx on frontend server

Add to your nginx config (on the server hosting `sprm.mtailabs.ai`):

```nginx
server {
    listen 443 ssl http2;
    server_name sprm.mtailabs.ai;

    # ... existing frontend config ...

    # Proxy /api to backend server
    location /api/ {
        proxy_pass http://192.168.120.110:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Rewrite /api/complaints to /complaints
        rewrite ^/api/(.*)$ /$1 break;
    }
}
```

#### 2. Test nginx config

```bash
sudo nginx -t
sudo systemctl reload nginx
```

#### 3. Update frontend

```javascript
// OLD ❌
const API_URL = 'http://192.168.120.110:8000';

// NEW ✅
const API_URL = '/api';  // Same origin!
```

✅ **DONE!** No CORS issues, no mixed content!

---

## Option 3: Self-Signed Certificate (TESTING ONLY) 🧪

**Only for local testing. NOT for production.**

### Steps

#### 1. Generate certificate

```bash
cd /home/kiesun/SPRM_Backend
chmod +x setup-self-signed-ssl.sh
./setup-self-signed-ssl.sh
```

#### 2. Install uvicorn with SSL support

```bash
pip install uvicorn[standard]
```

#### 3. Start backend with HTTPS

```bash
# Stop current backend (Ctrl+C)

# Start with SSL
uvicorn src.main:app \
  --host 0.0.0.0 \
  --port 8443 \
  --ssl-keyfile=ssl/key.pem \
  --ssl-certfile=ssl/cert.pem
```

#### 4. Update frontend

```javascript
const API_URL = 'https://192.168.120.110:8443';
```

#### 5. Accept certificate in browser

First time accessing, browser will show security warning:
1. Go to `https://192.168.120.110:8443/health`
2. Click "Advanced" → "Proceed Anyway"
3. Now API calls will work

⚠️ **WARNING:** Users will see security warnings. Only use for testing!

---

## Comparison

| Option | Pros | Cons | Best For |
|--------|------|------|----------|
| **Nginx + Let's Encrypt** | ✅ Free SSL<br>✅ Auto-renewal<br>✅ Production-ready | ❌ Needs domain | **Production** |
| **Same Domain Proxy** | ✅ No CORS issues<br>✅ Simplest for users | ❌ Needs nginx access | **Easiest setup** |
| **Self-Signed** | ✅ Quick to setup | ❌ Security warnings<br>❌ Not for production | **Testing only** |

---

## Recommended Approach

### For Production:

**Use Option 1 (Nginx + Let's Encrypt)**

1. Get subdomain: `api.sprm.mtailabs.ai`
2. Run `nginx-ssl-setup.sh`
3. Get SSL certificate with certbot
4. Update frontend API URL

**Total time:** ~15 minutes

### For Quick Testing:

**Use Option 3 (Self-Signed)**

1. Run `setup-self-signed-ssl.sh`
2. Start backend with SSL
3. Accept certificate in browser

**Total time:** ~5 minutes

---

## Troubleshooting

### "Connection refused" on HTTPS

**Check nginx is running:**
```bash
sudo systemctl status nginx
```

**Check nginx logs:**
```bash
sudo tail -f /var/log/nginx/error.log
```

### "Certificate invalid"

**For Let's Encrypt:**
```bash
# Renew certificate
sudo certbot renew

# Restart nginx
sudo systemctl restart nginx
```

**For self-signed:**
Browser will always show warning. Click "Proceed Anyway".

### Backend not receiving requests

**Check nginx is proxying:**
```bash
# Test from server itself
curl http://127.0.0.1:8000/health

# Should work
```

**Check backend logs:**
```bash
# In terminal where backend is running
# Should see incoming requests
```

---

## Security Notes

### Production Checklist

- ✅ Use proper SSL certificate (Let's Encrypt or commercial)
- ✅ Keep certificates up to date
- ✅ Use strong SSL protocols (TLS 1.2+)
- ✅ Enable HSTS headers
- ✅ Disable HTTP (redirect to HTTPS)
- ✅ Use firewall (only allow 80, 443)

### DO NOT in Production

- ❌ Self-signed certificates
- ❌ Allow HTTP access
- ❌ Expose backend port directly (8000)
- ❌ Use `allow_origins=["*"]` in CORS

---

## Quick Commands Reference

```bash
# Option 1: Nginx + SSL
sudo ./nginx-ssl-setup.sh
sudo certbot --nginx -d api.sprm.mtailabs.ai
sudo systemctl restart nginx

# Option 2: Same domain
# Edit nginx config, add /api proxy
sudo nano /etc/nginx/sites-available/default
sudo nginx -t && sudo systemctl reload nginx

# Option 3: Self-signed
./setup-self-signed-ssl.sh
uvicorn src.main:app --host 0.0.0.0 --port 8443 \
  --ssl-keyfile=ssl/key.pem --ssl-certfile=ssl/cert.pem
```

---

## Questions?

**Which option should I use?**
- Production → Option 1 (Nginx + Let's Encrypt)
- Quick fix → Option 2 (Same domain)
- Local testing → Option 3 (Self-signed)

**Do I need to change backend code?**
- Option 1 & 2: No changes needed
- Option 3: Just change startup command

**Will this fix CORS errors?**
- Yes! HTTPS + proper CORS = no more errors

---

**Last Updated:** 2025-11-02
**Backend Version:** 2.3.0
