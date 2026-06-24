# AI Insurance Claim Eligibility Checker

This project is a simple Python demo that uses **Google Gemini** to extract structured information from an insurance claim document, then applies local rule-based checks to decide whether the claim should be **approved**, **rejected**, or sent for **manual review**.

The project demonstrates how an AI model can support insurance claim processing by combining:

- Document information extraction
- Policy validation
- Coverage checking
- Claim amount limit checking
- Risk scoring
- AI-generated decision explanation

---

## Features

- Extracts claim details from unstructured claim text using Gemini
- Returns structured JSON claim data
- Checks whether the policy exists
- Checks whether the policy is active
- Compares patient name against policyholder name
- Validates claim type against covered benefits
- Checks claim amount against policy limits
- Checks receipt stamp presence
- Detects missing fields
- Calculates a risk score
- Produces a final decision:
  - `APPROVE`
  - `MANUAL REVIEW`
  - `REJECT`
- Generates a professional explanation of the decision using Gemini

---

## Tech Stack

- Python
- Google Gemini API / Gemini Enterprise
- `google-genai`
- Local rule-based policy database

---

## Project Structure

```text
AI-checker/
├── src/
│   └── claim_checker/
│       ├── __init__.py
│       ├── config.py
│       ├── gemini_client.py
│       ├── claim_extractor.py
│       ├── policy_database.py
│       ├── eligibility_checker.py
│       └── explanation_generator.py
├── main.py
├── requirements.txt
└── README.md

