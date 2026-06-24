import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types


# Load API key from .env
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found. Please add it to your .env file.")

# For Gemini Enterprise Agent Platform express mode
client = genai.Client(
    vertexai=True,
    api_key=GEMINI_API_KEY
)


# --------------------------------------------------
# Step 1: Gemini extracts claim data from document text
# --------------------------------------------------

def extract_claim_data(document_text):
    """
    Uses Gemini Enterprise Agent Platform API to extract structured claim data
    from claim document text.
    """

    prompt = f"""
You are an AI claim document extraction assistant.

Extract the important information from the claim document below.

Return only valid JSON with this exact structure:

{{
  "patient_name": null,
  "policy_id": null,
  "claim_id": null,
  "claim_type": null,
  "provider_name": null,
  "provider_registration_number": null,
  "treatment_date": null,
  "diagnosis": null,
  "procedure": null,
  "claim_amount": null,
  "currency": null,
  "receipt_stamp_present": null,
  "doctor_name": null,
  "document_authenticity_notes": [],
  "missing_fields": []
}}

Rules:
- Do not invent information.
- If information is missing, use null.
- claim_type should be one of: "Outpatient", "Inpatient", "Dental", "Vision", "Unknown".
- claim_amount should be a number only.
- receipt_stamp_present should be true, false, or null.
- document_authenticity_notes should mention anything unusual about the document.
- missing_fields should list important fields that are missing.
- Return JSON only.
- Do not include markdown.

Claim document:
{document_text}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )

    return json.loads(response.text)


# --------------------------------------------------
# Step 2: Local policy database for demo
# --------------------------------------------------

POLICY_DATABASE = {
    "POL-1001": {
        "policyholder_name": "Mary Wong",
        "status": "Active",
        "coverage": ["Outpatient", "Dental"],
        "outpatient_limit": 1000,
        "inpatient_limit": 10000,
        "dental_limit": 800,
        "currency": "HKD"
    },
    "POL-1002": {
        "policyholder_name": "Alex Ho",
        "status": "Active",
        "coverage": ["Outpatient", "Inpatient"],
        "outpatient_limit": 1500,
        "inpatient_limit": 20000,
        "dental_limit": 0,
        "currency": "HKD"
    },
    "POL-1003": {
        "policyholder_name": "John Tan",
        "status": "Expired",
        "coverage": ["Outpatient"],
        "outpatient_limit": 1000,
        "inpatient_limit": 0,
        "dental_limit": 0,
        "currency": "HKD"
    }
}


# --------------------------------------------------
# Step 3: Determine eligibility using rules
# --------------------------------------------------

def determine_eligibility(claim_data):
    """
    Compares extracted claim details with policy coverage.
    Returns decision, risk score, and rule checks.
    """

    risk_score = 0
    checks = []

    policy_id = claim_data.get("policy_id")
    claim_type = claim_data.get("claim_type")
    claim_amount = claim_data.get("claim_amount")

    try:
        claim_amount = float(claim_amount) if claim_amount is not None else 0
    except ValueError:
        claim_amount = 0

    policy = POLICY_DATABASE.get(policy_id)

    # Check policy exists
    if not policy:
        risk_score += 40
        checks.append({
            "check": "Policy existence",
            "status": "Failed",
            "reason": "Policy ID was not found in the policy database.",
            "risk_points": 40
        })

        return {
            "decision": "REJECT",
            "risk_score": min(risk_score, 100),
            "checks": checks,
            "policy": None
        }

    checks.append({
        "check": "Policy existence",
        "status": "Passed",
        "reason": "Policy ID was found.",
        "risk_points": 0
    })

    # Check policy status
    if policy["status"] != "Active":
        risk_score += 40
        checks.append({
            "check": "Policy status",
            "status": "Failed",
            "reason": f"Policy status is {policy['status']}, not Active.",
            "risk_points": 40
        })
    else:
        checks.append({
            "check": "Policy status",
            "status": "Passed",
            "reason": "Policy is active.",
            "risk_points": 0
        })

    # Check patient name match
    extracted_name = str(claim_data.get("patient_name") or "").lower()
    policyholder_name = str(policy.get("policyholder_name") or "").lower()

    if extracted_name and policyholder_name and extracted_name == policyholder_name:
        checks.append({
            "check": "Patient name match",
            "status": "Passed",
            "reason": "Patient name matches the policyholder name.",
            "risk_points": 0
        })
    else:
        risk_score += 20
        checks.append({
            "check": "Patient name match",
            "status": "Warning",
            "reason": "Patient name does not match or is missing.",
            "risk_points": 20
        })

    # Check claim type coverage
    if claim_type in policy["coverage"]:
        checks.append({
            "check": "Coverage type",
            "status": "Passed",
            "reason": f"{claim_type} is covered by the policy.",
            "risk_points": 0
        })
    else:
        risk_score += 35
        checks.append({
            "check": "Coverage type",
            "status": "Failed",
            "reason": f"{claim_type} is not covered by the policy.",
            "risk_points": 35
        })

    # Check claim amount limit
    limit = 0

    if claim_type == "Outpatient":
        limit = policy["outpatient_limit"]
    elif claim_type == "Inpatient":
        limit = policy["inpatient_limit"]
    elif claim_type == "Dental":
        limit = policy["dental_limit"]

    if claim_amount <= 0:
        risk_score += 20
        checks.append({
            "check": "Claim amount",
            "status": "Failed",
            "reason": "Claim amount is missing or invalid.",
            "risk_points": 20
        })
    elif limit > 0 and claim_amount <= limit:
        checks.append({
            "check": "Claim amount limit",
            "status": "Passed",
            "reason": f"Claim amount {claim_amount} is within the policy limit of {limit}.",
            "risk_points": 0
        })
    else:
        risk_score += 30
        checks.append({
            "check": "Claim amount limit",
            "status": "Failed",
            "reason": f"Claim amount {claim_amount} exceeds the policy limit of {limit}.",
            "risk_points": 30
        })

    # Check receipt stamp
    if claim_data.get("receipt_stamp_present") is True:
        checks.append({
            "check": "Receipt stamp",
            "status": "Passed",
            "reason": "Receipt stamp is present.",
            "risk_points": 0
        })
    elif claim_data.get("receipt_stamp_present") is False:
        risk_score += 20
        checks.append({
            "check": "Receipt stamp",
            "status": "Warning",
            "reason": "Receipt stamp is missing.",
            "risk_points": 20
        })
    else:
        risk_score += 10
        checks.append({
            "check": "Receipt stamp",
            "status": "Unclear",
            "reason": "Receipt stamp information is unclear.",
            "risk_points": 10
        })

    # Check missing important fields
    missing_fields = claim_data.get("missing_fields", [])

    if missing_fields:
        risk_points = min(len(missing_fields) * 5, 25)
        risk_score += risk_points
        checks.append({
            "check": "Missing fields",
            "status": "Warning",
            "reason": f"Missing fields: {', '.join(missing_fields)}",
            "risk_points": risk_points
        })
    else:
        checks.append({
            "check": "Missing fields",
            "status": "Passed",
            "reason": "No important fields are missing.",
            "risk_points": 0
        })

    risk_score = min(risk_score, 100)

    if risk_score < 30:
        decision = "APPROVE"
    elif risk_score < 70:
        decision = "MANUAL REVIEW"
    else:
        decision = "REJECT"

    return {
        "decision": decision,
        "risk_score": risk_score,
        "checks": checks,
        "policy": policy
    }


# --------------------------------------------------
# Step 4: Gemini explains the decision
# --------------------------------------------------

def generate_decision_explanation(claim_data, eligibility_result):
    """
    Uses Gemini Enterprise Agent Platform API to generate a professional explanation.
    """

    prompt = f"""
You are an AI insurance claim decision assistant.

Generate a clear explanation for the claim decision.

Extracted claim data:
{json.dumps(claim_data, indent=2)}

Eligibility result:
{json.dumps(eligibility_result, indent=2)}

Instructions:
- Keep the explanation professional and simple.
- Do not accuse anyone of fraud.
- Say "potential risk indicator" instead of "fraud".
- Explain why the claim is approved, rejected, or sent for manual review.
- Include the next recommended action.
- Use this format:

Summary:
Eligibility Result:
Key Checks:
Recommended Next Action:
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text


# --------------------------------------------------
# Step 5: Main program
# --------------------------------------------------

def main():
    sample_claim_document = """
    Claim Form

    Patient Name: Mary Wong
    Policy ID: POL-1001
    Claim ID: CLM-8891
    Claim Type: Outpatient

    Provider: Healthy Life Clinic
    Provider Registration Number: REG-88291
    Doctor: Dr. Lee

    Treatment Date: 2026-06-10
    Diagnosis: Influenza
    Procedure: General Consultation

    Total Amount: HKD 280

    Receipt includes clinic stamp.
    """

    print("\n--- Claim Document ---")
    print(sample_claim_document)

    print("\n--- Step 1: Extracting claim data with Gemini Enterprise Agent Platform ---")
    claim_data = extract_claim_data(sample_claim_document)
    print(json.dumps(claim_data, indent=2))

    print("\n--- Step 2: Determining eligibility ---")
    eligibility_result = determine_eligibility(claim_data)
    print(json.dumps(eligibility_result, indent=2))

    print("\n--- Step 3: Generating Gemini Enterprise Agent Platform explanation ---")
    explanation = generate_decision_explanation(claim_data, eligibility_result)
    print(explanation)


if __name__ == "__main__":
    main()