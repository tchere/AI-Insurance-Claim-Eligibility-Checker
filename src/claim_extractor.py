import json
from google.genai import types


def extract_claim_data(client, document_text):
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
- Return JSON only.

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