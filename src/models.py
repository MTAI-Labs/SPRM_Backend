"""
Pydantic models for API requests and responses
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Union
from datetime import datetime


class ComplaintSubmission(BaseModel):
    """Model for complaint form submission"""
    # Complainant Information (ALL OPTIONAL for anonymous complaints)
    full_name: Optional[str] = Field(None, max_length=255, description="Full name of complainant (optional)")
    ic_number: Optional[str] = Field(None, max_length=20, description="IC/Passport number (optional)")
    phone_number: Optional[str] = Field(None, max_length=20, description="Contact phone number (optional)")
    email: Optional[EmailStr] = Field(None, description="Email address (optional)")

    # Complaint Details
    complaint_title: str = Field(..., max_length=500, description="Title/subject of complaint")
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
    download_url: Optional[str] = None  # URL to download/preview the file


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
    phone_number: Optional[str] = None  # Optional (allows anonymous)
    email: Optional[str] = None
    complaint_title: str
    category: Optional[str] = None  # Optional (deprecated)
    urgency_level: Optional[str] = None  # Optional (deprecated)
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
    akta: Optional[str] = None          # Relevant legislation/act (single, AI-suggested)

    # AI-Generated Summary
    summary: Optional[str] = None       # Executive summary (2-4 sentences)

    # Classification fields
    classification: Optional[str] = None  # YES or NO
    classification_confidence: Optional[float] = None

    # Evaluation Fields (filled by officers)
    type_of_information: Optional[str] = None  # Intelligence, Complaint, Report, etc.
    source_type: Optional[str] = None           # Public, Agency, Media, etc.
    sub_sector: Optional[str] = None            # Sub-category of sector
    currency_type: Optional[str] = None         # MYR, USD, etc.
    property_value: Optional[float] = None      # Value of property/bribe
    cris_details_others: Optional[str] = None   # Additional CRIS details
    akta_sections: Optional[List[str]] = None   # Multiple akta sections (officer-selected)
    evaluated_at: Optional[datetime] = None     # When evaluated
    evaluated_by: Optional[str] = None          # Officer who evaluated

    # Officer Review Status
    officer_status: Optional[str] = None        # pending_review, nfa, escalated, investigating, closed
    officer_remarks: Optional[str] = None       # Officer notes and remarks
    reviewed_by: Optional[str] = None           # Officer who reviewed
    reviewed_at: Optional[datetime] = None      # When reviewed

    # Case Assignment
    case_id: Optional[int] = None           # ID of case this complaint belongs to
    case_number: Optional[str] = None       # Case number (e.g., CASE-2025-0001)

    submitted_at: datetime
    processed_at: Optional[datetime] = None
    has_documents: bool
    document_count: int
    documents: Optional[List[ComplaintDocument]] = None
    similar_cases: Optional[List[SimilarCase]] = None


class ComplaintEvaluation(BaseModel):
    """Model for officer's evaluation of complaint"""
    # Basic Information (editable from AI suggestions)
    title: Optional[str] = Field(None, max_length=500)
    what_happened: Optional[str] = None
    when_happened: Optional[str] = None
    where_happened: Optional[str] = None
    how_happened: Optional[str] = None
    why_done: Optional[str] = None

    # Classification (required)
    type_of_information: str = Field(..., description="Intelligence, Complaint, Report, etc.")
    source_type: str = Field(..., description="Public, Agency, Media, etc.")
    sector: str = Field(..., description="Main sector")
    sub_sector: str = Field(..., description="Sub-sector")

    # CRIS Details (required if classification = YES)
    currency_type: Optional[str] = None
    property_value: Optional[float] = None
    cris_details_others: Optional[str] = None
    organizations: Optional[List[str]] = None
    akta_sections: List[str] = Field(..., min_items=1, description="At least one akta section required")

    # Metadata
    evaluated_by: str = Field(..., description="Officer username/ID")


class OfficerReview(BaseModel):
    """Model for officer's manual review and status update"""
    officer_status: str = Field(..., description="pending_review, nfa, escalated, investigating, closed")
    officer_remarks: Optional[str] = Field(None, description="Officer notes and remarks")
    reviewed_by: str = Field(..., description="Officer username/ID")


class EvaluationOptions(BaseModel):
    """Available options for evaluation dropdowns"""
    main_sectors: List[str]
    sub_sectors: List[str]
    type_of_information_options: List[str]
    source_type_options: List[str]
    currency_types: List[str]
    officer_status_options: List[str]


class AuditLog(BaseModel):
    """Audit log entry for tracking user actions"""
    id: int
    user_id: Optional[str] = None
    user_role: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    description: Optional[str] = None
    changes: Optional[dict] = None
    metadata: Optional[dict] = None
    timestamp: datetime
    endpoint: Optional[str] = None
    http_method: Optional[str] = None
    status_code: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None


class AuditLogFilter(BaseModel):
    """Filter parameters for audit log queries"""
    user_id: Optional[str] = None
    action: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    ip_address: Optional[str] = None
    limit: int = 100
    offset: int = 0
