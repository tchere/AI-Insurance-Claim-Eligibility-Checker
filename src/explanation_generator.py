import json


def generate_decision_explanation(client, claim_data, eligibility_result):
    prompt = f"""
You are an AI insurance claim decision assistant.

Generate a clear explanation for the claim decision.

Extracted claim data:
{json.dumps(claim_data, indent=2)}

Eligibility result:
{json.dumps(eligibility_result, indent=2)}

Requirements:
- Use simple language.
- Explain why the claim was approved, rejected, or sent to manual review.
- Mention the main checks that passed or failed.
- Do not accuse anyone of fraud.
- Say "potential risk indicator" instead of "fraud".
- Keep the explanation professional.

Use this format:

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