import json

from gemini_client import get_gemini_client
from claim_extractor import extract_claim_data
from eligibility_checker import determine_eligibility
from explanation_generator import generate_decision_explanation


def main():
    client = get_gemini_client()

    sample_claim_document = """
Claim Form

Patient Name: Mary Wong
Policy ID: POL-1001
Claim ID: CLM-8891
Claim Type: Outpatient

Provider Name: Healthy Life Clinic
Provider Registration Number: REG-88291

Treatment Date: 2026-06-10
Diagnosis: Influenza
Procedure: General Consultation

Total Amount: HKD 280

Doctor: Dr. Lee
Receipt includes clinic stamp.
"""

    print("\n--- Claim Document ---")
    print(sample_claim_document)

    print("\n--- Step 1: Extracting claim data with Gemini ---")
    claim_data = extract_claim_data(client, sample_claim_document)
    print(json.dumps(claim_data, indent=2))

    print("\n--- Step 2: Determining eligibility ---")
    eligibility_result = determine_eligibility(claim_data)
    print(json.dumps(eligibility_result, indent=2))

    print("\n--- Step 3: Generating Gemini explanation ---")
    explanation = generate_decision_explanation(
        client,
        claim_data,
        eligibility_result
    )
    print(explanation)


if __name__ == "__main__":
    main()