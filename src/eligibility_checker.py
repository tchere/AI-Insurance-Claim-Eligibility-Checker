from policy_database import POLICY_DATABASE


def determine_eligibility(claim_data):
    risk_score = 0
    checks = []

    policy_id = claim_data.get("policy_id")
    claim_type = claim_data.get("claim_type")
    claim_amount = claim_data.get("claim_amount")

    try:
        claim_amount = float(claim_amount) if claim_amount is not None else 0
    except (ValueError, TypeError):
        claim_amount = 0

    policy = POLICY_DATABASE.get(policy_id)

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

    if policy["status"] != "Active":
        risk_score += 40
        checks.append({
            "check": "Policy status",
            "status": "Failed",
            "reason": "Policy is not active.",
            "risk_points": 40
        })
    else:
        checks.append({
            "check": "Policy status",
            "status": "Passed",
            "reason": "Policy is active.",
            "risk_points": 0
        })

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
            "reason": "Patient name does not match the policyholder name or is missing.",
            "risk_points": 20
        })

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

    limit = 0

    if claim_type == "Outpatient":
        limit = policy["outpatient_limit"]
    elif claim_type == "Inpatient":
        limit = policy["inpatient_limit"]
    elif claim_type == "Dental":
        limit = policy["dental_limit"]

    if claim_amount <= 0:
        risk_score += 25
        checks.append({
            "check": "Claim amount",
            "status": "Failed",
            "reason": "Claim amount is missing or invalid.",
            "risk_points": 25
        })
    elif limit > 0 and claim_amount <= limit:
        checks.append({
            "check": "Claim amount",
            "status": "Passed",
            "reason": f"Claim amount {claim_amount} is within the allowed limit of {limit}.",
            "risk_points": 0
        })
    else:
        risk_score += 30
        checks.append({
            "check": "Claim amount",
            "status": "Failed",
            "reason": f"Claim amount {claim_amount} exceeds the allowed limit of {limit}.",
            "risk_points": 30
        })

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
            "status": "Warning",
            "reason": "Receipt stamp presence is unclear.",
            "risk_points": 10
        })

    missing_fields = claim_data.get("missing_fields", [])

    if missing_fields:
        points = min(len(missing_fields) * 5, 25)
        risk_score += points
        checks.append({
            "check": "Missing fields",
            "status": "Warning",
            "reason": f"Missing fields: {', '.join(missing_fields)}",
            "risk_points": points
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