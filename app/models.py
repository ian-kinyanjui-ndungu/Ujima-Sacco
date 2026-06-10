from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class SMSInbound(BaseModel):
    member_id: str = Field(..., description="Unique ID of the member sending the message")
    text: str = Field(..., description="Content of the USSD/SMS text message")
    sub_county: str = Field("Busia Central", description="Sub-county location of the sender for anomaly tracking")

class SMSOutbound(BaseModel):
    member_id: str = Field(..., description="Recipient member ID")
    text: str = Field(..., description="SMS message content to be sent")

class MemberProfile(BaseModel):
    member_id: str
    name: str
    sub_county: str
    crop_type: Optional[str] = None  # e.g., "maize", "matooke", "shea_butter"
    estimated_child_ages: List[int] = Field(default_factory=list)
    current_token_balance: float = 0.0
    gender: str  # Sensitive attributes
    tribe: str   # Sensitive attributes
    is_salaried: bool = False
    monthly_salary: float = 0.0
    average_harvest_income: float = 0.0  # Seasonal spikes
    last_harvest_month: Optional[int] = None # Month index 1-12

class LoanApplication(BaseModel):
    amount: float
    repayment_date: str  # Format: "YYYY-MM-DD"
    status: str = "pending"  # "pending", "approved", "denied", "escalated"
    decision_reason: Optional[str] = None

class StateThread(BaseModel):
    member_id: str
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)  # {"sender": "member/scout/guardian/hunter", "text": "..."}
    harvest_cycle_context: Dict[str, Any] = Field(default_factory=dict)
    financial_stress_flags: List[str] = Field(default_factory=list)
    income_variance_metrics: Dict[str, Any] = Field(default_factory=dict)
    human_escalation_status: str = "inactive"  # "inactive", "pending_review", "assigned", "resolved"
    paused: bool = False
    current_agent: str = "scout"  # "scout", "guardian", "hunter"
    loan_application: Optional[LoanApplication] = None
    telemetry_metadata: Dict[str, Any] = Field(default_factory=dict)
