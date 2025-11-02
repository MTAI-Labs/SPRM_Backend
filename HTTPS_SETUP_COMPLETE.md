# HTTPS Setup Progress - Almost Done! 🎉

## ✅ What's Already Done

1. ✅ **Nginx installed** and configured
2. ✅ **Certbot installed** for SSL certificates
3. ✅ **Backend running** on port 8000
4. ✅ **Nginx reverse proxy** configured to forward requests to backend
5. ✅ **CORS fully open** - accepts all origins

## 🔧 What You Need to Do Next

### Step 1: Setup DNS (5 minutes)

You need to create a DNS A record for your backend API.

**Go to your DNS provider** (wherever you manage `sprm.mtailabs.ai`):

```
Type: A Record
Name: api.sprm.mtailabs.ai
Value: 192.168.120.110
TTL: 3600 (or Auto)
```

**Example for common DNS providers:**

**Cloudflare:**
1. Login to Cloudflare
2. Select domain: `mtailabs.ai`
3. DNS → Add record
4. Type: A, Name: `api.sprm`, IPv4: `192.168.120.110`
5. Proxy status: DNS only (gray cloud, not orange)
6. Save

**Other providers:** Similar process, just add A record pointing subdomain to server IP.

**Wait 5-10 minutes** for DNS propagation.

### Step 2: Verify DNS is Working

```bash
# Run this command after 5-10 minutes
ping api.sprm.mtailabs.ai

# Should show: 192.168.120.110
```

### Step 3: Get FREE SSL Certificate

Once DNS is working, run this ONE command:

```bash
sudo certbot --nginx -d api.sprm.mtailabs.ai
```

**It will ask:**
1. **Email**: Enter your email (for renewal notifications)
2. **Terms**: Type `Y` to agree
3. **Newsletter**: Type `N` (or Y if you want)

**Certbot will automatically:**
- ✅ Get SSL certificate from Let's Encrypt
- ✅ Configure nginx for HTTPS
- ✅ Set up auto-renewal
- ✅ Redirect HTTP to HTTPS

**Takes about 30 seconds!**

### Step 4: Update Frontend

Change your frontend API URL:

```javascript
// OLD ❌
const API_URL = 'http://192.168.120.110:8000';

// NEW ✅
const API_URL = 'https://api.sprm.mtailabs.ai';
```

Update in your `.env` file:
```bash
VITE_API_URL=https://api.sprm.mtailabs.ai
# or
REACT_APP_API_URL=https://api.sprm.mtailabs.ai
```

**Restart frontend** to apply changes.

### Step 5: Test

```bash
# Should return: {"status":"healthy",...}
curl https://api.sprm.mtailabs.ai/health
```

In browser console:
```javascript
fetch('https://api.sprm.mtailabs.ai/health')
  .then(r => r.json())
  .then(data => console.log('✅ HTTPS working:', data))
```

---

## 📋 Quick Reference

**Server IP:** `192.168.120.110`
**Backend API Domain:** `api.sprm.mtailabs.ai`
**Backend Port:** `8000` (local only, accessed via nginx)
**Nginx Config:** `/etc/nginx/sites-available/sprm-backend`

**Commands:**
```bash
# Restart nginx
sudo systemctl restart nginx

# Check nginx status
sudo systemctl status nginx

# View nginx logs
sudo tail -f /var/log/nginx/error.log

# Renew SSL certificate (auto-runs monthly, manual if needed)
sudo certbot renew
```

---

## 🐛 Troubleshooting

### Issue: DNS not resolving

**Wait 5-10 minutes** after adding DNS record. Some DNS providers take longer.

**Check DNS:**
```bash
nslookup api.sprm.mtailabs.ai
# Should show: 192.168.120.110
```

### Issue: Certbot fails with "connection refused"

**Make sure:**
1. DNS is resolving correctly
2. Port 80 is open: `sudo ufw allow 80`
3. Port 443 is open: `sudo ufw allow 443`
4. Nginx is running: `sudo systemctl status nginx`

### Issue: Frontend still getting CORS errors

**Already fixed!** CORS is fully open in backend. Just make sure you're using HTTPS URL.

### Issue: 502 Bad Gateway

**Backend not running.** Start it:
```bash
cd /home/kiesun/SPRM_Backend
source sprm_backend/bin/activate  # If using venv
python src/main.py
```

---

## 🎯 Summary

**Right now:**
- ✅ Backend runs on: `http://localhost:8000`
- ✅ Nginx proxies it to: `http://api.sprm.mtailabs.ai:80`
- ❌ No SSL yet (need DNS first)

**After you complete the steps:**
- ✅ Frontend: `https://sprm.mtailabs.ai`
- ✅ Backend: `https://api.sprm.mtailabs.ai`
- ✅ No more mixed content errors!
- ✅ Free SSL certificate with auto-renewal!

---

## 📞 Next Steps

1. **Setup DNS** (A record for `api.sprm.mtailabs.ai`)
2. **Wait 5-10 minutes**
3. **Run certbot**: `sudo certbot --nginx -d api.sprm.mtailabs.ai`
4. **Update frontend** to use `https://api.sprm.mtailabs.ai`
5. **Test** and celebrate! 🎉

**Estimated total time:** 15-20 minutes (mostly waiting for DNS)

---

**Questions?** Read `/home/kiesun/SPRM_Backend/docs/HTTPS_SETUP_GUIDE.md` for detailed troubleshooting.

**Last Updated:** 2025-11-02
