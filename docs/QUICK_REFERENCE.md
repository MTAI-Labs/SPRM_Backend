# 📋 SPRM Backend - Quick Reference Card

## 🚀 Start Server
```bash
python main.py
```
**URL**: http://localhost:8000

---

## 📡 Main API Endpoints

### 1. Classification
```bash
POST http://localhost:8000/classify
```
```json
{
  "text": "your case description"
}
```

### 2. Search Similar
```bash
POST http://localhost:8000/search/similar
```
```json
{
  "description": "your case description",
  "top_k": 5
}
```

### 3. Health Check
```bash
GET http://localhost:8000/health
```

---

## 💻 Command Line Usage

```bash
# Train model
python main.py --mode train

# Classify text
python main.py --mode predict --text "case description"

# Load cases
python main.py --mode load-cases --csv "path/to/file.csv"

# Search similar
python main.py --mode search --text "case description" --top-k 5

# Start API server
python main.py --mode api --port 8000
```

---

## 🔧 Python Code Usage

```python
from main import classify_text, search_similar, load_cases

# Classify
result = classify_text("pegawai menerima rasuah")
# Returns: {"classification": "CORRUPTION", "confidence": 87.43, ...}

# Search
results = search_similar("pegawai rasuah", top_k=5)
# Returns: [{"id": 123, "similarity_score": 0.92, ...}, ...]

# Load cases (one-time)
load_cases("Data CMS/complaint_cris.csv", max_cases=5000)
```

---

## 🌐 JavaScript/Frontend Usage

```javascript
// Classification
const response = await fetch('http://localhost:8000/classify', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ text: "case description" })
});
const result = await response.json();

// Search
const response = await fetch('http://localhost:8000/search/similar', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ description: "case description", top_k: 5 })
});
const results = await response.json();
```

---

## 📊 Response Formats

### Classification Response
```json
{
  "classification": "CORRUPTION" | "NO CORRUPTION",
  "confidence": 87.43,
  "corruption_probability": 87.43,
  "no_corruption_probability": 12.57
}
```

### Search Response
```json
{
  "query_text": "combined query",
  "total_matches": 5,
  "top_matches": [
    {
      "id": 12345,
      "description": "case text...",
      "similarity_score": 0.9234,
      "rank": 1
    }
  ]
}
```

---

## 🔍 Quick Tests

```bash
# Test health
curl http://localhost:8000/health

# Test classification
curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d '{"text":"pegawai menerima rasuah"}'

# Test search
curl -X POST http://localhost:8000/search/similar \
  -H "Content-Type: application/json" \
  -d '{"description":"pegawai rasuah","top_k":5}'
```

---

## 🐛 Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Check if server is running
curl http://localhost:8000/health

# View API documentation
open http://localhost:8000/docs

# Run with different port
python main.py --port 8001
```

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `main.py` | Main application |
| `README.md` | Main documentation |
| `FRONTEND_QUICKSTART.md` | Frontend guide |
| `API_SPECIFICATION.md` | API specs |
| `requirements.txt` | Dependencies |

---

## 🔐 Default Configuration

| Setting | Value |
|---------|-------|
| Host | 0.0.0.0 |
| Port | 8000 |
| Model | all-MiniLM-L6-v2 |
| Batch Size | 512 |
| Top-K Results | 5 |

---

## 📞 Quick Links

- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health**: http://localhost:8000/health
- **OpenAPI**: http://localhost:8000/openapi.json

---

## ⚡ Troubleshooting

| Problem | Solution |
|---------|----------|
| Model not trained | `python main.py --mode train` |
| No cases loaded | `python main.py --mode load-cases --csv "..."` |
| Port in use | `python main.py --port 8001` |
| Import error | `pip install -r requirements.txt` |

---

**📖 For detailed docs, see README.md**
