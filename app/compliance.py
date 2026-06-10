import re
from typing import Dict, Any, List, Tuple
from app.models import StateThread

# --- DATA SOVEREIGNTY ARCHITECTURE (Kenya Data Protection Act 2022 compliance) ---
# Enforce that all memory buffers and database bindings map strictly to African Cloud zones.
SOVEREIGN_CONFIG = {
    "STORAGE_REGION": "af-south-1",  # AWS Cape Town (local Africa deployment region)
    "DATA_RESIDENCY": "Kenya-Nairobi-Mock-DC",
    "ENCRYPTION_STANDARD": "AES-256-GCM-LOCAL",
    "ALLOW_OUTBOUND_FOREIGN_TRANSFER": False
}

def verify_data_residency(destination_uri: str) -> bool:
    """
    Validates that database connections and S3 targets do not leak outside sovereign African borders.
    """
    if "amazonaws.com" in destination_uri and "af-south-1" not in destination_uri:
        raise ConnectionError(
            f"DATA SOVEREIGNTY VIOLATION: Attempted to connect to {destination_uri}. "
            "Under the Kenya Data Protection Act 2022, financial customer data must remain within sovereign bounds."
        )
    return True


# --- BIAS MITIGATION FILTER ---
# Scrubs and flags ML proxy variables for gender (e.g. crop types, titles) or ethnicity (clan-based locations).
GENDER_PROXIES = {"matooke", "shea_butter", "traditional_weaving", "cassava"}
ETHNICITY_PROXIES = {"clan_leader", "ancestral_homestead", "tribe_origin"}

def scrub_sensitive_proxies(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Custom validation interceptor to scrub features or heavily flag proxy variables for gender or ethnicity.
    """
    scrubbed = {}
    flagged_keys = []
    
    # Direct scrubbing of explicit labels
    sensitive_keys = {"gender", "tribe", "ethnicity", "clan"}
    
    for k, v in features.items():
        if k in sensitive_keys:
            flagged_keys.append(k)
            continue # Scrub completely
            
        # Check proxy variables
        if isinstance(v, str):
            val_lower = v.lower()
            # If crop or metadata is a gender proxy
            if val_lower in GENDER_PROXIES or any(p in val_lower for p in GENDER_PROXIES):
                flagged_keys.append(f"{k} (gender proxy)")
                scrubbed[k] = "[REDACTED_GENDER_PROXY]"
                continue
            if val_lower in ETHNICITY_PROXIES or any(p in val_lower for p in ETHNICITY_PROXIES):
                flagged_keys.append(f"{k} (ethnicity proxy)")
                scrubbed[k] = "[REDACTED_ETHNICITY_PROXY]"
                continue
        
        scrubbed[k] = v
        
    if flagged_keys:
        # We append a telemetry flag to alert downstream logic of potential bias
        scrubbed["_bias_mitigation_alerts"] = flagged_keys
        
    return scrubbed


# --- DIGNITY LEXICON GUARDRAIL ---
# Intercepts outgoing messages, replacing harsh clinical banking terms with empathetic educational language.
PROHIBITED_BANKING_LEXICON = {
    "unreliable": "subject to seasonal fluctuations",
    "high risk": "experiencing temporary agricultural cash flow changes",
    "insolvent": "in need of a harvest buffer adjustment",
    "bad debtor": "navigating a seasonal liquidity transition",
    "defaulted": "awaiting the harvest buffer window"
}

def dignity_message_interceptor(message: str) -> str:
    """
    Inspects outgoing messaging payloads. If prohibited terms are found, they are rewritten
    using empathetic, educational language explaining how seasonal buffers protect the member's financial standing.
    """
    rewritten_message = message
    found_violations = False
    
    for prohibited_word, friendly_phrase in PROHIBITED_BANKING_LEXICON.items():
        # Case insensitive search
        pattern = re.compile(re.escape(prohibited_word), re.IGNORECASE)
        if pattern.search(rewritten_message):
            found_violations = True
            rewritten_message = pattern.sub(friendly_phrase, rewritten_message)
            
    if found_violations:
        # Add educational framing to explain seasonal buffers
        rewritten_message += (
            " Ujima SACCO works with you: we know seasonal cash-flow is tied to "
            "your harvest cycle, and we structure repayment to protect your crop returns."
        )
    return rewritten_message


# --- TELEMETRY ANOMALY DETECTION ---
# Mock storage of historical approvals per sub-county.
# Key: sub_county, Value: list of bool (True = Approved, False = Denied) in chronological order.
sub_county_loan_history: Dict[str, List[bool]] = {}
system_anomaly_alerts: List[str] = []

def record_and_analyze_telemetry(sub_county: str, approved: bool) -> bool:
    """
    Appends the approval status to a windowed sub-county log.
    Triggers a system-wide flag if the approval rate drops by >30% relative to a baseline moving average.
    Returns True if an anomaly is detected, False otherwise.
    """
    if sub_county not in sub_county_loan_history:
        # Initialize with baseline approvals (e.g., 8 approvals out of 10 for a baseline rate of 80%)
        sub_county_loan_history[sub_county] = [True, True, True, False, True, True, True, False, True, True]
        
    # Baseline approval rate is the moving average of the first 10 elements (historical baseline)
    baseline_history = sub_county_loan_history[sub_county][:10]
    baseline_rate = sum(1 for x in baseline_history if x) / len(baseline_history)
    
    # Append new transaction
    sub_county_loan_history[sub_county].append(approved)
    
    # Calculate the current rate of the last 5 decisions (current sliding window)
    recent_window = sub_county_loan_history[sub_county][-5:]
    recent_rate = sum(1 for x in recent_window if x) / len(recent_window)
    
    # Check drop percentage
    # (Baseline - Recent) / Baseline
    # E.g. baseline 80% (0.8), recent 50% (0.5). Drop is (0.8 - 0.5)/0.8 = 37.5%
    if baseline_rate > 0:
        drop_percentage = (baseline_rate - recent_rate) / baseline_rate
        if drop_percentage >= 0.30:
            alert_msg = f"ANOMALY: Approval rate for {sub_county} dropped by {drop_percentage:.1%}. Baseline: {baseline_rate:.1%}, Recent: {recent_rate:.1%}"
            if alert_msg not in system_anomaly_alerts:
                system_anomaly_alerts.append(alert_msg)
            return True
            
    return False

def get_anomaly_alerts() -> List[str]:
    return system_anomaly_alerts

def clear_anomaly_alerts():
    system_anomaly_alerts.clear()
