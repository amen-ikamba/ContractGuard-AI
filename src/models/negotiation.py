"""
Data models for contract negotiation
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class NegotiationStatus(str, Enum):
    """Status of negotiation session"""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    AWAITING_RESPONSE = "AWAITING_RESPONSE"
    COMPLETED = "COMPLETED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    STALLED = "STALLED"


class RequestStatus(str, Enum):
    """Status of individual negotiation request"""
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    COUNTERED = "COUNTERED"
    WITHDRAWN = "WITHDRAWN"


class NegotiationRequest(BaseModel):
    """Individual change request in negotiation"""
    request_id: str = Field(..., description="Unique request identifier")
    clause_id: str = Field(..., description="Related clause ID")
    clause_type: str = Field(..., description="Type of clause being negotiated")
    original_text: str = Field(..., description="Original clause text")
    proposed_text: str = Field(..., description="Proposed replacement text")
    rationale: str = Field(..., description="Business justification for change")
    priority: int = Field(..., ge=1, le=10, description="Priority 1-10 (10=critical)")
    status: RequestStatus = Field(default=RequestStatus.PENDING, description="Request status")
    counterparty_response: Optional[str] = Field(None, description="Their response/counter")
    final_text: Optional[str] = Field(None, description="Agreed final text")

    class Config:
        use_enum_values = True


class NegotiationStrategy(BaseModel):
    """AI-generated negotiation strategy"""
    overall_approach: str = Field(..., description="High-level strategy description")
    priorities: List[str] = Field(..., description="Ordered list of priorities")
    walk_away_conditions: List[str] = Field(..., description="Conditions that would cause rejection")
    compromise_positions: Dict[str, str] = Field(default_factory=dict, description="Fallback positions")
    talking_points: List[str] = Field(default_factory=list, description="Key points to emphasize")
    estimated_rounds: int = Field(default=1, description="Estimated negotiation rounds needed")


class NegotiationRound(BaseModel):
    """Single round of back-and-forth negotiation"""
    round_id: str = Field(..., description="Unique round identifier")
    session_id: str = Field(..., description="Parent negotiation session ID")
    round_number: int = Field(..., ge=1, description="Round number (1, 2, 3...)")
    
    # Our side
    our_requests: List[NegotiationRequest] = Field(..., description="Our requests this round")
    our_email_draft: str = Field(..., description="Draft email to counterparty")
    our_email_sent: bool = Field(default=False, description="Whether email was sent")
    our_email_sent_at: Optional[datetime] = Field(None, description="When email was sent")
    
    # Their side
    counterparty_response: Optional[str] = Field(None, description="Their full response")
    counterparty_response_received_at: Optional[datetime] = Field(None, description="When response received")
    
    # Analysis
    accepted_requests: List[str] = Field(default_factory=list, description="Request IDs accepted")
    rejected_requests: List[str] = Field(default_factory=list, description="Request IDs rejected")
    countered_requests: List[str] = Field(default_factory=list, description="Request IDs countered")
    
    # Next steps
    next_action: Optional[str] = Field(None, description="AI recommendation for next action")
    ai_analysis: Optional[str] = Field(None, description="AI analysis of counterparty response")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None, description="When round concluded")


class NegotiationSession(BaseModel):
    """Complete negotiation session for a contract"""
    session_id: str = Field(..., description="Unique session identifier")
    contract_id: str = Field(..., description="Related contract ID")
    user_id: str = Field(..., description="User managing negotiation")
    
    # Strategy
    strategy: NegotiationStrategy = Field(..., description="Overall negotiation strategy")
    
    # Rounds
    rounds: List[NegotiationRound] = Field(default_factory=list, description="Negotiation rounds")
    current_round: int = Field(default=0, description="Current round number")
    
    # Status
    status: NegotiationStatus = Field(default=NegotiationStatus.PENDING, description="Session status")
    
    # Results
    total_requests: int = Field(default=0, description="Total requests made")
    accepted_count: int = Field(default=0, description="Requests accepted")
    rejected_count: int = Field(default=0, description="Requests rejected")
    success_rate: float = Field(default=0.0, ge=0, le=1, description="Acceptance rate 0-1")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None, description="When negotiation concluded")
    
    # Final outcome
    final_recommendation: Optional[str] = Field(None, description="Sign/reject recommendation")
    final_contract_approved: bool = Field(default=False, description="Whether contract was approved")

    class Config:
        use_enum_values = True


class EmailTemplate(BaseModel):
    """Email template for negotiations"""
    template_id: str = Field(..., description="Template identifier")
    name: str = Field(..., description="Template name")
    subject: str = Field(..., description="Email subject line")
    body_template: str = Field(..., description="Email body with placeholders")
    tone: str = Field(default="professional", description="Email tone")
    use_case: str = Field(..., description="When to use this template")


class NegotiationResponse(BaseModel):
    """API response for negotiation operations"""
    success: bool = Field(..., description="Operation success")
    session_id: Optional[str] = Field(None, description="Negotiation session ID")
    round_number: Optional[int] = Field(None, description="Current round number")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data")
    error: Optional[str] = Field(None, description="Error message if failed")


class CounterpartyResponse(BaseModel):
    """Model for processing counterparty responses"""
    session_id: str = Field(..., description="Negotiation session ID")
    round_number: int = Field(..., description="Round number responding to")
    response_text: str = Field(..., description="Full text of their response")
    response_type: Optional[str] = Field(None, description="Email/letter/verbal")
    received_at: datetime = Field(default_factory=datetime.utcnow)
