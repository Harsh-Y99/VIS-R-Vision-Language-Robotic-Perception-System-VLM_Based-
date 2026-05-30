import re

def parse_vlm_response(text):
    """Extract structured info from VLM response (deep format)."""
    risk_level = "LOW"
    description = ""
    suggested_action = ""

    # Extract RISK_LEVEL
    match = re.search(r'RISK_LEVEL:\s*(LOW|MEDIUM|HIGH)', text, re.IGNORECASE)
    if match:
        risk_level = match.group(1).upper()

    # Extract DESCRIPTION
    match = re.search(r'DESCRIPTION:\s*(.*?)(?=SUGGESTED_ACTION:|$)', text, re.IGNORECASE | re.DOTALL)
    if match:
        description = match.group(1).strip()

    # Extract SUGGESTED_ACTION
    match = re.search(r'SUGGESTED_ACTION:\s*(.*?)$', text, re.IGNORECASE)
    if match:
        suggested_action = match.group(1).strip()

    return {
        'risk_level': risk_level,
        'description': description,
        'suggested_action': suggested_action,
        'raw': text
    }

def parse_fast_response(text):
    """Parse fast response from Moondream2 for risk flag."""
    risk_flag = "YES" in text.upper()
    return {
        'risk_flag': risk_flag,
        'description': text.strip()
    }