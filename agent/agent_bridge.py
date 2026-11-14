"""agent_bridge.py

Connects Python agent code to JavaScript agent files (finance.js, planning_agent.js, verification_agent.js)
via Node.js subprocess execution.

Allows Python code to directly invoke JavaScript agents and receive structured Python dictionaries.
"""
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Union

AGENT_DIR = Path(__file__).resolve().parent


def _run_node_script(script_name: str, payload: Union[Dict[str, Any], List[Any]]) -> Any:
    """Executes a JavaScript agent script using Node.js and returns the parsed JSON response.

    Args:
        script_name: Filename of the JavaScript script in agent/ (e.g., 'finance.js').
        payload: Python list or dict to pass to the script as JSON.

    Returns:
        Parsed JSON output (dict or list) from the Node.js script.

    Raises:
        FileNotFoundError: If the script is missing.
        RuntimeError: If Node.js is not found, execution fails, or output is invalid JSON.
    """
    script_path = AGENT_DIR / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Agent script not found: {script_path}")

    input_json = json.dumps(payload)

    try:
        proc = subprocess.run(
            ["node", str(script_path), input_json],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError as e:
        raise RuntimeError("Node.js ('node') is not installed or not found in PATH.") from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"Execution of {script_name} timed out after 10s.") from e

    if proc.returncode != 0:
        err = proc.stderr.strip() or f"Process exited with code {proc.returncode}"
        raise RuntimeError(f"Error from {script_name}: {err}")

    output_str = proc.stdout.strip()
    if not output_str:
        raise RuntimeError(f"{script_name} returned empty output")

    try:
        return json.loads(output_str)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON received from {script_name}: {output_str}") from e


def calculate_financial_impact(sponsors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Finance Agent (calls finance.js).

    Job: Calculate total financial impact of sponsor commitment changes.
    Input: List of {'sponsor_name': str, 'old_amount': int, 'new_amount': int}
    Output: dict with previous_total_sponsorship, updated_total_sponsorship,
            total_difference, financial_status, sponsor_details
    """
    if not isinstance(sponsors, list):
        raise ValueError("sponsors must be a list of sponsor dictionaries")
    return _run_node_script("finance.js", sponsors)


def generate_event_plan(finance_data: Dict[str, Any]) -> Dict[str, Any]:
    """Planning Agent (calls planning_agent.js).

    Job: Take financial difference and return event budget recommendations & activity impacts.
    Input: {'total_difference': number}
    Output: dict with budget_status, total_budget_change, affected_activities,
            recommendations, approval_required
    """
    if not isinstance(finance_data, dict):
        raise ValueError("finance_data must be a dictionary")
    return _run_node_script("planning_agent.js", finance_data)


def verify_event_data_js(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """Verification Agent in JS (calls verification_agent.js).

    Job: Cross-check communication, knowledge, finance, and planning agent outputs.
    """
    if not isinstance(event_data, dict):
        raise ValueError("event_data must be a dictionary")
    return _run_node_script("verification_agent.js", event_data)


# ---------------------------------------------------------------- TESTS
def test_agent_bridge():
    print("Testing Python -> JS Agent Bridge...")

    # 1. Test Finance Agent (finance.js)
    finance_input = [
        {"sponsor_name": "ABC Technologies", "old_amount": 200000, "new_amount": 120000}
    ]
    fin_result = calculate_financial_impact(finance_input)
    assert fin_result["total_difference"] == -80000, fin_result
    assert fin_result["financial_status"] == "negative", fin_result
    assert len(fin_result["sponsor_details"]) == 1, fin_result
    print("  PASS: Python -> finance.js (total_difference:", fin_result["total_difference"], ")")

    # 2. Test Planning Agent (planning_agent.js)
    plan_input = {"total_difference": fin_result["total_difference"]}
    plan_result = generate_event_plan(plan_input)
    assert plan_result["budget_status"] == "budget_decreased", plan_result
    assert plan_result["total_budget_change"] == -80000, plan_result
    assert plan_result["approval_required"] is True, plan_result
    print("  PASS: Python -> planning_agent.js (budget_status:", plan_result["budget_status"], ")")

    # 3. Test JS Verification Agent (verification_agent.js)
    verify_input = {
        "communicationData": {
            "sponsor_name": "ABC Technologies",
            "old_amount": 200000,
            "new_amount": 120000,
            "change_type": "decrease",
        },
        "knowledgeData": {
            "record_found": True,
            "verification_status": "verified",
        },
        "financeData": fin_result,
        "planningData": plan_result,
    }
    verify_result = verify_event_data_js(verify_input)
    assert verify_result["overall_status"] == "passed", verify_result
    print("  PASS: Python -> verification_agent.js (overall_status:", verify_result["overall_status"], ")")

    # 4. Bad input handling
    try:
        calculate_financial_impact("invalid")
    except ValueError:
        print("  PASS: Bad input raises ValueError")
    else:
        raise AssertionError("Expected ValueError for bad input")

    print("\nALL BRIDGE TESTS PASSED")


if __name__ == "__main__":
    test_agent_bridge()
