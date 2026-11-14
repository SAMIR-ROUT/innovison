"""
run_update.py

Flow: read email -> get sponsors from the backend -> parse -> check against
database -> HUMAN approves -> PATCH -> verify.

Run:   python run_update.py                (uses the sample email)
       python run_update.py my_email.txt   (uses your own email text file)

Needs agent/.env with:
    API_URL=http://localhost:8000
    API_KEY=<the same key as in the backend .env>
"""
import os
import sys

import httpx
from dotenv import load_dotenv

from sponsor_parser import check_against_database, extract_sponsor_update
from agent_bridge import calculate_financial_impact, generate_event_plan
from verification import verifyEventData

SAMPLE_EMAIL = """
Sponsor: ABC Technologies

We previously committed Rs. 2,00,000.
Our revised contribution is Rs. 1,20,000.
The change is effective 20 December 2026.
"""


def backend_message(error):
    """Show the backend's own error message when there is one."""
    try:
        return error.response.json().get("message", error.response.text)
    except Exception:
        return error.response.text


def run(client, email_text, api_key, approve=input):
    # 1. Get the sponsors the database already knows
    response = client.get("/sponsors")
    response.raise_for_status()
    sponsors = response.json()
    if not isinstance(sponsors, list):
        print("Unexpected answer from GET /sponsors (expected a list). Stopping.")
        return False

    # 2. Parse the email, then check it against the database
    parsed = extract_sponsor_update(email_text, known_names=[s["name"] for s in sponsors])
    result = check_against_database(parsed, sponsors)
    print("\nPARSED RESULT")
    for key, value in result.items():
        print(f"  {key}: {value}")

    # 3. Anything unclear -> stop. A human must look at it.
    if result["manual_review_required"]:
        print("\nSTOPPED: manual review required. Nothing was changed.")
        return False

    # 3b. Multi-Agent cross-checks:
    #     - Finance Agent (finance.js via bridge)
    #     - Planning Agent (planning_agent.js via bridge)
    #     - Verification Agent (cross-checks all agent outputs)
    comm_data = {
        "sponsor_name": result["sponsor_name"],
        "old_amount": result["current_in_database"],
        "new_amount": result["new_amount"],
        "change_type": result["change_type"],
    }
    knowledge_data = {
        "record_found": True,
        "verification_status": "verified",
    }
    finance_data = calculate_financial_impact([comm_data])
    planning_data = generate_event_plan({"total_difference": finance_data["total_difference"]})
    verification = verifyEventData({
        "communicationData": comm_data,
        "knowledgeData": knowledge_data,
        "financeData": finance_data,
        "planningData": planning_data,
    })

    if verification.get("overall_status") != "passed":
        print(f"\nSTOPPED: Multi-agent verification failed: {verification.get('errors')}")
        return False

    print(
        f"\nMULTI-AGENT ANALYSIS:\n"
        f"  Finance Impact: difference {finance_data['total_difference']} ({finance_data['financial_status']})\n"
        f"  Planning Status: {planning_data['budget_status']} (activities affected: {len(planning_data['affected_activities'])})\n"
        f"  Verification: {verification['message']}"
    )

    # 4. Human approval (the Policy & Approval box in your diagram)
    print(
        f"\nPROPOSED CHANGE: {result['sponsor_name']} (id {result['sponsor_id']}): "
        f"{result['current_in_database']} -> {result['new_amount']} ({result['change_type']})"
    )
    if approve("Type 'yes' to apply this change: ").strip().lower() != "yes":
        print("Not approved. Nothing was changed.")
        return False

    # 5. Execute: PATCH (this needs the API key)
    note = "Agent: updated from sponsor email"
    if result["effective_date"]:
        note += f" (effective {result['effective_date']})"
    patch = client.patch(
        f"/sponsors/{result['sponsor_id']}",
        json={"current_commitment": result["new_amount"], "note": note},
        headers={"X-API-Key": api_key},
    )
    patch.raise_for_status()

    # 6. Verify: read the data again. Do not trust the PATCH answer alone.
    check = client.get(f"/sponsors/{result['sponsor_id']}")
    check.raise_for_status()
    saved = int(round(float(check.json()["current_commitment"])))
    history = client.get(f"/sponsors/{result['sponsor_id']}/history")
    history.raise_for_status()
    rows = history.json()

    if saved == result["new_amount"]:
        print(f"\nVERIFIED: database now shows {saved}. History rows for this sponsor: {len(rows)}")
        return True
    print(f"\nPROBLEM: expected {result['new_amount']} but database shows {saved}")
    return False


if __name__ == "__main__":
    load_dotenv()
    base_url = os.getenv("API_URL", "http://localhost:8000")
    api_key = os.getenv("API_KEY")
    if not api_key:
        sys.exit("API_KEY is missing. Put it in agent/.env (do not commit that file).")

    email_text = SAMPLE_EMAIL
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            email_text = f.read()

    try:
        with httpx.Client(base_url=base_url, timeout=10) as client:
            run(client, email_text, api_key)
    except httpx.ConnectError:
        sys.exit(f"Cannot reach the backend at {base_url}. Is Uvicorn running?")
    except httpx.HTTPStatusError as error:
        sys.exit(f"Backend refused: {error.response.status_code} - {backend_message(error)}")
