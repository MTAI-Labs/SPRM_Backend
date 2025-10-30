# SPRM Backend - API Specification

## Base Information

- **Base URL**: `http://localhost:8000`
- **Protocol**: HTTP/HTTPS
- **Content-Type**: `application/json`
- **Character Encoding**: UTF-8

---

## 📡 Endpoints Summary

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | Get API information | No |
| GET | `/health` | Health check | No |
| GET | `/model-info` | Get model information | No |
| POST | `/classify` | Classify a case | No |
| POST | `/train` | Train classification model | No |
| POST | `/load-model` | Load pre-trained model | No |
| POST | `/search/similar` | Search similar cases | No |
| POST | `/search/load-cases` | Load cases from CSV | No |
| POST | `/search/add-case` | Add single case | No |
| GET | `/search/stats` | Get search statistics | No |

---

## 1. Classification Endpoints

### POST `/classify`

Classify a case description as CORRUPTION or NO CORRUPTION.

**Request Body:**
```json
{
  "text": "string (required)",
  "description_5": "string (optional)"
}
```

**Response 200:**
```json
{
  "classification": "CORRUPTION" | "NO CORRUPTION",
  "confidence": 87.43,
  "corruption_probability": 87.43,
  "no_corruption_probability": 12.57
}
```

**Response 503:**
```json
{
  "detail": "Classifier not ready. Please train the model first using POST /train"
}
```

**Response 500:**
```json
{
  "detail": "Classification error: {error_message}"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "pegawai kerajaan menerima rasuah daripada syarikat swasta",
    "description_5": "projek pembinaan bernilai RM 5 juta"
  }'
```

---

### POST `/train`

Train the corruption classification model.

**Request Body:**
```json
{
  "cris_path": "string (default: 'Data CMS/complaint_cris.csv')",
  "nfa_path": "string (default: 'Data CMS/complaint_nfa.csv')",
  "description_columns": ["description", "description_5"],
  "test_size": 0.2
}
```

**Response 200:**
```json
{
  "accuracy": 51.7,
  "auc_score": 0.51,
  "total_cases": 262249,
  "cris_cases": 63612,
  "nfa_cases": 198637,
  "confusion_matrix": [[matrix_data]]
}
```

**Response 404:**
```json
{
  "detail": "Data files not found: {error}. Please ensure CSV files are in the correct location."
}
```

**Response 500:**
```json
{
  "detail": "Training error: {error_message}"
}
```

---

### POST `/load-model`

Load a pre-trained classification model.

**Query Parameters:**
- `model_path` (string, default: "sprm_model.pkl"): Path to model file

**Response 200:**
```json
{
  "message": "Model loaded successfully",
  "model_path": "sprm_model.pkl"
}
```

**Response 404:**
```json
{
  "detail": "Model file not found: {model_path}"
}
```

---

## 2. Search Endpoints

### POST `/search/similar`

Search for cases similar to the provided description.

**Request Body:**
```json
{
  "description": "string (required)",
  "description_1": "string (optional)",
  "description_2": "string (optional)",
  "description_3": "string (optional)",
  "description_4": "string (optional)",
  "description_5": "string (optional)",
  "top_k": 5
}
```

**Response 200:**
```json
{
  "query_text": "combined query text",
  "total_matches": 5,
  "top_matches": [
    {
      "id": 12345,
      "description": "case description text",
      "similarity_score": 0.9234,
      "rank": 1
    }
  ]
}
```

**Response 503:**
```json
{
  "detail": "No cases loaded. Please load cases using POST /search/load-cases"
}
```

**Response 500:**
```json
{
  "detail": "Search error: {error_message}"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/search/similar" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "pegawai kerajaan menerima wang rasuah",
    "description_5": "projek pembinaan",
    "top_k": 5
  }'
```

---

### POST `/search/load-cases`

Load cases from CSV file into the search engine.

**Request Body:**
```json
{
  "csv_path": "string (required)",
  "max_cases": 5000 (optional)
}
```

**Response 200:**
```json
{
  "message": "Cases loaded successfully",
  "total_cases": 5000,
  "csv_path": "Data CMS/complaint_cris.csv"
}
```

**Response 404:**
```json
{
  "detail": "CSV file not found: {csv_path}"
}
```

**Response 500:**
```json
{
  "detail": "Error loading cases: {error_message}"
}
```

---

### POST `/search/add-case`

Add a single case to the search engine.

**Query Parameters:**
- `case_id` (integer, required): Unique case ID
- `description` (string, required): Main case description
- `description_1` (string, optional): Additional description 1
- `description_2` (string, optional): Additional description 2
- `description_3` (string, optional): Additional description 3
- `description_4` (string, optional): Additional description 4
- `description_5` (string, optional): Additional description 5

**Response 200:**
```json
{
  "message": "Case added successfully",
  "case_id": 999,
  "total_cases": 5001
}
```

**Response 500:**
```json
{
  "detail": "Error adding case: {error_message}"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/search/add-case?case_id=999&description=Test+case+description"
```

---

### GET `/search/stats`

Get search engine statistics.

**Response 200:**
```json
{
  "total_cases": 5000,
  "model_name": "all-MiniLM-L6-v2",
  "use_database": false,
  "embeddings_loaded": true
}
```

---

## 3. Utility Endpoints

### GET `/`

Get API information and available endpoints.

**Response 200:**
```json
{
  "message": "SPRM Corruption Classification & Case Search API",
  "status": "active",
  "endpoints": {
    "classify": "POST /classify - Classify a corruption case",
    "train": "POST /train - Train the classifier",
    "search": "POST /search/similar - Search for similar cases",
    "load_cases": "POST /search/load-cases - Load cases from CSV",
    "add_case": "POST /search/add-case - Add a single case",
    "search_stats": "GET /search/stats - Get search engine statistics",
    "health": "GET /health - Check API health",
    "model_info": "GET /model-info - Get model information"
  }
}
```

---

### GET `/health`

Health check endpoint to verify API status and model readiness.

**Response 200:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "classifier_trained": true,
  "gpu_available": false
}
```

---

### GET `/model-info`

Get information about the loaded models.

**Response 200:**
```json
{
  "model_name": "all-MiniLM-L6-v2",
  "batch_size": 512,
  "device": "cpu",
  "embedding_model_loaded": true,
  "classifier_trained": true
}
```

**Response 500:**
```json
{
  "detail": "Classifier not initialized"
}
```

---

## 📊 Data Models

### CaseRequest
```typescript
interface CaseRequest {
  text: string;              // Required
  description_5?: string;    // Optional
}
```

### ClassificationResponse
```typescript
interface ClassificationResponse {
  classification: "CORRUPTION" | "NO CORRUPTION";
  confidence: number;                    // 0-100
  corruption_probability: number;        // 0-100
  no_corruption_probability: number;     // 0-100
}
```

### SearchRequest
```typescript
interface SearchRequest {
  description: string;       // Required
  description_1?: string;    // Optional
  description_2?: string;    // Optional
  description_3?: string;    // Optional
  description_4?: string;    // Optional
  description_5?: string;    // Optional
  top_k?: number;           // Default: 5
}
```

### CaseMatch
```typescript
interface CaseMatch {
  id: number;
  description: string;
  similarity_score: number;  // 0-1
  rank: number;             // 1-based
}
```

### SearchResponse
```typescript
interface SearchResponse {
  query_text: string;
  total_matches: number;
  top_matches: CaseMatch[];
}
```

### TrainingRequest
```typescript
interface TrainingRequest {
  cris_path?: string;                    // Default: "Data CMS/complaint_cris.csv"
  nfa_path?: string;                     // Default: "Data CMS/complaint_nfa.csv"
  description_columns?: string[];        // Default: ["description", "description_5"]
  test_size?: number;                    // Default: 0.2
}
```

### TrainingResponse
```typescript
interface TrainingResponse {
  accuracy: number;
  auc_score: number;
  total_cases: number;
  cris_cases: number;
  nfa_cases: number;
  confusion_matrix: number[][];
}
```

---

## 🔐 Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input parameters |
| 404 | Not Found - Resource doesn't exist (file, model, etc.) |
| 500 | Internal Server Error - Server-side error |
| 503 | Service Unavailable - Model not loaded/trained |

---

## 📝 Notes for Frontend Developers

### 1. **CORS**
The API accepts requests from all origins by default. In production, configure allowed origins.

### 2. **Request Timeout**
- Classification requests may take 1-3 seconds
- Search requests typically take <1 second
- Training requests can take several minutes (use async/await)

### 3. **Rate Limiting**
Currently no rate limiting is implemented. Consider adding on frontend side for user experience.

### 4. **Caching**
Consider caching classification and search results on the frontend to reduce API calls.

### 5. **Error Handling**
Always implement proper error handling:
```javascript
try {
  const response = await fetch('/classify', {...});
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }
  const data = await response.json();
  // Handle success
} catch (error) {
  // Handle error
  console.error('API Error:', error.message);
}
```

---

## 🧪 Testing

### Postman Collection
Import the OpenAPI schema from: `http://localhost:8000/openapi.json`

### Sample Test Cases

**Classification Test:**
```json
{
  "text": "Pegawai kerajaan menerima rasuah sebanyak RM 50,000 daripada kontraktor untuk meluluskan projek pembinaan jambatan baharu. Kes ini melibatkan salah guna kuasa dan penyelewengan tender kerajaan."
}
```

Expected: `classification: "CORRUPTION"`, `confidence: >70%`

**Search Test:**
```json
{
  "description": "Penyelewengan dalam proses tender kerajaan melibatkan pegawai tinggi",
  "top_k": 3
}
```

Expected: 3 similar cases with `similarity_score > 0.5`

---

## 📞 Support

For API issues or questions:
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Check Logs**: View server console output

---

**Last Updated**: 2025-10-26
**API Version**: 1.0.0
