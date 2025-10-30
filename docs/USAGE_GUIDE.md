# SPRM Backend - Complete Usage Guide

This system integrates **SPRM Corruption Classification** and **Case Search** functionality.

## 🚀 Quick Start

### Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 📋 Available Modes

### 1. **API Mode** (Default - FastAPI Server)
```bash
python main.py
# or
python main.py --mode api --host 0.0.0.0 --port 8000
```

Access the API at: `http://localhost:8000`
- Swagger Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

### 2. **Train Mode** (Train Corruption Classifier)
```bash
python main.py --mode train
```

This will:
- Load CRIS (corruption) and NFA (no corruption) data
- Train the classification model
- Save to `sprm_model.pkl`

---

### 3. **Predict Mode** (Classify Text)
```bash
python main.py --mode predict --text "pegawai kerajaan menerima rasuah"
```

Output:
```
📊 CLASSIFICATION RESULTS:
✅ Classification: CORRUPTION
✅ Confidence: 87.43%
✅ Corruption Probability: 87.43%
✅ No Corruption Probability: 12.57%
```

---

### 4. **Load Cases Mode** (Load Cases for Search)
```bash
# Load all cases
python main.py --mode load-cases --csv "Data CMS/complaint_cris.csv"

# Load limited cases (faster for testing)
python main.py --mode load-cases --csv "Data CMS/complaint_cris.csv" --max-cases 1000
```

---

### 5. **Search Mode** (Find Similar Cases)
```bash
python main.py --mode search --text "pegawai menerima wang rasuah" --top-k 5
```

Output:
```
📊 SEARCH RESULTS:
🏆 Rank 1
   ID: 12345
   Similarity: 0.9234
   Description: Pegawai kerajaan didakwa menerima...
```

---

## 🔌 API Endpoints

### Classification Endpoints

#### POST `/classify` - Classify a Case
```bash
curl -X POST "http://localhost:8000/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "pegawai kerajaan menerima rasuah",
    "description_5": "projek pembinaan bernilai RM 5 juta"
  }'
```

#### POST `/train` - Train the Classifier
```bash
curl -X POST "http://localhost:8000/train" \
  -H "Content-Type: application/json" \
  -d '{
    "cris_path": "Data CMS/complaint_cris.csv",
    "nfa_path": "Data CMS/complaint_nfa.csv"
  }'
```

---

### Search Endpoints

#### POST `/search/similar` - Search Similar Cases
```bash
curl -X POST "http://localhost:8000/search/similar" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "pegawai menerima wang rasuah",
    "description_5": "projek pembinaan",
    "top_k": 5
  }'
```

#### POST `/search/load-cases` - Load Cases from CSV
```bash
curl -X POST "http://localhost:8000/search/load-cases" \
  -H "Content-Type: application/json" \
  -d '{
    "csv_path": "Data CMS/complaint_cris.csv",
    "max_cases": 1000
  }'
```

#### POST `/search/add-case` - Add a Single Case
```bash
curl -X POST "http://localhost:8000/search/add-case?case_id=999&description=Test+case"
```

#### GET `/search/stats` - Get Search Engine Statistics
```bash
curl "http://localhost:8000/search/stats"
```

---

### Utility Endpoints

#### GET `/health` - Health Check
```bash
curl "http://localhost:8000/health"
```

#### GET `/model-info` - Model Information
```bash
curl "http://localhost:8000/model-info"
```

---

## 💻 Python Code Usage

### Example 1: Classification
```python
from main import classify_text, train_model

# Train the model (only need once)
results = train_model()
print(f"Accuracy: {results['accuracy']:.2f}%")

# Classify text
result = classify_text("pegawai kerajaan menerima rasuah")
print(f"Classification: {result['classification']}")
print(f"Confidence: {result['confidence']:.2f}%")
```

### Example 2: Search Similar Cases
```python
from main import load_cases, search_similar

# Load cases from CSV (only need once)
num_cases = load_cases("Data CMS/complaint_cris.csv", max_cases=1000)
print(f"Loaded {num_cases} cases")

# Search for similar cases
results = search_similar(
    description="pegawai menerima wang rasuah",
    top_k=5
)

for result in results:
    print(f"Rank {result['rank']}: {result['description'][:100]}...")
    print(f"Similarity: {result['similarity_score']:.4f}\n")
```

### Example 3: Combined Usage
```python
from main import classify_text, search_similar

# First, classify the case
classification = classify_text("pegawai kerajaan menerima wang haram")
print(f"Classification: {classification['classification']}")

# If it's corruption, search for similar cases
if classification['classification'] == 'CORRUPTION':
    similar_cases = search_similar("pegawai kerajaan menerima wang haram", top_k=3)
    print(f"\nFound {len(similar_cases)} similar cases:")
    for case in similar_cases:
        print(f"  - Case {case['id']}: {case['similarity_score']:.2f}")
```

---

## 📁 Project Structure

```
SPRM_Backend/
├── main.py                      # Main FastAPI application
├── SPRM Classification.py       # SPRM classifier module
├── search_relevant_case.py      # Case search engine module
├── requirements.txt             # Python dependencies
├── example_usage.py             # Usage examples
├── USAGE_GUIDE.md              # This guide
│
├── Data CMS/                    # Data folder (create this)
│   ├── complaint_cris.csv      # Corruption cases
│   └── complaint_nfa.csv       # No further action cases
│
└── Generated Files/
    ├── sprm_model.pkl          # Trained classification model
    └── case_search_engine.pkl  # Loaded search engine
```

---

## 🎯 Common Workflows

### Workflow 1: First-Time Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Train classification model
python main.py --mode train

# 3. Load cases for search
python main.py --mode load-cases --csv "Data CMS/complaint_cris.csv" --max-cases 5000

# 4. Start API server
python main.py --mode api
```

### Workflow 2: Testing Classification
```bash
# Test single prediction
python main.py --mode predict --text "pegawai menerima rasuah untuk kelulusan projek"
```

### Workflow 3: Testing Search
```bash
# Load some cases first
python main.py --mode load-cases --csv "Data CMS/complaint_cris.csv" --max-cases 100

# Search for similar cases
python main.py --mode search --text "penyelewengan tender kerajaan" --top-k 5
```

---

## ⚙️ Configuration

### Change Embedding Model
Edit the model name in `SPRM Classification.py` or `search_relevant_case.py`:
```python
SPRMClassifier(model_name='all-MiniLM-L6-v2')  # Default
# or
SPRMClassifier(model_name='paraphrase-MiniLM-L6-v2')  # Alternative
```

### Database Mode (Optional)
To use PostgreSQL instead of in-memory search:
```python
from search_relevant_case import CaseSearchEngine

engine = CaseSearchEngine(
    use_database=True,
    db_config={
        "host": "localhost",
        "port": 5432,
        "database": "postgres",
        "user": "postgres",
        "password": "your_password"
    }
)
```

---

## 🐛 Troubleshooting

### Issue: "Model not trained"
**Solution**: Train the model first
```bash
python main.py --mode train
```

### Issue: "No cases loaded"
**Solution**: Load cases from CSV
```bash
python main.py --mode load-cases --csv "Data CMS/complaint_cris.csv"
```

### Issue: "GPU not available"
**Solution**: The system will automatically fall back to CPU. To use GPU:
- Install CUDA-enabled PyTorch
- Ensure NVIDIA drivers are installed

---

## 📊 Performance Tips

1. **For Faster Search**: Load fewer cases initially
   ```bash
   --max-cases 1000
   ```

2. **For Better Classification**: Use full dataset for training
   ```bash
   python main.py --mode train  # Uses all data
   ```

3. **For Production**: Use GPU acceleration if available

---

## 🔐 Security Notes

- Set proper `POSTGRES_PASSWORD` environment variable for database mode
- Restrict API access in production (use authentication middleware)
- Don't expose sensitive data in API responses

---

## 📞 Support

For issues or questions:
1. Check the `/docs` endpoint for API documentation
2. Review the `example_usage.py` file
3. Check log output for error details
