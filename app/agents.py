import re
from datetime import datetime
from typing import Tuple, Dict, Any, List, Optional
from app.models import StateThread, MemberProfile, LoanApplication
from app.compliance import (
    verify_data_residency,
    scrub_sensitive_proxies,
    dignity_message_interceptor,
    record_and_analyze_telemetry
)

# --- MOCK HUMAN OFFICERS SCHEDULE/SPECIALIST MATRIX ---
HUMAN_OFFICERS = [
    {"name": "Sarah", "specialty": "maize", "available_days": ["Monday", "Tuesday", "Wednesday"]},
    {"name": "John", "specialty": "shea_butter", "available_days": ["Wednesday", "Thursday", "Friday"]},
    {"name": "Amina", "specialty": "matooke", "available_days": ["Monday", "Thursday", "Friday"]},
    {"name": "David", "specialty": "salaried", "available_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]}
]

# --- CULTURAL METAPHORS FOR SCOUT TIPS ---
CULTURAL_TIPS = [
    "Just as a single matooke tree needs support to hold its heavy fruit, we build our savings slowly to support our families in dry months.",
    "A wise farmer does not sell all the maize right at the harvest; they store a portion in the granary to protect against market fluctuations.",
    "Like the shea tree that takes years to mature and yields valuable butter, consistent daily tokens grow into strong financial safety nets.",
    "Do not plant all your seeds in one corner of the shamba. Diversifying your income streams is like planting cassava alongside your maize."
]

def parse_loan_amount(text: str) -> Optional[float]:
    """
    Tries to extract numbers from the message representing requested loan amounts.
    E.g. 'loan 10000', 'need KES 15,000', 'apply 5000'
    """
    text_clean = text.replace(",", "")
    match = re.search(r'(?:loan|kes|apply|borrow|need)\s*(\d+)', text_clean, re.IGNORECASE)
    if match:
        return float(match.group(1))
    # General fallback to checking any standalone numeric strings
    numbers = re.findall(r'\b\d{3,6}\b', text_clean)
    if numbers:
        return float(numbers[0])
    return None

def determine_repayment_date(current_date: datetime) -> Tuple[str, bool]:
    """
    Calculates agricultural liquidity peak months in Kenya (March/April or September/October).
    Returns a tuple of (Repayment Date String YYYY-MM-DD, IsAlignedWithHarvestPeak)
    """
    month = current_date.month
    year = current_date.year
    
    # Check alignment and schedule next harvest month
    # March (3), April (4), September (9), October (10)
    if month in [11, 12, 1, 2]:
        # Target March/April of this year
        repayment_month = 4
        repayment_year = year if month != 11 and month != 12 else year + 1
        aligned = True
    elif month in [5, 6, 7, 8]:
        # Target October of this year
        repayment_month = 10
        repayment_year = year
        aligned = True
    elif month in [3, 4]:
        # Currently in peak, repayment scheduled for next peak (September/October)
        repayment_month = 10
        repayment_year = year
        aligned = True
    elif month in [9, 10]:
        # Currently in peak, repayment scheduled for next peak (March/April next year)
        repayment_month = 4
        repayment_year = year + 1
        aligned = True
    else:
        repayment_month = 10
        repayment_year = year
        aligned = False
        
    repayment_date = f"{repayment_year:04d}-{repayment_month:02d}-15"
    return repayment_date, aligned

# --- AGENT PIPELINES ---

def run_scout_agent(state: StateThread, profile: MemberProfile, inbound_text: str) -> Tuple[StateThread, str]:
    """
    Scout Agent (Financial Literacy Coach)
    - Reads profile (read-only), writes to conversation history.
    - Generates cultural metaphor financial tips.
    - Intercepts stressful inputs for automated handoff to Guardian Agent.
    """
    # Check for intense stress triggers or loan intent
    stress_keywords = [
        "school fees", "drought", "crops died", "hunger", "no money", 
        "debt collector", "loan shark", "died", "ruined", "failed", "starving"
    ]
    loan_keywords = ["loan", "borrow", "apply"]
    
    text_lower = inbound_text.lower()
    has_stress = any(kw in text_lower for kw in stress_keywords)
    has_loan_intent = any(kw in text_lower for kw in loan_keywords)
    
    # Process stress or loan intent event - Hand off to Guardian
    if has_stress or has_loan_intent:
        # Extract stress indicators
        child_ages_under_5 = [age for age in profile.estimated_child_ages if age < 5]
        next_harvest = profile.last_harvest_month or 10  # fallback to Oct
        token_bal = profile.current_token_balance
        
        # Log stress flags
        state.financial_stress_flags.append("INTENSE_STRESS_DETECTED")
        if len(child_ages_under_5) >= 2:
            state.financial_stress_flags.append("VULNERABLE_CHILDREN_UNDER_5")
            
        state.harvest_cycle_context.update({
            "estimated_child_ages": profile.estimated_child_ages,
            "next_crop_harvest_month": next_harvest,
            "current_token_balance": token_bal
        })
        
        # Transition state
        state.current_agent = "guardian"
        # Run Guardian transition message
        handoff_msg = "SYSTEM HANDOFF: Scout Coach detected financial pressure. Engaging Guardian Loan Triage..."
        state.conversation_history.append({"sender": "scout", "text": handoff_msg})
        
        # Execute Guardian right away in the loop
        return run_guardian_agent(state, profile, inbound_text)
    
    # Regular Scout behavior - Financial Tip
    # Check SMS daily limit (max 3/day simulation)
    scout_sms_count = sum(1 for m in state.conversation_history if m.get("sender") == "scout" and "Tip:" in m.get("text", ""))
    
    if scout_sms_count >= 3:
        response_text = "Habari. You have received your daily financial literacy tips. Keep practicing your seasonal savings!"
    else:
        # Select tip based on crop type or cycle
        tip_index = len(state.conversation_history) % len(CULTURAL_TIPS)
        tip = CULTURAL_TIPS[tip_index]
        response_text = f"Tip: {tip}"
        
        # Enforce rule: Scout must never recommend specific loan products
        if "loan" in response_text.lower() or "borrow" in response_text.lower():
            # Fallback scrub to guarantee safety
            response_text = "Tip: Focus on building your seasonal granary buffer to shield your family."
            
    state.conversation_history.append({"sender": "scout", "text": response_text})
    return state, response_text


def run_guardian_agent(state: StateThread, profile: MemberProfile, inbound_text: str) -> Tuple[StateThread, str]:
    """
    Guardian Agent (Loan Triage System)
    - Low temperature computation (strict rules).
    - Checks loan limits (KES 15,000 threshold).
    - Syncs repayment with agricultural peak liquidity months.
    - Escalates high-risk applications to Hunter Agent.
    """
    # Check for manual takeover code
    if inbound_text.strip() == "*#733#":
        state.current_agent = "hunter"
        state.human_escalation_status = "pending_review"
        state.financial_stress_flags.append("MANUAL_HUMAN_TAKEOVER_REQUEST")
        esc_msg = "SMS Request: Escopement triggered. Transferring to Ujima human loan coordinator queue."
        state.conversation_history.append({"sender": "guardian", "text": esc_msg})
        return run_hunter_agent(state, profile, inbound_text)

    # Parse requested loan amount
    amount = parse_loan_amount(inbound_text)
    if not amount:
        # Default request if amount not found but reached triage
        amount = 10000.0

    # Calculate repayment alignment
    repayment_date, is_aligned = determine_repayment_date(datetime.now())
    
    # Compile telemetry risks
    telemetry_risks = []
    
    # 1. Income Variance Metric (Highly volatile seasonal vs salaried)
    variance_index = 0.9 if not profile.is_salaried else 0.1
    state.income_variance_metrics = {
        "is_salaried": profile.is_salaried,
        "variance_index": variance_index,
        "monthly_salary": profile.monthly_salary,
        "average_harvest_income": profile.average_harvest_income
    }
    if variance_index > 0.8:
        telemetry_risks.append("HIGH_INCOME_VARIANCE")
        
    # 2. Number of children under 5 (vulnerability index)
    children_under_5 = sum(1 for age in profile.estimated_child_ages if age < 5)
    if children_under_5 >= 2:
        telemetry_risks.append("MULTIPLE_UNDER_5_DEPENDENTS")
        
    # 3. Predatory Apps / Debt collectors trigger
    text_lower = inbound_text.lower()
    debt_trigger = "loan shark" in text_lower or "debt collector" in text_lower or "tala" in text_lower or "branch" in text_lower
    if debt_trigger:
        telemetry_risks.append("PREDATORY_APP_EXPOSURE")
        
    # 4. Token balance risk
    if profile.current_token_balance < 100.0:
        telemetry_risks.append("LOW_TOKEN_RESERVES")
        
    # Update state flags
    for risk in telemetry_risks:
        if risk not in state.financial_stress_flags:
            state.financial_stress_flags.append(risk)

    # ESCALATION TRIGGERS TO HUNTER:
    # (a) Amount > KES 15,000
    # (b) 2+ children under age 5 are flagged
    # (c) Inbound text references debt collectors or predatory apps
    should_escalate = (
        amount > 15000.0 or
        children_under_5 >= 2 or
        debt_trigger
    )
    
    if should_escalate:
        # Setup loan application in escalation mode
        state.loan_application = LoanApplication(
            amount=amount,
            repayment_date=repayment_date,
            status="escalated",
            decision_reason="Escalated due to risk profile or high loan amount request."
        )
        state.current_agent = "hunter"
        state.human_escalation_status = "pending_review"
        
        esc_msg = f"Application for KES {amount:.2f} escalated to Human Specialist."
        state.conversation_history.append({"sender": "guardian", "text": esc_msg})
        
        # Route to Hunter
        return run_hunter_agent(state, profile, inbound_text)

    # STRICT AUTO-APPROVAL DECISION LOOP:
    # Instantly auto-approve loans <= KES 15,000 ONLY IF repayment date aligns with agricultural peak liquidity.
    # Deny only if 3+ high-risk telemetry flags are tripped.
    is_approved = False
    decision_reason = ""
    
    if len(telemetry_risks) >= 3:
        is_approved = False
        decision_reason = f"Denied: {len(telemetry_risks)} telemetry risk indicators flagged."
    elif is_aligned:
        is_approved = True
        decision_reason = "Auto-approved: Amount within range and aligned with harvest liquidity peaks."
    else:
        is_approved = False
        decision_reason = "Denied: Repayment schedule does not align with regional agricultural peak liquidity months."

    # Record decision to telemetry and check for sub-county anomalies
    record_and_analyze_telemetry(profile.sub_county, is_approved)

    # Update state loan application
    state.loan_application = LoanApplication(
        amount=amount,
        repayment_date=repayment_date,
        status="approved" if is_approved else "denied",
        decision_reason=decision_reason
    )

    if is_approved:
        resp = f"Congratulations! Your loan of KES {amount:.2f} is approved. Repayment is scheduled for {repayment_date} to match your harvest sale returns."
    else:
        # Construct message using dignity lexicons (dignity_message_interceptor will filter it)
        resp = f"Your loan application of KES {amount:.2f} was unsuccessful. Reason: {decision_reason}"

    state.conversation_history.append({"sender": "guardian", "text": resp})
    return state, resp


def run_hunter_agent(state: StateThread, profile: MemberProfile, inbound_text: str) -> Tuple[StateThread, str]:
    """
    Hunter Agent (Human-in-the-Loop Coordinator)
    - Strict read-only workflow. Never issues approvals/denials.
    - Maps escalated packet to human officer schedule matrix.
    - Generates highly empathetic Markdown Briefing Packet.
    """
    # Find officer specialist based on crop or profile
    crop = (profile.crop_type or "salaried").lower()
    officer_name = "Sarah"  # Default
    
    for officer in HUMAN_OFFICERS:
        if officer["specialty"] == crop:
            officer_name = officer["name"]
            break
    else:
        # Fallback to salaried specialist if member is salaried or no crop specialty match
        if profile.is_salaried:
            for officer in HUMAN_OFFICERS:
                if officer["specialty"] == "salaried":
                    officer_name = officer["name"]
                    break

    # Calculate seasonal cash-flow runway
    harvest_month = profile.last_harvest_month or 10
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    harvest_name = months[harvest_month - 1]
    
    runway_desc = (
        f"Member income peaks during the {harvest_name} harvest cycle. "
        f"Current token balance of KES {profile.current_token_balance:.2f} serves as immediate liquidity cushion."
    )
    
    # Localized cross-sell recommendation
    cross_sell = "Ujima Drought Index Insurance"
    if crop == "maize":
        cross_sell = "Ujima Area Yield Index Insurance (Maize Guard)"
    elif crop == "shea_butter":
        cross_sell = "Kilimo Salama Shea Buffer Insurance"
    elif crop == "matooke":
        cross_sell = "Matooke Crop Yield Cover"

    # Construct the Briefing Packet (Markdown format)
    briefing_packet = (
        f"# Human Loan Officer Briefing Packet\n"
        f"**Assigned Specialist:** {officer_name}\n"
        f"**Escalation Status:** PENDING HUMAN REVIEW\n\n"
        f"### 1. Vendor Profile\n"
        f"- **Member ID:** {profile.member_id}\n"
        f"- **Name:** {profile.name}\n"
        f"- **Location (Sub-County):** {profile.sub_county}\n"
        f"- **Production Profile:** {crop.title()} Farmer/Vendor\n"
        f"- **Family Matrix:** {len(profile.estimated_child_ages)} children (Ages: {profile.estimated_child_ages})\n\n"
        f"### 2. Seasonal Cash-Flow Runway\n"
        f"- {runway_desc}\n"
        f"- **Income Variance Index:** {state.income_variance_metrics.get('variance_index', 0.9)}\n\n"
        f"### 3. Risk Mitigation Factors\n"
        f"- Current Stress Flags: {', '.join(state.financial_stress_flags)}\n"
        f"- Repayment dates set during local liquidity peaks protect crop returns and minimize default risk.\n\n"
        f"### 4. Localized Recommendation & Cross-Sell\n"
        f"- **Cross-sell Target:** {cross_sell}\n"
        f"- **Action:** Recommend structuring loan repayment dates around {harvest_name} with drought insurance premium bundled."
    )

    # Store Briefing Packet inside telemetry or context
    state.telemetry_metadata["briefing_packet"] = briefing_packet
    state.telemetry_metadata["assigned_officer"] = officer_name
    
    resp_text = f"Your request has been prioritized for human review. Officer {officer_name} is evaluating your seasonal flow buffers."
    state.conversation_history.append({"sender": "hunter", "text": resp_text})
    
    return state, resp_text


# --- COORDINATOR ENGINE (ORCHESTRATION LOOP) ---

def process_ussd_sms_loop(
    state: StateThread, 
    profile: MemberProfile, 
    inbound_text: str,
    db_destination_uri: str = "mongodb://localhost:27017/ujima_sacco?authSource=admin"
) -> Tuple[StateThread, str]:
    """
    Main stateful orchestrator loop that manages routing, commands, database sovereignty,
    scrubbing of bias, and intercepting outgoing text through the dignity filter.
    """
    # 1. Enforce Data Sovereignty rules
    verify_data_residency(db_destination_uri)
    
    # 2. Check runtime USSD commands
    cleaned_input = inbound_text.strip()
    
    # USSD Pause Command: *#700#
    if cleaned_input == "*#700#":
        state.paused = not state.paused
        status = "PAUSED" if state.paused else "RESUMED"
        msg = f"Ujima SACCO notification service is now {status}. Send *#700# to toggle."
        state.conversation_history.append({"sender": "system", "text": msg})
        return state, msg
        
    if state.paused:
        # Silent ignore or return paused indicator
        return state, "Ujima service is currently paused. Text *#700# to resume."

    # USSD Takeover / Human takeover hook: *#733#
    if cleaned_input == "*#733#":
        state.current_agent = "hunter"
        state.human_escalation_status = "pending_review"
        state.financial_stress_flags.append("MANUAL_HUMAN_TAKEOVER_REQUEST")
        esc_msg = "Human takeover command received. Application routed to human queue."
        state.conversation_history.append({"sender": "system", "text": esc_msg})
        state, output_text = run_hunter_agent(state, profile, inbound_text)
        
        # Apply Outbound Dignity Filter
        filtered_output = dignity_message_interceptor(output_text)
        return state, filtered_output

    # 3. Apply Bias Mitigation Filter on profile/metadata variables before agent logic
    raw_features = {
        "gender": profile.gender,
        "tribe": profile.tribe,
        "crop_type": profile.crop_type,
        "sub_county": profile.sub_county
    }
    scrubbed_features = scrub_sensitive_proxies(raw_features)
    state.telemetry_metadata["scrubbed_features"] = scrubbed_features
    if "_bias_mitigation_alerts" in scrubbed_features:
        state.telemetry_metadata["bias_mitigation_alerts"] = scrubbed_features["_bias_mitigation_alerts"]

    # 4. Route to current agent
    if state.current_agent == "scout":
        state, output_text = run_scout_agent(state, profile, inbound_text)
    elif state.current_agent == "guardian":
        state, output_text = run_guardian_agent(state, profile, inbound_text)
    elif state.current_agent == "hunter":
        state, output_text = run_hunter_agent(state, profile, inbound_text)
    else:
        # Fallback to scout
        state.current_agent = "scout"
        state, output_text = run_scout_agent(state, profile, inbound_text)

    # 5. Dignity Lexicon Guardrail - Intercept outgoing SMS response
    filtered_output = dignity_message_interceptor(output_text)
    
    # If the dignity filter updated the text, make sure the updated text is logged in the history
    if filtered_output != output_text:
        if state.conversation_history:
            state.conversation_history[-1]["text"] = filtered_output

    return state, filtered_output
