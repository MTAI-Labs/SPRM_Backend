# SPRM Backend - Project Structure

## 📁 Directory Structure

```
SPRM_Backend/
│
├── 📄 main.py                          # Main FastAPI application entry point
├── 📄 SPRM Classification.py           # Corruption classification module
├── 📄 search_relevant_case.py          # Case search engine module
├── 📄 example_usage.py                 # Python usage examples
├── 📄 Text.py                          # (Legacy file - can be removed)
│
├── 📋 requirements.txt                 # Python package dependencies
├── 📋 README.md                        # Main documentation for frontend team
├── 📋 API_SPECIFICATION.md             # Detailed API specification
├── 📋 USAGE_GUIDE.md                  # Detailed usage guide
├── 📋 PROJECT_STRUCTURE.md            # This file
│
├── 📂 Data CMS/                        # Data directory (create this)
│   ├── complaint_cris.csv             # Corruption cases dataset
│   └── complaint_nfa.csv              # No further action cases dataset
│
├── 📂 Generated Files/                 # Auto-generated files (gitignore these)
│   ├── sprm_model.pkl                 # Trained classification model
│   └── case_search_engine.pkl         # Loaded search engine with embeddings
│
├── 📂 .git/                            # Git repository
├── 📂 .github/                         # GitHub configuration
└── 📂 venv/                            # Python virtual environment (gitignore)
```

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                       │
│                          (main.py)                               │
└────────────┬────────────────────────────────────┬────────────────┘
             │                                    │
             │                                    │
    ┌────────▼─────────┐                ┌────────▼──────────┐
    │  Classification  │                │   Search Engine   │
    │     Module       │                │      Module       │
    │                  │                │                   │
    │ SPRM             │                │ search_relevant_  │
    │ Classification.py│                │ case.py           │
    └────────┬─────────┘                └────────┬──────────┘
             │                                    │
             │                                    │
    ┌────────▼─────────┐                ┌────────▼──────────┐
    │ SentenceTransformer               │ SentenceTransformer│
    │ + Logistic        │                │ + Cosine Similarity│
    │ Regression        │                │                   │
    └───────────────────┘                └───────────────────┘
```

---

## 📦 Core Modules

### 1. **main.py** - FastAPI Application
**Purpose**: Main application entry point and API endpoint definitions

**Key Components**:
- FastAPI app initialization
- API endpoints (classify, search, health, etc.)
- Request/Response models (Pydantic)
- Global instances management
- Command-line interface

**Dependencies**:
- FastAPI, Uvicorn, Pydantic
- SPRM Classification module
- Search Relevant Case module

**Endpoints Defined**:
```python
GET  /                  # API information
GET  /health            # Health check
GET  /model-info        # Model information
POST /classify          # Classify case
POST /train             # Train classifier
POST /load-model        # Load model
POST /search/similar    # Search similar cases
POST /search/load-cases # Load cases
POST /search/add-case   # Add single case
GET  /search/stats      # Search statistics
```

---

### 2. **SPRM Classification.py** - Corruption Classifier
**Purpose**: AI-powered corruption case classification

**Key Components**:
```python
class SPRMClassifier:
    - __init__()           # Initialize classifier
    - load_model()         # Load embedding model
    - clean_text()         # Text preprocessing
    - predict()            # Classify single case
    - train()              # Train on dataset
    - save()               # Save model
    - load_classifier()    # Load saved model
```

**Machine Learning Pipeline**:
1. Text cleaning and preprocessing
2. SentenceTransformer embeddings (all-MiniLM-L6-v2)
3. Logistic Regression classifier with balanced weights
4. Binary classification: CORRUPTION vs NO CORRUPTION

**Input**: Case description text
**Output**: Classification + confidence scores

---

### 3. **search_relevant_case.py** - Case Search Engine
**Purpose**: Semantic search for finding similar cases

**Key Components**:
```python
class CaseSearchEngine:
    - __init__()              # Initialize search engine
    - load_model()            # Load embedding model
    - combine_descriptions()  # Combine description fields
    - generate_embedding()    # Create text embedding
    - add_case()              # Add case to index
    - load_cases_from_csv()   # Bulk load from CSV
    - search()                # Search similar cases
    - save()                  # Save search index
    - load()                  # Load search index
```

**Search Pipeline**:
1. Text embedding generation (SentenceTransformer)
2. Cosine similarity calculation
3. Top-K ranking of similar cases
4. Return ranked results

**Storage Modes**:
- In-memory (default): Fast, no database required
- PostgreSQL (optional): Persistent storage

---

## 🔄 Data Flow

### Classification Flow
```
User Input (text)
    │
    ▼
[Clean Text] → [Generate Embedding] → [Logistic Regression]
    │
    ▼
Classification Result
(CORRUPTION / NO CORRUPTION + confidence)
```

### Search Flow
```
User Query (description)
    │
    ▼
[Combine Descriptions] → [Generate Embedding]
    │
    ▼
[Calculate Cosine Similarity with All Cases]
    │
    ▼
[Rank by Similarity] → [Return Top-K Results]
    │
    ▼
Similar Cases (ranked list)
```

---

## 🗄️ Data Models

### Database Schema (Optional - PostgreSQL)

```sql
-- complaints table
CREATE TABLE complaints (
    id SERIAL PRIMARY KEY,
    reference_number VARCHAR(255),
    title TEXT,
    description TEXT,
    description_1 TEXT,
    description_2 TEXT,
    description_3 TEXT,
    description_4 TEXT,
    description_5 TEXT,
    complainer_id INTEGER,
    source_id INTEGER,
    status_id INTEGER,
    embeddings_array REAL[],
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- complaint_references table
CREATE TABLE complaint_references (
    id SERIAL PRIMARY KEY,
    complaint_id INTEGER REFERENCES complaints(id),
    reference_complaint_id INTEGER REFERENCES complaints(id),
    description TEXT,
    embeddings_array REAL[],
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### File Storage (Default)

**sprm_model.pkl** (Pickle Format):
```python
{
    'classifier': LogisticRegression object,
    # Saved by scikit-learn's pickle
}
```

**case_search_engine.pkl** (Pickle Format):
```python
{
    'model_name': 'all-MiniLM-L6-v2',
    'cases': [
        {
            'id': int,
            'description': str,
            'combined_text': str,
            'embedding': numpy.ndarray
        },
        ...
    ],
    'embeddings_matrix': numpy.ndarray  # Shape: (n_cases, 384)
}
```

---

## 🔧 Configuration

### Environment Variables (Optional)
```bash
# Database configuration (if using PostgreSQL)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# API configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### Model Configuration
```python
# In SPRM Classification.py
SPRMClassifier(
    model_name='all-MiniLM-L6-v2',  # SentenceTransformer model
    batch_size=512                   # Batch size for embeddings
)

# In search_relevant_case.py
CaseSearchEngine(
    model_name='all-MiniLM-L6-v2',  # SentenceTransformer model
    use_database=False,              # Use in-memory or PostgreSQL
    db_config={}                     # Database config if use_database=True
)
```

---

## 🚀 Startup Sequence

### When `python main.py` is run:

1. **Import Modules**
   - Load FastAPI and dependencies
   - Import SPRM Classification module
   - Import Search Relevant Case module

2. **Initialize FastAPI App**
   - Create FastAPI instance
   - Define API routes

3. **Startup Event** (`@app.on_event("startup")`)
   - Initialize SPRM Classifier
   - Load pre-trained model if exists (sprm_model.pkl)
   - Initialize Case Search Engine
   - Load search index if exists (case_search_engine.pkl)

4. **Start Uvicorn Server**
   - Listen on specified host:port
   - Enable hot-reload in development mode
   - Serve API endpoints

---

## 📊 Performance Characteristics

### Memory Usage
- **Base Application**: ~200 MB
- **Classification Model**: ~100 MB
- **Search Engine**: ~500 MB per 10,000 cases (with embeddings)
- **Total (Typical)**: ~1-2 GB RAM

### Processing Speed
- **Classification**: 0.5-2 seconds per request
- **Search**: 0.1-1 second per query (depending on corpus size)
- **Training**: 5-10 minutes for 250K cases
- **Loading Cases**: ~1-2 seconds per 1000 cases

### Scalability
- **Concurrent Requests**: Supports multiple workers
- **Max Cases (In-Memory)**: ~50,000 cases recommended
- **Database Mode**: Unlimited (limited by PostgreSQL)

---

## 🔐 Security Considerations

### Current Implementation
- ✅ Input validation (Pydantic models)
- ✅ Error handling
- ❌ No authentication/authorization
- ❌ No rate limiting
- ❌ No CORS restrictions

### Recommended for Production
```python
# Add to main.py

# 1. CORS Configuration
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Rate Limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/classify")
@limiter.limit("10/minute")
async def classify_case(request: Request, ...):
    ...

# 3. API Key Authentication
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

@app.post("/classify")
async def classify_case(api_key: str = Depends(api_key_header)):
    if api_key != "your-secret-key":
        raise HTTPException(status_code=401, detail="Invalid API Key")
    ...
```

---

## 🧪 Testing Structure

### Unit Tests (Recommended)
```python
# tests/test_classification.py
def test_classifier_initialization()
def test_text_cleaning()
def test_prediction()
def test_training()

# tests/test_search.py
def test_search_engine_initialization()
def test_embedding_generation()
def test_search_similarity()
def test_case_loading()

# tests/test_api.py
def test_health_endpoint()
def test_classify_endpoint()
def test_search_endpoint()
```

---

## 📚 Dependencies Overview

### Core Dependencies
```
fastapi==0.104.1           # Web framework
uvicorn[standard]==0.24.0  # ASGI server
pydantic==2.5.0            # Data validation
```

### Machine Learning
```
torch>=2.4.0               # PyTorch framework
sentence-transformers>=2.2.0  # Embeddings
scikit-learn>=1.3.0        # ML algorithms
numpy>=1.24.0              # Numerical computing
pandas>=2.0.0              # Data manipulation
```

### Optional
```
psycopg2-binary>=2.9.0     # PostgreSQL driver
requests>=2.31.0           # HTTP client
matplotlib>=3.7.0          # Plotting (for training)
```

---

## 🔄 Deployment Options

### Option 1: Traditional Server
```bash
# Install dependencies
pip install -r requirements.txt

# Run with Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Option 2: Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Option 3: Cloud (AWS Lambda, Google Cloud Run, etc.)
- Package application with dependencies
- Use serverless FastAPI adapter
- Configure API Gateway

---

## 📝 Development Workflow

### Local Development
```bash
# 1. Clone repository
git clone <repo-url>

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run development server
python main.py  # Auto-reload enabled
```

### Making Changes
1. Edit code in respective modules
2. Test using Swagger UI (http://localhost:8000/docs)
3. Run manual tests
4. Commit changes

---

## 🎯 Integration Points for Frontend

### Key Integration Points
1. **API Base URL**: Configure in frontend environment
2. **WebSocket** (Future): Real-time updates
3. **File Upload** (Future): Direct CSV upload
4. **Batch Processing** (Future): Multiple case classification

### Recommended Frontend Structure
```
frontend/
├── src/
│   ├── api/
│   │   ├── client.js          # API client configuration
│   │   ├── classification.js  # Classification API calls
│   │   └── search.js          # Search API calls
│   ├── components/
│   │   ├── ClassificationForm.jsx
│   │   └── SearchForm.jsx
│   └── utils/
│       └── errorHandler.js    # API error handling
```

---

## 📞 Support & Maintenance

### Logs Location
- **Console**: Standard output (stdout)
- **Error Logs**: Standard error (stderr)
- **Custom Logging**: Configure in Python logging module

### Monitoring Endpoints
- `/health` - Basic health check
- `/model-info` - Model status
- `/search/stats` - Search engine statistics

### Backup Strategy
1. **Models**: Backup `*.pkl` files regularly
2. **Data**: Backup `Data CMS/` directory
3. **Configuration**: Version control for code

---

**Last Updated**: 2025-10-26
**Project Version**: 1.0.0
