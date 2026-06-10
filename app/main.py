import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.models import SMSInbound, SMSOutbound, MemberProfile, LoanApplication
from app.db import db
from app.agents import process_ussd_sms_loop
from app.compliance import SOVEREIGN_CONFIG, get_anomaly_alerts, dignity_message_interceptor

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(
    title="Ujima SACCO Multi-Agent Backend",
    description="Localized financial literacy & micro-triage API for East African deployment.",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url="/api/redoc"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HumanTakeoverRequest(BaseModel):
    member_id: str
    decision: str  # "approved" or "denied"
    reason: str

@app.get("/api/info")
def read_root():
    return {
        "service": "Ujima SACCO Multi-Agent Service",
        "compliance": "Kenya Data Protection Act 2022 compliant (Local Mock Mode)",
        "region": SOVEREIGN_CONFIG["STORAGE_REGION"]
    }

@app.post("/sms/inbound", response_model=SMSOutbound)
def inbound_sms(payload: SMSInbound):
    """
    USSD/SMS Inbound Entry Point. processes incoming member text,
    updates state thread, executes agent handoffs, and returns the response SMS.
    """
    # 1. Fetch or initialize member profile
    profile = db.get_profile(payload.member_id)
    if not profile:
        # Create standard anonymous profile to prevent crashes if a new member calls
        profile = MemberProfile(
            member_id=payload.member_id,
            name="SACCO Member",
            sub_county=payload.sub_county,
            gender="unknown",
            tribe="unknown",
            estimated_child_ages=[]
        )
    
    # 2. Get existing conversation state thread
    state = db.get_state(payload.member_id)
    
    # Track the inbound message in history
    state.conversation_history.append({"sender": "member", "text": payload.text})
    
    # 3. Invoke multi-agent orchestrator loop
    state, response_text = process_ussd_sms_loop(state, profile, payload.text)
    
    # 4. Save state back to mock db
    db.save_state(state)
    
    return SMSOutbound(member_id=payload.member_id, text=response_text)

@app.get("/human/queue")
def human_queue():
    """
    Dashboard endpoint for Human Loan Officers to inspect escalated applications
    and view Markdown briefing packets compiled by the Hunter Agent.
    """
    queue = []
    for member_id, state in db.states.items():
        if state.human_escalation_status == "pending_review":
            profile = db.get_profile(member_id)
            queue.append({
                "member_id": member_id,
                "name": profile.name if profile else "Unknown Member",
                "current_agent": state.current_agent,
                "assigned_officer": state.telemetry_metadata.get("assigned_officer"),
                "briefing_packet": state.telemetry_metadata.get("briefing_packet"),
                "loan_amount": state.loan_application.amount if state.loan_application else None,
                "repayment_date": state.loan_application.repayment_date if state.loan_application else None
            })
    return queue

@app.post("/human/takeover")
def human_takeover(req: HumanTakeoverRequest):
    """
    Resolves an escalated loan application via manual human coordinator input.
    """
    state = db.get_state(req.member_id)
    if state.human_escalation_status != "pending_review":
        raise HTTPException(
            status_code=400, 
            detail="Member application is not in the human review queue."
        )
        
    state.human_escalation_status = "resolved"
    state.current_agent = "scout"  # Hand conversation flow back to Scout Financial Coach
    
    # Finalize decision details
    if state.loan_application:
        state.loan_application.status = req.decision
        state.loan_application.decision_reason = f"Human Review ({req.reason})"
    else:
        state.loan_application = LoanApplication(
            amount=0.0,
            repayment_date="N/A",
            status=req.decision,
            decision_reason=f"Human Review ({req.reason})"
        )
        
    # Generate SMS notifying the member of human decision
    sms_text = f"Ujima SACCO Update: Human Officer has review your request and {req.decision} the loan. Reason: {req.reason}."
    
    # Intercept outbound messaging to enforce Dignity Lexicon rules
    filtered_sms = dignity_message_interceptor(sms_text)
    state.conversation_history.append({"sender": "hunter", "text": filtered_sms})
    db.save_state(state)
    
    return {
        "status": "success", 
        "decision": req.decision, 
        "sms_response": filtered_sms
    }

@app.get("/telemetry/status")
def telemetry_status():
    """
    System monitoring dashboard telemetry, reflecting anomaly alerts and general metrics.
    """
    alerts = get_anomaly_alerts()
    
    total_loans = 0
    approved_loans = 0
    denied_loans = 0
    escalated_loans = 0
    
    for state in db.states.values():
        if state.loan_application:
            total_loans += 1
            status = state.loan_application.status
            if status == "approved":
                approved_loans += 1
            elif status == "denied":
                denied_loans += 1
            elif status == "escalated":
                escalated_loans += 1
                
    return {
        "sovereign_configuration": SOVEREIGN_CONFIG,
        "anomaly_alerts": alerts,
        "aggregate_metrics": {
            "total_applications": total_loans,
            "approved": approved_loans,
            "escalated": escalated_loans
        }
    }

@app.get("/health")
def health_check():
    """
    Health check endpoint for deployment monitoring
    """
    return {
        "status": "healthy",
        "service": "Ujima SACCO",
        "environment": os.getenv("APP_ENV", "development")
    }

# Mount static files (frontend) - MUST be after all routes
STATIC_DIR = Path(__file__).parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True))
