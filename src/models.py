"""
Pydantic models for API requests and responses
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime


class ComplaintSubmission(BaseModel):
    """Model for complaint form submission"""
    # Complainant Information
    full_name: Optional[str] = Field(None, max_length=255, description="Full name of complainant")
    ic_number: Optional[str] = Field(None, max_length=20, description="IC/Passport number")
    phone_number: str = Field(..., max_length=20, description="Contact phone number")
    email: Optional[EmailStr] = Field(None, description="Email address")

    # Complaint Details
    complaint_title: str = Field(..., max_length=500, description="Title/subject of complaint")
    category: str = Field(..., max_length=100, description="Complaint category")
    urgency_level: str = Field(default="Sederhana", description="Urgency level: Rendah/Sederhana/Tinggi/Kritikal")
    complaint_description: str = Field(..., min_length=10, description="Detailed complaint description")


class ComplaintDocument(BaseModel):
    """Model for uploaded document metadata"""
    id: int
    complaint_id: int
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    file_type: str
    uploaded_at: datetime


class SimilarCase(BaseModel):
    """Model for similar case reference"""
    id: int
    similar_case_id: int
    similarity_score: float
    rank: int
    description: Optional[str] = None


class ComplaintResponse(BaseModel):
    """Response after complaint submission"""
    complaint_id: int
    status: str
    message: str
    submitted_at: datetime
    classification: Optional[str] = None
    classification_confidence: Optional[float] = None
    similar_cases: Optional[List[SimilarCase]] = None
    document_count: int = 0


class ComplaintDetail(BaseModel):
    """Detailed complaint information"""
    id: int
    full_name: Optional[str] = None
    ic_number: Optional[str] = None
    phone_number: str
    email: Optional[str] = None
    complaint_title: str
    category: str
    urgency_level: str
    complaint_description: str
    status: str

    # VLLM Processing Results
    extracted_data: Optional[dict] = None
    w1h_summary: Optional[str] = None  # Full text format (backward compatibility)

    # 5W1H Structured Fields
    w1h_what: Optional[str] = None      # What happened
    w1h_who: Optional[str] = None       # Who was involved
    w1h_when: Optional[str] = None      # When it happened
    w1h_where: Optional[str] = None     # Where it happened
    w1h_why: Optional[str] = None       # Why it happened
    w1h_how: Optional[str] = None       # How it happened

    # AI-Generated Categories
    sector: Optional[str] = None        # Government sector involved
    akta: Optional[str] = None          # Relevant legislation/act

    # AI-Generated Summary
    summary: Optional[str] = None       # Executive summary (2-4 sentences)

    # Classification fields
    classification: Optional[str] = None
    classification_confidence: Optional[float] = None

    # Case Assignment
    case_id: Optional[int] = None           # ID of case this complaint belongs to
    case_number: Optional[str] = None       # Case number (e.g., CASE-2025-0001)

    submitted_at: datetime
    processed_at: Optional[datetime] = None
    has_documents: bool
    document_count: int
    documents: Optional[List[ComplaintDocument]] = None
    similar_cases: Optional[List[SimilarCase]] = None
