"""
Data models for contracts
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ContractStatus(str, Enum):
    """Contract processing status"""
    PENDING = "PENDING"
    UPLOADING = "UPLOADING"
    ANALYZING = "ANALYZING"
    REVIEWED = "REVIEWED"
    NEEDS_NEGOTIATION = "NEEDS_NEGOTIATION"
    NEGOTIATING = "NEGOTIATING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ERROR = "ERROR"


class RiskLevel(str, Enum):
    """Risk severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class ClauseType(str, Enum):
    """Types of contract clauses"""
    LIABILITY = "LIABILITY"
    IP = "IP"
    PAYMENT = "PAYMENT"
    TERMINATION = "TERMINATION"
    CONFIDENTIALITY = "CONFIDENTIALITY"
    DATA_PROTECTION = "DATA_PROTECTION"
    DISPUTE_RESOLUTION = "DISPUTE_RESOLUTION"
    WARRANTY = "WARRANTY"
    INDEMNIFICATION = "INDEMNIFICATION"
    OTHER = "OTHER"


class Clause(BaseModel):
    """Individual contract clause"""
    clause_id: str = Field(..., description="Unique identifier for the clause")
    type: ClauseType = Field(..., description="Type of clause")
    text: str = Field(..., description="Abbreviated clause text (first 500 chars)")
    full_text: str = Field(..., description="Full clause text")
    section_number: int = Field(..., description="Section number in contract")
    risk_score: Optional[float] = Field(None, ge=0, le=10, description="Risk score 0-10")
    risk_level: Optional[RiskLevel] = Field(None, description="Categorized risk level")
    concerns: List[str] = Field(default_factory=list, description="Identified concerns")
    impact: Optional[str] = Field(None, description="Business impact description")
    recommendations: List[str] = Field(default_factory=list, description="Suggested improvements")

    class Config:
        use_enum_values = True


class UserContext(BaseModel):
    """User/company context for contract analysis"""
    industry: str = Field(default="General", description="Industry sector")
    company_size: str = Field(default="Small", description="Company size: Small/Medium/Large")
    risk_tolerance: str = Field(default="Moderate", description="Risk tolerance: Conservative/Moderate/Aggressive")
    jurisdiction: Optional[str] = Field(None, description="Legal jurisdiction")
    additional_context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class ContractMetadata(BaseModel):
    """Contract document metadata"""
    word_count: int = Field(default=0, description="Total word count")
    estimated_pages: int = Field(default=0, description="Estimated page count")
    parsed_at: Optional[datetime] = Field(None, description="When parsing completed")
    analyzed_at: Optional[datetime] = Field(None, description="When analysis completed")
    file_size_bytes: Optional[int] = Field(None, description="Original file size")
    file_type: Optional[str] = Field(None, description="File type (pdf, docx, etc)")


class RiskAnalysis(BaseModel):
    """Contract risk analysis results"""
    overall_risk_score: float = Field(..., ge=0, le=10, description="Overall risk score")
    risk_level: RiskLevel = Field(..., description="Overall risk level")
    high_risk_clauses: List[Clause] = Field(default_factory=list)
    medium_risk_clauses: List[Clause] = Field(default_factory=list)
    low_risk_clauses: List[Clause] = Field(default_factory=list)
    summary: str = Field(..., description="Executive summary of risks")
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class Contract(BaseModel):
    """Main contract model"""
    contract_id: str = Field(..., description="Unique contract identifier")
    user_id: str = Field(..., description="User who uploaded the contract")

    # Document information
    contract_type: str = Field(default="OTHER", description="Type of contract (NDA, MSA, etc)")
    title: Optional[str] = Field(None, description="Contract title")
    parties: List[str] = Field(default_factory=list, description="Contracting parties")
    effective_date: Optional[str] = Field(None, description="Contract effective date")
    term_length: Optional[str] = Field(None, description="Contract term/duration")

    # Storage
    s3_bucket: str = Field(..., description="S3 bucket containing document")
    s3_key: str = Field(..., description="S3 key for document")

    # Processing status
    status: ContractStatus = Field(default=ContractStatus.PENDING, description="Current status")

    # Parsed data
    key_clauses: List[Clause] = Field(default_factory=list, description="Extracted clauses")
    full_text: Optional[str] = Field(None, description="Full extracted text")

    # Analysis results
    risk_analysis: Optional[RiskAnalysis] = Field(None, description="Risk analysis results")

    # Context
    user_context: UserContext = Field(default_factory=UserContext, description="User context")
    metadata: ContractMetadata = Field(default_factory=ContractMetadata, description="Document metadata")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    # Negotiation
    negotiation_session_id: Optional[str] = Field(None, description="Active negotiation session ID")

    class Config:
        use_enum_values = True

    @validator('updated_at', always=True)
    def set_updated_at(cls, v):
        """Always update timestamp on model changes"""
        return datetime.utcnow()


class ContractUploadRequest(BaseModel):
    """Request model for contract upload"""
    user_id: str = Field(..., description="User uploading the contract")
    file_name: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File MIME type")
    user_context: Optional[UserContext] = Field(None, description="User context for analysis")


class ContractResponse(BaseModel):
    """Response model for contract operations"""
    success: bool = Field(..., description="Operation success status")
    contract_id: Optional[str] = Field(None, description="Contract ID if successful")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional response data")
    error: Optional[str] = Field(None, description="Error message if failed")
