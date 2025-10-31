from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
import uvicorn
import os
import sys
import shutil
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import SPRM Classifier
from sprm_classification import SPRMClassifier

# Import Search Relevant Case Engine
from search_relevant_case import CaseSearchEngine

# Import Database and Services
from database import db
from complaint_service import ComplaintService
from openrouter_service import OpenRouterService
from classification_service import ClassificationService
from case_service import CaseService
from analytics_service import AnalyticsService
from models import ComplaintSubmission, ComplaintResponse, ComplaintDetail, ComplaintEvaluation, EvaluationOptions, OfficerReview

# Initialize FastAPI app
app = FastAPI(
    title="SPRM Corruption Classification API",
    description="Malaysian Anti-Corruption Commission (SPRM) AI-Powered Case Classifier API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Mount uploads directory as static files for frontend access
# Frontend can access files via: http://localhost:8000/uploads/filename
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Thread pool for background processing
# max_workers=1 means sequential processing (one complaint at a time)
# Increase to 3-5 if you want concurrent processing in the future
executor = ThreadPoolExecutor(max_workers=5)

# Global instances
classifier: Optional[SPRMClassifier] = None
search_engine: Optional[CaseSearchEngine] = None
vllm_service: Optional[OpenRouterService] = None
classification_service: Optional[ClassificationService] = None
case_service: Optional[CaseService] = None
complaint_service: Optional[ComplaintService] = None
analytics_service: Optional[AnalyticsService] = None


def get_classifier():
    """Get or initialize the global classifier instance"""
    global classifier
    if classifier is None:
        print("🚀 Initializing SPRM Classifier...")
        classifier = SPRMClassifier()

        # Try to load pre-trained model if it exists
        if os.path.exists("sprm_model.pkl"):
            try:
                classifier.load_model()
                classifier.load_classifier("sprm_model.pkl")
                print("✅ Pre-trained model loaded successfully!")
            except Exception as e:
                print(f"⚠️  Could not load pre-trained model: {e}")
    return classifier


def get_search_engine():
    """Get or initialize the global search engine instance"""
    global search_engine
    if search_engine is None:
        print("🚀 Initializing Case Search Engine...")

        # Use database mode for persistent embeddings
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'sprm_db'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres')
        }

        search_engine = CaseSearchEngine(
            model_name='all-MiniLM-L6-v2',
            use_database=True,
            db_config=db_config
        )
        search_engine.load_model()
        print("✅ Search engine initialized (database mode)")
    return search_engine


def get_vllm_service():
    """Get or initialize the global VLLM/OpenRouter service instance"""
    global vllm_service
    if vllm_service is None:
        print("🚀 Initializing OpenRouter Service...")
        vllm_service = OpenRouterService()
        if vllm_service.api_key:
            print(f"✅ OpenRouter Service initialized (Model: {vllm_service.model})")
        else:
            print("⚠️  OpenRouter API key not configured")
    return vllm_service


def get_classification_service():
    """Get or initialize the global classification service instance"""
    global classification_service
    if classification_service is None:
        print("🚀 Initializing Classification Service...")
        openrouter = get_vllm_service()
        classification_service = ClassificationService(openrouter_service=openrouter)
        print(f"✅ Classification Service initialized (threshold: {classification_service.threshold})")
    return classification_service


def get_case_service():
    """Get or initialize the global case service instance"""
    global case_service
    if case_service is None:
        print("🚀 Initializing Case Service...")
        se = get_search_engine()
        case_service = CaseService(search_engine=se)
        print(f"✅ Case Service initialized (auto-group threshold: {case_service.min_similarity_for_auto_group})")
    return case_service


def get_complaint_service():
    """Get or initialize the global complaint service instance"""
    global complaint_service
    if complaint_service is None:
        clf = get_classifier()
        se = get_search_engine()
        vllm = get_vllm_service()
        classification_svc = get_classification_service()
        case_svc = get_case_service()
        complaint_service = ComplaintService(
            classifier=clf,
            search_engine=se,
            vllm_service=vllm,
            classification_service=classification_svc,
            case_service=case_svc
        )
    return complaint_service


def get_analytics_service():
    """Get or initialize the global analytics service instance"""
    global analytics_service
    if analytics_service is None:
        print("🚀 Initializing Analytics Service...")
        vllm = get_vllm_service()
        analytics_service = AnalyticsService(openrouter_service=vllm)
        print("✅ Analytics Service initialized")
    return analytics_service


class CaseRequest(BaseModel):
    """Request model for corruption classification"""
    text: str
    description_5: Optional[str] = None


class ClassificationResponse(BaseModel):
    """Response model for corruption classification"""
    classification: str
    confidence: float
    corruption_probability: float
    no_corruption_probability: float


class TrainingRequest(BaseModel):
    """Request model for training the classifier"""
    cris_path: str = "Data CMS/complaint_cris.csv"
    nfa_path: str = "Data CMS/complaint_nfa.csv"
    description_columns: list = ['description', 'description_5']
    test_size: float = 0.2


class TrainingResponse(BaseModel):
    """Response model for training results"""
    accuracy: float
    auc_score: float
    total_cases: int
    cris_cases: int
    nfa_cases: int
    confusion_matrix: list


class SearchRequest(BaseModel):
    """Request model for case similarity search"""
    description: str
    description_1: Optional[str] = None
    description_2: Optional[str] = None
    description_3: Optional[str] = None
    description_4: Optional[str] = None
    description_5: Optional[str] = None
    top_k: int = 5


class CaseMatch(BaseModel):
    """Model for a similar case match"""
    id: int
    description: str
    similarity_score: float
    rank: int


class SearchResponse(BaseModel):
    """Response model for search results"""
    query_text: str
    total_matches: int
    top_matches: list[CaseMatch]


class LoadCasesRequest(BaseModel):
    """Request model for loading cases from CSV"""
    csv_path: str
    max_cases: Optional[int] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the classifier, search engine, VLLM service, and database on startup"""
    # Initialize database tables
    try:
        db.create_tables()
    except Exception as e:
        print(f"⚠️  Database initialization failed: {e}")
        print("💡 Make sure PostgreSQL is running and environment variables are set")

    # Initialize services
    get_vllm_service()
    get_classification_service()
    get_case_service()
    get_complaint_service()

    # Optional: Initialize classifier and search engine (for backward compatibility)
    get_classifier()
    get_search_engine()

    if classifier and not classifier.classifier:
        print("💡 Classification model not trained (optional feature)")
    if search_engine and not search_engine.cases:
        print("💡 Search engine has no cases loaded (optional feature)")

    print("\n" + "="*60)
    print("🚀 SPRM Backend API Ready!")
    print("="*60)
    print("📝 Complaint submission: POST /complaints/submit")
    print("🔍 View complaint: GET /complaints/{id}")
    print("📋 List complaints: GET /complaints")
    print("📚 API Docs: http://localhost:8000/docs")
    print("="*60 + "\n")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
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


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global classifier

    model_loaded = classifier is not None and classifier.embedding_model is not None
    classifier_trained = classifier is not None and classifier.classifier is not None

    return {
        "status": "healthy",
        "model_loaded": model_loaded,
        "classifier_trained": classifier_trained,
        "gpu_available": classifier.device.type == "cuda" if classifier else False
    }


@app.get("/model-info")
async def model_info():
    """Get model information"""
    global classifier

    if classifier is None:
        raise HTTPException(status_code=500, detail="Classifier not initialized")

    return {
        "model_name": classifier.model_name,
        "batch_size": classifier.batch_size,
        "device": str(classifier.device),
        "embedding_model_loaded": classifier.embedding_model is not None,
        "classifier_trained": classifier.classifier is not None
    }


@app.post("/classify", response_model=ClassificationResponse)
async def classify_case(request: CaseRequest):
    """
    Classify a corruption case

    Args:
        request: CaseRequest containing case description

    Returns:
        ClassificationResponse with prediction results
    """
    global classifier

    if classifier is None or classifier.classifier is None:
        raise HTTPException(
            status_code=503,
            detail="Classifier not ready. Please train the model first using POST /train"
        )

    try:
        # Combine text fields if description_5 is provided
        combined_text = request.text
        if request.description_5:
            combined_text = f"{request.text} {request.description_5}"

        # Make prediction
        result = classifier.predict(combined_text)

        return ClassificationResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification error: {str(e)}")


@app.post("/train", response_model=TrainingResponse)
async def train_classifier(request: TrainingRequest):
    """
    Train the SPRM classifier

    Args:
        request: TrainingRequest with training configuration

    Returns:
        TrainingResponse with training results
    """
    global classifier

    if classifier is None:
        classifier = SPRMClassifier()

    try:
        # Train the model
        results = classifier.train(
            cris_path=request.cris_path,
            nfa_path=request.nfa_path,
            description_columns=request.description_columns,
            test_size=request.test_size
        )

        # Save the trained model
        classifier.save("sprm_model.pkl")

        return TrainingResponse(**results)

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Data files not found: {str(e)}. Please ensure CSV files are in the correct location."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training error: {str(e)}")


@app.post("/load-model")
async def load_model(model_path: str = "sprm_model.pkl"):
    """
    Load a pre-trained model

    Args:
        model_path: Path to the saved model file

    Returns:
        Success message
    """
    global classifier

    if classifier is None:
        classifier = SPRMClassifier()

    try:
        if not os.path.exists(model_path):
            raise HTTPException(status_code=404, detail=f"Model file not found: {model_path}")

        classifier.load_model()
        classifier.load_classifier(model_path)

        return {
            "message": "Model loaded successfully",
            "model_path": model_path
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading model: {str(e)}")


# ============================================================================
# SEARCH RELEVANT CASE ENDPOINTS
# ============================================================================

@app.post("/search/similar", response_model=SearchResponse)
async def search_similar_cases(request: SearchRequest):
    """
    Search for similar cases using semantic similarity

    Args:
        request: SearchRequest with case descriptions

    Returns:
        SearchResponse with similar cases
    """
    global search_engine

    engine = get_search_engine()

    if not engine.cases:
        raise HTTPException(
            status_code=503,
            detail="No cases loaded. Please load cases using POST /search/load-cases"
        )

    try:
        # Prepare query description
        query_desc = {
            'description': request.description,
            'description_1': request.description_1,
            'description_2': request.description_2,
            'description_3': request.description_3,
            'description_4': request.description_4,
            'description_5': request.description_5
        }

        # Search for similar cases
        results = engine.search(query_description=query_desc, top_k=request.top_k)

        # Build query text
        query_text = engine.combine_descriptions(**query_desc)

        # Format matches
        matches = [
            CaseMatch(
                id=result['id'],
                description=result.get('description', result.get('combined_text', '')),
                similarity_score=result['similarity_score'],
                rank=result['rank']
            )
            for result in results
        ]

        return SearchResponse(
            query_text=query_text,
            total_matches=len(matches),
            top_matches=matches
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@app.post("/search/load-cases")
async def load_cases_from_csv(request: LoadCasesRequest):
    """
    Load cases from CSV file into search engine

    Args:
        request: LoadCasesRequest with CSV path and options

    Returns:
        Success message with number of cases loaded
    """
    global search_engine

    engine = get_search_engine()

    try:
        if not os.path.exists(request.csv_path):
            raise HTTPException(status_code=404, detail=f"CSV file not found: {request.csv_path}")

        # Load cases
        num_cases = engine.load_cases_from_csv(
            csv_path=request.csv_path,
            max_cases=request.max_cases
        )

        # Save search engine
        engine.save("case_search_engine.pkl")

        return {
            "message": "Cases loaded successfully",
            "total_cases": num_cases,
            "csv_path": request.csv_path
        }

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"CSV file not found: {request.csv_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading cases: {str(e)}")


@app.post("/search/add-case")
async def add_case(case_id: int, description: str, description_1: Optional[str] = None,
                  description_2: Optional[str] = None, description_3: Optional[str] = None,
                  description_4: Optional[str] = None, description_5: Optional[str] = None):
    """
    Add a single case to the search engine

    Args:
        case_id: Unique case ID
        description: Main case description
        description_1 to description_5: Additional descriptions

    Returns:
        Success message
    """
    global search_engine

    engine = get_search_engine()

    try:
        engine.add_case(
            case_id=case_id,
            description=description,
            description_1=description_1,
            description_2=description_2,
            description_3=description_3,
            description_4=description_4,
            description_5=description_5
        )

        # Save search engine
        engine.save("case_search_engine.pkl")

        return {
            "message": "Case added successfully",
            "case_id": case_id,
            "total_cases": len(engine.cases)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding case: {str(e)}")


@app.get("/search/stats")
async def get_search_stats():
    """Get search engine statistics"""
    global search_engine

    engine = get_search_engine()

    return {
        "total_cases": len(engine.cases),
        "model_name": engine.model_name,
        "use_database": engine.use_database,
        "embeddings_loaded": engine.embeddings_matrix is not None
    }


# ============================================================================
# COMPLAINT SUBMISSION & PROCESSING ENDPOINTS
# ============================================================================

def process_complaint_sync(complaint_id: int, service: ComplaintService):
    """
    Synchronous processing function that runs in thread pool
    This allows multiple complaints to be processed simultaneously
    """
    try:
        print(f"🔄 Starting background processing for complaint {complaint_id}")

        # Use new VLLM processing pipeline
        result = service.process_complaint_new(complaint_id)
        print(f"✅ Background processing completed for complaint {complaint_id}")

        # Handle extraction results
        if result.get('extracted_data'):
            print(f"   ✓ Data extracted via VLLM")
        else:
            print(f"   ✗ Data extraction not available")

        # Handle 5W1H summary
        if result.get('w1h_summary'):
            print(f"   ✓ 5W1H summary generated")
            # Print first 100 chars of summary
            summary_preview = result['w1h_summary'][:100] + "..." if len(result.get('w1h_summary', '')) > 100 else result.get('w1h_summary', '')
            print(f"   Summary preview: {summary_preview}")
        else:
            print(f"   ✗ 5W1H summary not generated")

        print(f"   Final status: {result.get('status', 'unknown')}")

        # Update pre-computed analytics tables
        try:
            from simple_analytics import update_analytics_for_complaint
            update_analytics_for_complaint(complaint_id)
        except Exception as analytics_error:
            print(f"⚠️  Failed to update analytics: {analytics_error}")

        return result

    except Exception as e:
        print(f"❌ Background processing failed for complaint {complaint_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


async def process_complaint_async(complaint_id: int, service: ComplaintService):
    """
    Async wrapper that runs the synchronous processing in a thread pool
    This prevents blocking the main event loop
    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, process_complaint_sync, complaint_id, service)


@app.post("/complaints/submit", response_model=ComplaintResponse)
async def submit_complaint(
    background_tasks: BackgroundTasks,
    full_name: Optional[str] = Form(None),
    ic_number: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    complaint_title: str = Form(...),
    complaint_description: str = Form(...),
    files: List[UploadFile] = File(default=[])
):
    """
    Submit a new complaint with optional file attachments

    All complainant information is now OPTIONAL for anonymous complaints.

    This endpoint:
    1. Saves complaint to database
    2. Uploads and saves any attached files
    3. Triggers background processing (classification + similarity search)
    4. Returns immediately with complaint ID
    """
    service = get_complaint_service()

    try:
        # Prepare complaint data
        complaint_data = {
            'full_name': full_name,
            'ic_number': ic_number,
            'phone_number': phone_number,
            'email': email,
            'complaint_title': complaint_title,
            'complaint_description': complaint_description
        }

        # Save complaint to database
        complaint_id = service.save_complaint(complaint_data)
        print(f"✅ Complaint {complaint_id} saved to database")

        # Handle file uploads
        uploaded_files = []
        if files and len(files) > 0:
            for file in files:
                if file.filename:
                    # Generate unique filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    file_extension = Path(file.filename).suffix
                    unique_filename = f"complaint_{complaint_id}_{timestamp}_{file.filename}"
                    file_path = UPLOAD_DIR / unique_filename

                    # Save file
                    with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)

                    file_size = file_path.stat().st_size

                    # Save document metadata to database
                    doc_id = service.save_document(
                        complaint_id=complaint_id,
                        filename=unique_filename,
                        original_filename=file.filename,
                        file_path=str(file_path),
                        file_size=file_size,
                        file_type=file.content_type or "application/octet-stream"
                    )

                    uploaded_files.append({
                        'id': doc_id,
                        'filename': file.filename,
                        'size': file_size
                    })

                    print(f"✅ File uploaded: {file.filename} ({file_size} bytes)")

            # Update document count
            service.update_document_count(complaint_id, len(uploaded_files))

        # Trigger background processing (classification + similarity search)
        background_tasks.add_task(process_complaint_async, complaint_id, service)

        return ComplaintResponse(
            complaint_id=complaint_id,
            status="submitted",
            message="Aduan berjaya diterima dan sedang diproses / Complaint successfully received and being processed",
            submitted_at=datetime.now(),
            document_count=len(uploaded_files)
        )

    except Exception as e:
        print(f"❌ Error submitting complaint: {e}")
        raise HTTPException(status_code=500, detail=f"Error submitting complaint: {str(e)}")


@app.get("/complaints/{complaint_id}", response_model=ComplaintDetail)
async def get_complaint_details(complaint_id: int):
    """
    Get detailed information about a complaint

    Includes:
    - Complaint information
    - Classification results
    - Uploaded documents
    - Similar cases
    - Case assignment (if any)
    """
    service = get_complaint_service()
    case_service = get_case_service()

    try:
        # Get complaint
        complaint = service.get_complaint(complaint_id)
        if not complaint:
            raise HTTPException(status_code=404, detail="Complaint not found")

        # Get documents
        documents = service.get_complaint_documents(complaint_id)

        # Get similar cases
        similar_cases = service.get_similar_cases(complaint_id)

        # Get case assignment
        case = case_service.get_case_for_complaint(complaint_id)
        case_id = case['id'] if case else None
        case_number = case['case_number'] if case else None

        return ComplaintDetail(
            **complaint,
            documents=documents,
            similar_cases=similar_cases,
            case_id=case_id,
            case_number=case_number
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving complaint: {str(e)}")


def reprocess_complaint_after_edit(complaint_id: int):
    """
    Re-process complaint after officer edits 5W1H fields

    This function:
    1. Rebuilds w1h_summary from individual fields
    2. Re-classifies (CRIS/NFA) based on new 5W1H
    3. Re-determines sector and akta
    4. Regenerates embedding for similarity search
    5. Optionally re-groups into different case
    """
    try:
        print(f"🔄 Re-processing complaint {complaint_id} after 5W1H edit...")

        service = get_complaint_service()
        classification_service = get_classification_service()
        vllm_service = get_vllm_service()

        # Get current complaint data
        with db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM complaints WHERE id = %s", (complaint_id,))
            complaint = cursor.fetchone()

        if not complaint:
            print(f"❌ Complaint {complaint_id} not found")
            return

        # Rebuild w1h_summary from edited fields
        w1h_dict = {
            'what': complaint.get('w1h_what'),
            'who': complaint.get('w1h_who'),
            'when': complaint.get('w1h_when'),
            'where': complaint.get('w1h_where'),
            'why': complaint.get('w1h_why'),
            'how': complaint.get('w1h_how')
        }

        # Create full_text version
        full_text = f"""**WHAT (Apa):** {w1h_dict.get('what', 'N/A')}

**WHO (Siapa):** {w1h_dict.get('who', 'N/A')}

**WHEN (Bila):** {w1h_dict.get('when', 'N/A')}

**WHERE (Di mana):** {w1h_dict.get('where', 'N/A')}

**WHY (Mengapa):** {w1h_dict.get('why', 'N/A')}

**HOW (Bagaimana):** {w1h_dict.get('how', 'N/A')}"""

        w1h_dict['full_text'] = full_text

        # Step 1: Re-classify
        classification_result = classification_service.classify_from_5w1h(
            w1h_summary=w1h_dict,
            complaint_description=complaint['complaint_description']
        )

        # Step 2: Re-determine sector
        sector = vllm_service.generate_sector(
            w1h_summary=w1h_dict,
            complaint_text=f"{complaint['complaint_title']} {complaint['complaint_description']}"
        )

        # Step 3: Re-determine akta
        akta = vllm_service.generate_akta(
            w1h_summary=w1h_dict,
            complaint_text=f"{complaint['complaint_title']} {complaint['complaint_description']}",
            sector=sector
        )

        # Step 4: Regenerate embedding
        from search_relevant_case import CaseSearchEngine
        search_engine = CaseSearchEngine()
        search_engine.load_model()

        embedding_text = f"{complaint['complaint_title']} {complaint['complaint_description']} {full_text}"
        embedding_array = search_engine.generate_embedding(embedding_text)
        embedding = embedding_array.tolist()

        # Step 5: Update database
        update_query = """
        UPDATE complaints
        SET w1h_summary = %s,
            sector = %s,
            akta = %s,
            embedding = %s,
            classification = %s,
            classification_confidence = %s,
            processed_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """

        with db.get_cursor() as cursor:
            cursor.execute(update_query, (
                full_text,
                sector,
                akta,
                embedding,
                classification_result['classification'] if classification_result else None,
                classification_result['confidence'] if classification_result else None,
                complaint_id
            ))

        print(f"✅ Re-processing completed for complaint {complaint_id}")
        print(f"   Classification: {classification_result['classification'] if classification_result else 'N/A'}")
        print(f"   Sector: {sector or 'N/A'}")
        print(f"   Akta: {akta or 'N/A'}")
        print(f"   Embedding: Regenerated ({len(embedding)} dimensions)")

        # Invalidate analytics cache after complaint update
        try:
            analytics_service = get_analytics_service()
            analytics_service.invalidate_cache()
            print(f"🗑️  Analytics cache invalidated (will refresh on next request)")
        except Exception as cache_error:
            print(f"⚠️  Failed to invalidate analytics cache: {cache_error}")

    except Exception as e:
        print(f"❌ Error re-processing complaint {complaint_id}: {e}")
        import traceback
        traceback.print_exc()


@app.put("/complaints/{complaint_id}")
async def update_complaint(complaint_id: int, updates: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Update complaint fields (for manual editing by officers)

    **Editable fields:**
    - `complaint_title` - Update complaint title
    - `complaint_description` - Update description
    - `category` - Change category
    - `urgency_level` - Change urgency (Rendah/Sederhana/Tinggi/Kritikal)
    - `w1h_what` - Edit WHAT field
    - `w1h_who` - Edit WHO field
    - `w1h_when` - Edit WHEN field
    - `w1h_where` - Edit WHERE field
    - `w1h_why` - Edit WHY field
    - `w1h_how` - Edit HOW field
    - `w1h_summary` - Edit full 5W1H summary
    - `sector` - Change government sector
    - `akta` - Change relevant legislation/act
    - `classification` - Change classification (CRIS/NFA)
    - `classification_confidence` - Update confidence score
    - `status` - Change status

    **Request body example:**
    ```json
    {
      "w1h_what": "Updated description of what happened",
      "w1h_who": "Updated persons involved",
      "classification": "CRIS"
    }
    ```

    **Returns:** Updated complaint details
    """
    # Define allowed fields for updates
    allowed_fields = [
        'complaint_title', 'complaint_description', 'category', 'urgency_level',
        'w1h_what', 'w1h_who', 'w1h_when', 'w1h_where', 'w1h_why', 'w1h_how', 'w1h_summary',
        'sector', 'akta',
        'classification', 'classification_confidence', 'status'
    ]

    # Filter to only allowed fields
    update_fields = {k: v for k, v in updates.items() if k in allowed_fields}

    if not update_fields:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    # Check if 5W1H fields were edited - triggers re-processing
    w1h_fields = {'w1h_what', 'w1h_who', 'w1h_when', 'w1h_where', 'w1h_why', 'w1h_how', 'w1h_summary'}
    w1h_edited = any(field in update_fields for field in w1h_fields)

    # Build dynamic UPDATE query
    set_clauses = ', '.join([f"{field} = %s" for field in update_fields.keys()])
    query = f"""
    UPDATE complaints
    SET {set_clauses}, processed_at = CURRENT_TIMESTAMP
    WHERE id = %s
    RETURNING id
    """

    try:
        with db.get_cursor() as cursor:
            # Execute update
            values = list(update_fields.values()) + [complaint_id]
            cursor.execute(query, tuple(values))
            result = cursor.fetchone()

            if not result:
                raise HTTPException(status_code=404, detail="Complaint not found")

        print(f"✅ Complaint {complaint_id} updated: {', '.join(update_fields.keys())}")

        # If 5W1H was edited, trigger re-classification and re-embedding
        if w1h_edited:
            print(f"🔄 5W1H edited - triggering re-processing for complaint {complaint_id}")
            background_tasks.add_task(reprocess_complaint_after_edit, complaint_id)

        # Return updated complaint
        return await get_complaint_details(complaint_id)

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating complaint {complaint_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating complaint: {str(e)}")


@app.get("/documents/{document_id}/download")
async def download_document(document_id: int):
    """
    Download a complaint document by ID

    **Description:**
    Returns the actual file for download or preview in browser.
    Frontend can use this to display images, PDFs, etc.

    **Example:**
    ```
    GET /documents/123/download
    ```

    **Returns:** File with appropriate content-type headers
    """
    try:
        # Get document metadata from database
        query = """
        SELECT filename, file_path, file_type, original_filename
        FROM complaint_documents
        WHERE id = %s
        """

        with db.get_cursor() as cursor:
            cursor.execute(query, (document_id,))
            document = cursor.fetchone()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        file_path = Path(document['file_path'])

        # Check if file exists on disk
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"File not found on server: {document['filename']}"
            )

        # Return file with proper headers
        return FileResponse(
            path=str(file_path),
            media_type=document['file_type'],
            filename=document['original_filename']  # Use original filename for download
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error downloading document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error downloading document: {str(e)}")


@app.get("/complaints")
async def list_complaints(
    status: Optional[str] = None,
    category: Optional[str] = None,
    assigned: Optional[bool] = None,
    officer_status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    List complaints with optional filtering

    Query parameters:
    - status: Filter by AI processing status (pending, processed)
    - category: Filter by category
    - assigned: Filter by case assignment (true=in a case, false=not in any case, null=all)
    - officer_status: Filter by officer review status (pending_review, nfa, escalated, investigating, closed)
    - limit: Number of results (default: 50)
    - offset: Pagination offset (default: 0)
    """
    try:
        # Build query with LEFT JOIN to get case info
        query = """
        SELECT c.*,
               cases.id as case_id,
               cases.case_number
        FROM complaints c
        LEFT JOIN case_complaints cc ON c.id = cc.complaint_id
        LEFT JOIN cases ON cc.case_id = cases.id
        WHERE 1=1
        """
        params = []

        if status:
            query += " AND c.status = %s"
            params.append(status)

        if category:
            query += " AND c.category = %s"
            params.append(category)

        if officer_status:
            query += " AND c.officer_status = %s"
            params.append(officer_status)

        if assigned is not None:
            if assigned:
                query += " AND cases.id IS NOT NULL"
            else:
                query += " AND cases.id IS NULL"

        query += " ORDER BY c.submitted_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        # Execute query
        with db.get_cursor() as cursor:
            cursor.execute(query, tuple(params))
            complaints = cursor.fetchall()

        return {
            "total": len(complaints),
            "complaints": complaints,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing complaints: {str(e)}")


@app.get("/complaints/unassigned")
async def list_unassigned_complaints(
    limit: int = 50,
    offset: int = 0
):
    """
    List complaints that are not assigned to any case

    This endpoint helps officers find complaints that need to be reviewed
    and potentially grouped into cases.

    Query parameters:
    - limit: Number of results (default: 50)
    - offset: Pagination offset (default: 0)

    Returns:
    - List of complaints without case assignments
    """
    try:
        query = """
        SELECT c.*
        FROM complaints c
        LEFT JOIN case_complaints cc ON c.id = cc.complaint_id
        WHERE cc.case_id IS NULL
        ORDER BY c.submitted_at DESC
        LIMIT %s OFFSET %s
        """

        # Count total unassigned
        count_query = """
        SELECT COUNT(*) as total
        FROM complaints c
        LEFT JOIN case_complaints cc ON c.id = cc.complaint_id
        WHERE cc.case_id IS NULL
        """

        with db.get_cursor() as cursor:
            # Get count
            cursor.execute(count_query)
            total = cursor.fetchone()['total']

            # Get complaints
            cursor.execute(query, (limit, offset))
            complaints = cursor.fetchall()

        return {
            "total": total,
            "complaints": complaints,
            "limit": limit,
            "offset": offset,
            "message": f"Found {total} unassigned complaint(s)"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing unassigned complaints: {str(e)}")


# ============================================================================
# CASE MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/cases")
async def list_cases(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    List all cases with optional filtering

    Query parameters:
    - status: Filter by status (open, investigating, closed)
    - limit: Number of results (default: 50)
    - offset: Pagination offset (default: 0)
    """
    service = get_case_service()

    try:
        cases = service.list_cases(status=status, limit=limit, offset=offset)
        return {
            "total": len(cases),
            "cases": cases,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing cases: {str(e)}")


@app.get("/cases/{case_id}")
async def get_case_details(case_id: int):
    """
    Get detailed information about a case including all related complaints

    Returns:
    - Case metadata (case_number, title, status, etc.)
    - List of complaints in the case
    - Common entities and keywords
    """
    service = get_case_service()

    try:
        case = service.get_case_details(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        return case
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving case: {str(e)}")


@app.post("/cases")
async def create_case(
    complaint_ids: List[int],
    case_title: Optional[str] = None,
    added_by: str = "user"
):
    """
    Manually create a new case with specified complaints

    Request body:
    - complaint_ids: List of complaint IDs to group together
    - case_title: Optional case title (auto-generated if not provided)
    - added_by: Username or 'system'

    Returns:
    - Created case ID and case number
    """
    service = get_case_service()

    try:
        case_id = service.create_case(
            complaint_ids=complaint_ids,
            case_title=case_title,
            auto_grouped=False,
            added_by=added_by
        )

        if not case_id:
            raise HTTPException(status_code=400, detail="Failed to create case")

        # Get case details
        case = service.get_case_details(case_id)
        return {
            "message": "Case created successfully",
            "case_id": case_id,
            "case_number": case['case_number'],
            "case": case
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating case: {str(e)}")


@app.put("/cases/{case_id}")
async def update_case(case_id: int, updates: Dict[str, Any]):
    """
    Update case information

    Allowed fields:
    - case_title: Update case title
    - case_description: Update description
    - status: Change status (open, investigating, closed)
    - priority: Change priority (low, medium, high, critical)
    - classification: Change classification (CRIS, NFA)
    """
    service = get_case_service()

    try:
        success = service.update_case(case_id, updates)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update case")

        case = service.get_case_details(case_id)
        return {
            "message": "Case updated successfully",
            "case": case
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating case: {str(e)}")


@app.delete("/cases/{case_id}")
async def delete_case(case_id: int):
    """
    Delete a case

    Note: This will remove the case and all case-complaint associations,
    but complaints themselves will remain in the system.
    """
    service = get_case_service()

    try:
        success = service.delete_case(case_id)
        if not success:
            raise HTTPException(status_code=404, detail="Case not found or already deleted")

        return {"message": f"Case {case_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting case: {str(e)}")


@app.post("/cases/{case_id}/complaints")
async def add_complaint_to_case(
    case_id: int,
    complaint_id: int,
    added_by: str = "user"
):
    """
    Add a complaint to an existing case

    Parameters:
    - case_id: Target case ID
    - complaint_id: Complaint to add
    - added_by: Username or 'system'
    """
    service = get_case_service()

    try:
        # Check if case exists
        case = service.get_case_details(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        # Check if complaint exists
        complaint = service.get_complaint_by_id(complaint_id)
        if not complaint:
            raise HTTPException(status_code=404, detail="Complaint not found")

        # Add complaint to case
        service.add_complaint_to_case(case_id, complaint_id, added_by=added_by)

        return {
            "message": f"Complaint {complaint_id} added to case {case_id}",
            "case": service.get_case_details(case_id)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding complaint to case: {str(e)}")


@app.get("/cases/{case_id}/related")
async def get_related_cases(case_id: int):
    """
    Get related closed cases for a given case

    Returns:
    - List of similar closed cases that were detected when this case was created
    - Includes case_number, case_title, similarity_score, and status

    Example response:
    {
        "case_id": 42,
        "case_number": "CASE-2025-0042",
        "related_cases": [
            {
                "case_id": 15,
                "case_number": "CASE-2024-0015",
                "case_title": "Kes: Rasuah Tender",
                "similarity_score": 0.87,
                "status": "closed",
                "closed_at": "2024-12-15T10:30:00",
                "detected_at": "2025-10-30T16:45:00"
            }
        ]
    }
    """
    service = get_case_service()

    try:
        case = service.get_case_details(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        # Get related_cases from database
        related_cases = case.get('related_cases', [])

        # Parse JSON if it's a string
        if isinstance(related_cases, str):
            import json
            related_cases = json.loads(related_cases)

        return {
            "case_id": case_id,
            "case_number": case.get('case_number'),
            "related_cases": related_cases if related_cases else []
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving related cases: {str(e)}")


@app.delete("/cases/{case_id}/complaints/{complaint_id}")
async def remove_complaint_from_case(case_id: int, complaint_id: int):
    """
    Remove a complaint from a case

    Parameters:
    - case_id: Source case ID
    - complaint_id: Complaint to remove

    Note: If this is the last complaint in the case, the case will be deleted.
    """
    service = get_case_service()

    try:
        service.remove_complaint_from_case(case_id, complaint_id)

        return {
            "message": f"Complaint {complaint_id} removed from case {case_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing complaint from case: {str(e)}")


@app.get("/config/evaluation-options", response_model=EvaluationOptions)
async def get_evaluation_options():
    """
    Get all dropdown options for complaint evaluation form

    Returns options for:
    - Main sectors
    - Sub-sectors
    - Type of information
    - Source types
    - Currency types
    """
    from subsector_mapping import (
        get_main_sectors,
        get_sub_sectors,
        get_type_of_information_options,
        get_source_type_options,
        get_currency_types
    )

    return EvaluationOptions(
        main_sectors=get_main_sectors(),
        sub_sectors=get_sub_sectors(),
        type_of_information_options=get_type_of_information_options(),
        source_type_options=get_source_type_options(),
        currency_types=get_currency_types(),
        officer_status_options=[
            "pending_review",
            "nfa",
            "escalated",
            "investigating",
            "closed"
        ]
    )


@app.put("/complaints/{complaint_id}/evaluation")
async def save_complaint_evaluation(complaint_id: int, evaluation: ComplaintEvaluation):
    """
    Save officer's evaluation of complaint

    Updates complaint with:
    - Reviewed/edited 5W1H data
    - Classification details (type, source, sector, sub-sector)
    - CRIS details (if applicable)
    - Selected akta sections
    - Evaluation metadata (who, when)
    """
    try:
        # Update complaint with evaluation data
        update_query = """
        UPDATE complaints
        SET
            -- Update 5W1H if edited
            complaint_title = COALESCE(%s, complaint_title),
            w1h_what = COALESCE(%s, w1h_what),
            w1h_when = COALESCE(%s, w1h_when),
            w1h_where = COALESCE(%s, w1h_where),
            w1h_how = COALESCE(%s, w1h_how),
            w1h_why = COALESCE(%s, w1h_why),

            -- Classification
            type_of_information = %s,
            source_type = %s,
            sector = %s,
            sub_sector = %s,

            -- CRIS details
            currency_type = %s,
            property_value = %s,
            cris_details_others = %s,
            akta_sections = %s,

            -- Metadata
            evaluated_at = CURRENT_TIMESTAMP,
            evaluated_by = %s

        WHERE id = %s
        RETURNING *
        """

        with db.get_cursor() as cursor:
            cursor.execute(update_query, (
                # 5W1H (only update if provided)
                evaluation.title,
                evaluation.what_happened,
                evaluation.when_happened,
                evaluation.where_happened,
                evaluation.how_happened,
                evaluation.why_done,

                # Classification
                evaluation.type_of_information,
                evaluation.source_type,
                evaluation.sector,
                evaluation.sub_sector,

                # CRIS details
                evaluation.currency_type,
                evaluation.property_value,
                evaluation.cris_details_others,
                evaluation.akta_sections,

                # Metadata
                evaluation.evaluated_by,
                complaint_id
            ))

            result = cursor.fetchone()

            if not result:
                raise HTTPException(status_code=404, detail="Complaint not found")

            return {
                "message": "Evaluation saved successfully",
                "complaint_id": complaint_id,
                "evaluated_at": result['evaluated_at'],
                "evaluated_by": result['evaluated_by']
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving evaluation: {str(e)}")


@app.put("/complaints/{complaint_id}/officer-review")
async def update_officer_review(complaint_id: int, review: OfficerReview):
    """
    Officer manually reviews complaint and updates status

    Status options:
    - pending_review: Waiting for officer review (default after AI processing)
    - nfa: No Further Action (not corruption, close complaint)
    - escalated: Escalate for investigation
    - investigating: Currently under investigation
    - closed: Investigation completed and closed

    Request Body:
    {
        "officer_status": "nfa",
        "officer_remarks": "After review, this is not a corruption case...",
        "reviewed_by": "officer_ahmad"
    }
    """
    try:
        # Validate status
        valid_statuses = ["pending_review", "nfa", "escalated", "investigating", "closed"]
        if review.officer_status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )

        # Update complaint with officer review
        with db.get_cursor() as cursor:
            update_query = """
            UPDATE complaints
            SET
                officer_status = %s,
                officer_remarks = %s,
                reviewed_by = %s,
                reviewed_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, officer_status, officer_remarks, reviewed_by, reviewed_at
            """

            cursor.execute(update_query, (
                review.officer_status,
                review.officer_remarks,
                review.reviewed_by,
                complaint_id
            ))

            result = cursor.fetchone()

            if not result:
                raise HTTPException(status_code=404, detail="Complaint not found")

            return {
                "message": "Officer review updated successfully",
                "complaint_id": complaint_id,
                "officer_status": result['officer_status'],
                "reviewed_by": result['reviewed_by'],
                "reviewed_at": result['reviewed_at']
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating officer review: {str(e)}")


@app.get("/complaints/{complaint_id}/case")
async def get_complaint_case(complaint_id: int):
    """
    Get the case that a complaint belongs to

    Returns:
    - Case information if complaint is in a case
    - 404 if complaint is not in any case
    """
    service = get_case_service()

    try:
        case = service.get_case_for_complaint(complaint_id)
        if not case:
            raise HTTPException(status_code=404, detail="Complaint is not in any case")

        return service.get_case_details(case['id'])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving complaint case: {str(e)}")


@app.post("/complaints/{complaint_id}/move-to-case/{target_case_id}")
async def move_complaint_to_existing_case(
    complaint_id: int,
    target_case_id: int,
    added_by: str = "officer"
):
    """
    Move a complaint from its current case to another existing case

    This is useful when AI misclassifies complaints or when officers
    want to manually reorganize cases.

    **Parameters:**
    - complaint_id: ID of complaint to move
    - target_case_id: ID of target case to move to
    - added_by: Username of officer performing the move

    **Returns:**
    - Success message with updated case details
    - 404 if complaint or target case not found
    - 400 if complaint is already in target case
    """
    service = get_case_service()

    try:
        # Check if complaint exists
        complaint = service.get_complaint_by_id(complaint_id)
        if not complaint:
            raise HTTPException(status_code=404, detail="Complaint not found")

        # Check if target case exists
        target_case = service.get_case_details(target_case_id)
        if not target_case:
            raise HTTPException(status_code=404, detail="Target case not found")

        # Check if complaint is already in target case
        current_case = service.get_case_for_complaint(complaint_id)
        if current_case and current_case['id'] == target_case_id:
            raise HTTPException(
                status_code=400,
                detail=f"Complaint {complaint_id} is already in case {target_case_id}"
            )

        # Step 1: Remove from current case (if any)
        if current_case:
            print(f"🔄 Removing complaint {complaint_id} from case {current_case['case_number']}")
            service.remove_complaint_from_case(current_case['id'], complaint_id)

        # Step 2: Add to target case
        print(f"➕ Adding complaint {complaint_id} to case {target_case['case_number']}")
        service.add_complaint_to_case(target_case_id, complaint_id, added_by=added_by)

        # Return updated target case
        updated_case = service.get_case_details(target_case_id)
        return {
            "message": f"Complaint {complaint_id} moved to case {target_case['case_number']}",
            "previous_case": current_case['case_number'] if current_case else None,
            "target_case": updated_case
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error moving complaint: {e}")
        raise HTTPException(status_code=500, detail=f"Error moving complaint: {str(e)}")


@app.post("/complaints/{complaint_id}/move-to-new-case")
async def move_complaint_to_new_case(
    complaint_id: int,
    case_title: Optional[str] = None,
    added_by: str = "officer"
):
    """
    Move a complaint from its current case to a new standalone case

    This is useful when a complaint was incorrectly grouped and
    needs to be separated into its own case.

    **Parameters:**
    - complaint_id: ID of complaint to move
    - case_title: Optional title for new case (auto-generated if not provided)
    - added_by: Username of officer performing the move

    **Request body example:**
    ```json
    {
      "case_title": "Kes Rasuah Jabatan Pendidikan XYZ"
    }
    ```

    **Returns:**
    - Success message with new case details
    - 404 if complaint not found
    """
    service = get_case_service()

    try:
        # Check if complaint exists
        complaint = service.get_complaint_by_id(complaint_id)
        if not complaint:
            raise HTTPException(status_code=404, detail="Complaint not found")

        # Get current case (if any)
        current_case = service.get_case_for_complaint(complaint_id)

        # Step 1: Remove from current case (if any)
        if current_case:
            print(f"🔄 Removing complaint {complaint_id} from case {current_case['case_number']}")
            service.remove_complaint_from_case(current_case['id'], complaint_id)

        # Step 2: Create new case with this complaint
        print(f"➕ Creating new case for complaint {complaint_id}")
        new_case_id = service.create_case(
            complaint_ids=[complaint_id],
            case_title=case_title,
            auto_grouped=False,
            added_by=added_by
        )

        if not new_case_id:
            raise HTTPException(status_code=500, detail="Failed to create new case")

        # Return new case details
        new_case = service.get_case_details(new_case_id)
        return {
            "message": f"Complaint {complaint_id} moved to new case {new_case['case_number']}",
            "previous_case": current_case['case_number'] if current_case else None,
            "new_case": new_case
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error moving complaint to new case: {e}")
        raise HTTPException(status_code=500, detail=f"Error moving complaint to new case: {str(e)}")


# ============================================================================
# CLASSIFICATION HELPER FUNCTIONS
# ============================================================================

def classify_text(text: str, description_5: str = None) -> Dict:
    """
    Direct function to classify text without using API

    Args:
        text: Main case description
        description_5: Optional additional description

    Returns:
        Dictionary with classification results
    """
    clf = get_classifier()

    if clf.classifier is None:
        raise ValueError("Model not trained. Please train the model first.")

    # Combine text fields if description_5 is provided
    combined_text = text
    if description_5:
        combined_text = f"{text} {description_5}"

    return clf.predict(combined_text)


def train_model(cris_path: str = "Data CMS/complaint_cris.csv",
                nfa_path: str = "Data CMS/complaint_nfa.csv",
                save_path: str = "sprm_model.pkl") -> Dict:
    """
    Direct function to train the model without using API

    Args:
        cris_path: Path to CRIS CSV file
        nfa_path: Path to NFA CSV file
        save_path: Path to save the trained model

    Returns:
        Dictionary with training results
    """
    clf = get_classifier()

    results = clf.train(cris_path=cris_path, nfa_path=nfa_path)
    clf.save(save_path)

    return results


def search_similar(description: str, top_k: int = 5, **additional_descriptions) -> List[Dict]:
    """
    Direct function to search for similar cases without using API

    Args:
        description: Main case description
        top_k: Number of top results to return
        **additional_descriptions: Additional description fields (description_1, etc.)

    Returns:
        List of similar cases
    """
    engine = get_search_engine()

    if not engine.cases:
        raise ValueError("No cases loaded. Please load cases first.")

    query_desc = {'description': description, **additional_descriptions}
    results = engine.search(query_description=query_desc, top_k=top_k)

    return results


def load_cases(csv_path: str, max_cases: Optional[int] = None) -> int:
    """
    Direct function to load cases from CSV without using API

    Args:
        csv_path: Path to CSV file
        max_cases: Maximum number of cases to load

    Returns:
        Number of cases loaded
    """
    engine = get_search_engine()
    num_cases = engine.load_cases_from_csv(csv_path=csv_path, max_cases=max_cases)
    engine.save("case_search_engine.pkl")

    return num_cases


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/analytics/dashboard")
async def get_analytics_dashboard():
    """
    Get pre-computed analytics dashboard (SIMPLE & FAST)

    **How it works:**
    - Analytics pre-computed and stored when complaints are processed
    - This endpoint just reads from database tables
    - No computation needed - instant response!

    **Returns:**
    {
        "summary": {
            "total_complaints": 150,
            "yes_classification_count": 90,
            "no_classification_count": 60,
            "pending_review_count": 45,
            "nfa_count": 30,
            "escalated_count": 15,
            "total_cases": 85
        },
        "top_names": [{"name": "Ahmad", "count": 12}, ...],
        "top_organizations": [{"organization": "JKR", "count": 8}, ...],
        "top_locations": [{"location": "Kuala Lumpur", "count": 15}, ...],
        "top_amounts": [{"amount": "RM50,000", "count": 5}, ...],
        "sectors": [
            {"sector": "Pembinaan", "complaint_count": 25, "yes_count": 15, "no_count": 10},
            ...
        ],
        "patterns": [
            {"pattern": "tender + gold", "count": 8},
            ...
        ]
    }

    **Frontend Usage:**
    Just call this endpoint - data is already computed!
    No need to wait for computation.
    """
    try:
        from simple_analytics import get_simple_analytics
        analytics = get_simple_analytics()
        return analytics
    except Exception as e:
        print(f"❌ Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting analytics: {str(e)}")


@app.get("/analytics/entities")
async def get_entity_analytics(days: Optional[int] = None):
    """
    Get entity-based analytics

    **Returns:**
    - Top 10 names mentioned across complaints
    - Top 10 organizations/departments
    - Top 10 locations
    - Top amounts/items (gold, cash, etc.)
    - Breakdown by sector and category

    **Query parameters:**
    - days: Limit to last N days (optional)

    **Example:**
    ```
    GET /analytics/entities?days=30
    ```
    """
    service = get_analytics_service()

    try:
        date_from = None
        if days:
            from datetime import datetime, timedelta
            date_from = datetime.now() - timedelta(days=days)

        analytics = service.get_entity_analytics(date_from=date_from)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting entity analytics: {str(e)}")


@app.get("/analytics/patterns")
async def detect_patterns(min_occurrences: int = 2):
    """
    Detect common patterns and combinations in complaints

    **What you get:**
    - 2-keyword combinations (e.g., "tender + gold")
    - 3-keyword combinations (e.g., "school + bribery + cash")
    - Count of how many complaints match each pattern

    **Query parameters:**
    - min_occurrences: Minimum times a pattern must occur (default: 2)

    **Example:**
    ```
    GET /analytics/patterns?min_occurrences=3
    ```

    **Returns:**
    ```json
    {
      "two_keyword_patterns": [
        {
          "pattern": "tender + gold",
          "count": 3,
          "example": "3 complaints involve both tender + gold"
        }
      ]
    }
    ```
    """
    service = get_analytics_service()

    try:
        patterns = service.detect_patterns(min_occurrences=min_occurrences)
        return patterns
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting patterns: {str(e)}")


@app.get("/analytics/trending")
async def get_trending_keywords(days: int = 30, top_n: int = 20):
    """
    Get trending corruption keywords over time period

    **Query parameters:**
    - days: Number of days to analyze (default: 30)
    - top_n: Number of top keywords to return (default: 20)

    **Example:**
    ```
    GET /analytics/trending?days=60&top_n=15
    ```

    **Returns:**
    Top trending keywords with counts and percentages
    """
    service = get_analytics_service()

    try:
        trending = service.get_trending_keywords(days=days, top_n=top_n)
        return trending
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting trending keywords: {str(e)}")


@app.get("/analytics/cases")
async def get_case_analytics():
    """
    Get case-level analytics

    **Returns:**
    - Total cases and complaints
    - Average complaints per case
    - Breakdown by status, priority, classification
    - Top 10 largest cases

    **Example:**
    ```
    GET /analytics/cases
    ```
    """
    service = get_analytics_service()

    try:
        analytics = service.get_case_analytics()
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting case analytics: {str(e)}")


@app.post("/analytics/precompute")
async def precompute_analytics(background_tasks: BackgroundTasks, periods: List[int] = [7, 30, 90]):
    """
    Pre-compute analytics for common periods (runs in background)

    This endpoint triggers background computation of analytics for specified periods.
    The results are cached so frontend requests are instant.

    **Usage:**
    - Call this manually when needed
    - Or set up a cron job to call it every hour
    - First request after this will be fast (served from cache)

    **Query parameters:**
    - periods: List of day periods to pre-compute (default: [7, 30, 90])

    **Example:**
    ```
    POST /analytics/precompute?periods=7&periods=30&periods=90
    ```

    **Returns:**
    Immediate confirmation that task is queued
    """
    service = get_analytics_service()

    # Run in background
    background_tasks.add_task(service.precompute_analytics, periods)

    return {
        "message": "Analytics pre-computation started",
        "periods": periods,
        "status": "queued",
        "note": "Analytics will be computed in background and cached for fast access"
    }


@app.post("/analytics/cache/invalidate")
async def invalidate_analytics_cache(pattern: Optional[str] = None):
    """
    Invalidate (clear) analytics cache

    **Use cases:**
    - After bulk complaint import/updates
    - To force fresh analytics computation
    - When you want to clear specific cache entries

    **Query parameters:**
    - pattern: Optional pattern to match (e.g., "dashboard" clears all dashboard_* caches)
              If omitted, clears ALL analytics cache

    **Example:**
    ```
    POST /analytics/cache/invalidate?pattern=dashboard
    POST /analytics/cache/invalidate  # Clear all
    ```

    **Returns:**
    Confirmation of cache invalidation
    """
    service = get_analytics_service()

    try:
        service.invalidate_cache(pattern=pattern)
        return {
            "message": "Cache invalidated successfully",
            "pattern": pattern or "all",
            "note": "Next analytics request will recompute fresh data"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error invalidating cache: {str(e)}")


@app.get("/analytics/cache/status")
async def get_cache_status():
    """
    Get analytics cache status

    **Returns:**
    - List of cached entries
    - Cache hit/miss ratio
    - Expiration times

    **Example:**
    ```
    GET /analytics/cache/status
    ```
    """
    try:
        query = """
        SELECT
            cache_key,
            period_days,
            complaint_count,
            computed_at,
            expires_at,
            CASE
                WHEN expires_at > CURRENT_TIMESTAMP THEN 'valid'
                ELSE 'expired'
            END as status
        FROM analytics_cache
        ORDER BY computed_at DESC
        """

        with db.get_cursor() as cursor:
            cursor.execute(query)
            entries = cursor.fetchall()

        return {
            "total_entries": len(entries),
            "entries": entries,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cache status: {str(e)}")


# ============================================================================
# LETTER GENERATION ENDPOINTS
# ============================================================================

@app.get("/letters/types")
async def get_letter_types():
    """
    Get available letter types for generation

    Returns list of letter types with descriptions
    """
    from letter_templates import get_available_templates

    return {
        "letter_types": get_available_templates()
    }


@app.get("/letters/template/{letter_type}")
async def get_letter_template_fields(letter_type: str, complaint_id: Optional[int] = None):
    """
    Get editable fields for a letter template with pre-filled values

    **Query Parameters:**
    - complaint_id: Optional complaint ID to pre-fill values

    **Returns:**
    Form fields configuration with pre-filled values from complaint data
    Frontend can render these as editable form fields

    **Example:**
    GET /letters/template/rujuk_jabatan?complaint_id=123
    """
    from letter_templates import get_template_fields, get_template
    from datetime import datetime
    import json

    try:
        # Get template fields configuration
        fields = get_template_fields(letter_type)
        if not fields:
            raise HTTPException(status_code=404, detail=f"Template '{letter_type}' not found")

        # If complaint_id provided, pre-fill values from complaint
        if complaint_id:
            query = "SELECT * FROM complaints WHERE id = %s"
            with db.get_cursor() as cursor:
                cursor.execute(query, (complaint_id,))
                complaint = cursor.fetchone()

            if complaint:
                # Pre-fill auto fields
                now = datetime.now()
                hijri_date = "01 Jamadilakhir 1447"  # Placeholder - would need proper Hijri conversion

                if 'auto_filled' in fields:
                    fields['auto_filled']['rujukan_kami']['value'] = f"SPRM. BPRM. 600-2/3/2 Jld.5({complaint_id})"
                    fields['auto_filled']['tarikh_surat']['value'] = f"{now.strftime('%d %B %Y')}\n{hijri_date}"

                    complaint_title = complaint.get('complaint_title', '')
                    fields['auto_filled']['subject_line']['value'] = f"ADUAN BERHUBUNG {complaint_title.upper()}"

        # Get template preview
        template = get_template(letter_type)

        return {
            "letter_type": letter_type,
            "fields": fields,
            "template_preview": template,
            "complaint_id": complaint_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting template: {str(e)}")


@app.post("/complaints/{complaint_id}/letters/generate")
async def generate_letter(
    complaint_id: int,
    request_body: Dict
):
    """
    Generate letter for a complaint with officer-filled data

    **Request Body:**
    {
        "letter_type": "rujuk_jabatan",
        "fields": {
            "recipient_title": "YBhg. Dato',",
            "recipient_name": "Datuk Bandar",
            "recipient_organization": "Majlis Bandaraya Johor Bahru",
            "recipient_address_line1": "Menara MBJB, No. 1",
            "recipient_address_line2": "Jalan Lingkaran Dalam",
            "recipient_address_line3": "Bukit Senyum, 80300 Johor Bahru",
            "recipient_state": "JOHOR",
            "salutation": "YBhg. Dato',",
            "subject_line": "ADUAN BERHUBUNG...",
            "rujukan_tuan": "",
            "rujukan_kami": "SPRM. BPRM. 600-2/3/2 Jld.5(123)",
            "tarikh_surat": "30 Oktober 2025",
            "officer_title": "Pengarah",
            "officer_department": "Bahagian Pengurusan Rekod & Maklumat",
            "cc_line1": "Setiausaha Kerajaan",
            "cc_line2": "Setiausaha Kerajaan Negeri Johor",
            ...
        },
        "generated_by": "officer_ahmad"
    }

    **Returns:**
    Generated letter with all fields filled
    """
    from letter_templates import get_template

    try:
        letter_type = request_body.get('letter_type')
        fields = request_body.get('fields', {})
        generated_by = request_body.get('generated_by', 'system')

        # Get template
        template = get_template(letter_type)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template '{letter_type}' not found")

        # Fill template with provided fields
        letter_content = template
        for key, value in fields.items():
            placeholder = '{{' + key + '}}'
            letter_content = letter_content.replace(placeholder, str(value) if value else '')

        # Save to database
        from letter_service import LetterService
        from datetime import datetime

        letter_service = LetterService()
        letter_id = letter_service.save_generated_letter(
            complaint_id=complaint_id,
            letter_type=letter_type,
            letter_content=letter_content,
            generated_by=generated_by
        )

        return {
            'letter_id': letter_id,
            'letter_content': letter_content,
            'letter_type': letter_type,
            'generated_at': datetime.now().isoformat(),
            'complaint_id': complaint_id
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating letter: {str(e)}")


@app.get("/complaints/{complaint_id}/letters")
async def get_letter_history(complaint_id: int):
    """
    Get all letters generated for a complaint

    Returns:
    - List of all generated letters with timestamps
    - Allows officer to view/reprint previous letters
    """
    # Validate complaint_id
    if complaint_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid complaint ID")

    from letter_service import LetterService

    try:
        # Check if complaint exists
        with db.get_cursor() as cursor:
            cursor.execute("SELECT id FROM complaints WHERE id = %s", (complaint_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail=f"Complaint {complaint_id} not found")

        letter_service = LetterService()
        letters = letter_service.get_letter_history(complaint_id)

        return {
            "complaint_id": complaint_id,
            "total_letters": len(letters),
            "letters": letters
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting letter history: {str(e)}")


@app.get("/letters/{letter_id}")
async def get_letter(letter_id: int):
    """
    Get specific letter by ID

    Returns:
    - Full letter content
    - Metadata (type, generated_by, timestamp)
    """
    try:
        query = "SELECT * FROM generated_letters WHERE id = %s"

        with db.get_cursor() as cursor:
            cursor.execute(query, (letter_id,))
            letter = cursor.fetchone()

        if not letter:
            raise HTTPException(status_code=404, detail="Letter not found")

        return dict(letter)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting letter: {str(e)}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SPRM Classification & Case Search System")
    parser.add_argument("--mode", choices=["api", "train", "predict", "search", "load-cases"], default="api",
                       help="Mode to run: api (FastAPI server), train (train model), predict (test prediction), search (search similar cases), load-cases (load cases from CSV)")
    parser.add_argument("--text", type=str, help="Text to classify or search (for predict/search mode)")
    parser.add_argument("--csv", type=str, help="CSV file path (for load-cases mode)")
    parser.add_argument("--max-cases", type=int, help="Maximum cases to load from CSV")
    parser.add_argument("--top-k", type=int, default=5, help="Number of top results for search (default: 5)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="API host")
    parser.add_argument("--port", type=int, default=8000, help="API port")

    args = parser.parse_args()

    if args.mode == "api":
        # Run the FastAPI server
        print("🚀 Starting SPRM Classification API Server...")
        uvicorn.run(
            "main:app",
            host=args.host,
            port=args.port,
            reload=True
        )

    elif args.mode == "train":
        # Train the model directly
        print("🚀 Starting model training...")
        results = train_model()
        print("\n" + "="*60)
        print("📊 TRAINING RESULTS:")
        print("="*60)
        print(f"✅ Accuracy: {results['accuracy']:.2f}%")
        print(f"✅ AUC Score: {results['auc_score']:.4f}")
        print(f"✅ Total Cases: {results['total_cases']:,}")
        print(f"✅ CRIS Cases: {results['cris_cases']:,}")
        print(f"✅ NFA Cases: {results['nfa_cases']:,}")
        print("="*60)

    elif args.mode == "predict":
        # Make a prediction directly
        if not args.text:
            print("❌ Error: --text argument is required for predict mode")
            print("Example: python main.py --mode predict --text 'pegawai kerajaan menerima rasuah'")
            sys.exit(1)

        print(f"🔍 Classifying text: {args.text}")
        try:
            result = classify_text(args.text)
            print("\n" + "="*60)
            print("📊 CLASSIFICATION RESULTS:")
            print("="*60)
            print(f"✅ Classification: {result['classification']}")
            print(f"✅ Confidence: {result['confidence']:.2f}%")
            print(f"✅ Corruption Probability: {result['corruption_probability']:.2f}%")
            print(f"✅ No Corruption Probability: {result['no_corruption_probability']:.2f}%")
            print("="*60)
        except ValueError as e:
            print(f"❌ Error: {e}")
            print("💡 Train the model first using: python main.py --mode train")

    elif args.mode == "search":
        # Search for similar cases
        if not args.text:
            print("❌ Error: --text argument is required for search mode")
            print("Example: python main.py --mode search --text 'pegawai menerima rasuah'")
            sys.exit(1)

        print(f"🔍 Searching for similar cases: {args.text}")
        try:
            results = search_similar(args.text, top_k=args.top_k)
            print("\n" + "="*60)
            print("📊 SEARCH RESULTS:")
            print("="*60)
            for result in results:
                print(f"\n🏆 Rank {result['rank']}")
                print(f"   ID: {result['id']}")
                print(f"   Similarity: {result['similarity_score']:.4f}")
                print(f"   Description: {result.get('description', result.get('combined_text', ''))[:200]}...")
            print("="*60)
        except ValueError as e:
            print(f"❌ Error: {e}")
            print("💡 Load cases first using: python main.py --mode load-cases --csv <path>")

    elif args.mode == "load-cases":
        # Load cases from CSV
        if not args.csv:
            print("❌ Error: --csv argument is required for load-cases mode")
            print("Example: python main.py --mode load-cases --csv 'Data CMS/complaint_cris.csv' --max-cases 1000")
            sys.exit(1)

        print(f"🚀 Loading cases from: {args.csv}")
        if args.max_cases:
            print(f"   Max cases: {args.max_cases}")

        try:
            num_cases = load_cases(args.csv, max_cases=args.max_cases)
            print("\n" + "="*60)
            print("📊 LOAD COMPLETE:")
            print("="*60)
            print(f"✅ Total cases loaded: {num_cases:,}")
            print(f"✅ Search engine saved to: case_search_engine.pkl")
            print("="*60)
        except Exception as e:
            print(f"❌ Error: {e}")
