"""Verification agent for Event Second Brain.

Run the tests with:  python verification.py
"""


def _is_money(value):
    # Money must be a whole number. bool is a subclass of int in Python,
    # so True/False must be rejected on purpose.
    return isinstance(value, int) and not isinstance(value, bool)


def _clean_input(name, item, errors):
    # A backend error looks like {"error": true, "message": "...", "status_code": 404}.
    # Report it. Anything that is not a dict is treated as missing.
    if isinstance(item, dict) and item.get("error") is True:
        errors.append(
            f"{name} is a backend error: {item.get('message')} "
            f"(status {item.get('status_code')})."
        )
        return None
    if not isinstance(item, dict):
        return None
    return item


def verifyEventData(data):
    errors = []
    warnings = []

    # Bad top-level input must not crash.
    if not isinstance(data, dict):
        return {
            "overall_status": "review_required",
            "errors": ["Input data is missing or is not a dictionary."],
            "warnings": [],
            "message": "Some information requires correction or manual review.",
        }

    communicationData = _clean_input("communicationData", data.get("communicationData"), errors)
    knowledgeData = _clean_input("knowledgeData", data.get("knowledgeData"), errors)
    financeData = _clean_input("financeData", data.get("financeData"), errors)
    planningData = _clean_input("planningData", data.get("planningData"), errors)

    expected_difference = None

    # 1. Check communication data
    if communicationData is None:
        errors.append("Communication data is missing.")
    else:
        name = communicationData.get("sponsor_name")
        if not (isinstance(name, str) and name.strip()):
            errors.append("Sponsor name is missing.")

        oldAmount = communicationData.get("old_amount")
        newAmount = communicationData.get("new_amount")
        if not _is_money(oldAmount) or not _is_money(newAmount):
            errors.append("Invalid or missing sponsor amounts.")
        else:
            # 2. Check whether change type is correct
            expectedChange = (
                "increase" if newAmount > oldAmount
                else "decrease" if newAmount < oldAmount
                else "unchanged"
            )
            expected_difference = newAmount - oldAmount

            if communicationData.get("change_type") != expectedChange:
                errors.append("Incorrect change type detected.")

    # 3. Check knowledge agent verification
    if knowledgeData is None:
        errors.append("Knowledge data is missing.")
    elif (
        knowledgeData.get("record_found") is not True
        or knowledgeData.get("verification_status") != "verified"
    ):
        warnings.append("Sponsor record needs manual verification.")

    # 4. Check finance calculation
    if financeData is None or not _is_money(financeData.get("total_difference")):
        errors.append("Finance calculation is missing or invalid.")
    elif (
        expected_difference is not None
        and financeData["total_difference"] != expected_difference
    ):
        errors.append("Finance total does not match the sponsor amounts.")

    # 5. Check planning data
    # planning_agent.js returns "total_budget_change"; finance agent returns "total_difference".
    if planningData is None:
        errors.append("Event planning data is missing.")
    elif (
        financeData is not None
        and planningData.get("total_budget_change") != financeData.get("total_difference")
    ):
        errors.append("Planning and finance totals do not match.")

    overallStatus = "passed" if not errors and not warnings else "review_required"

    return {
        "overall_status": overallStatus,
        "errors": errors,
        "warnings": warnings,
        "message": (
            "All agent outputs verified successfully."
            if overallStatus == "passed"
            else "Some information requires correction or manual review."
        ),
    }


# ---------------------------------------------------------------- TESTS

def _good_data():
    return {
        "communicationData": {
            "sponsor_name": "ABC Technologies",
            "old_amount": 200000,
            "new_amount": 100000,
            "change_type": "decrease",
        },
        "knowledgeData": {"record_found": True, "verification_status": "verified"},
        "financeData": {"total_difference": -100000},
        # planning_agent.js returns "total_budget_change" (not "total_difference")
        "planningData": {"total_budget_change": -100000},
    }


def test_verifyEventData():
    # 1. Normal input -> passed
    result = verifyEventData(_good_data())
    assert result["overall_status"] == "passed", result
    assert result["errors"] == [] and result["warnings"] == [], result
    print("PASS 1 normal input -> passed")

    # 2. Bad input: None, string, empty dict -> no crash, review_required
    for bad in (None, "", "abc", 42, []):
        r = verifyEventData(bad)
        assert r["overall_status"] == "review_required", (bad, r)
    r = verifyEventData({})
    assert r["overall_status"] == "review_required"
    assert "Communication data is missing." in r["errors"], r
    print("PASS 2 None / string / number / list / empty dict -> review_required, no crash")

    # 3. Edge case: finance and planning agree with each other,
    #    but both are wrong compared with the sponsor amounts.
    d = _good_data()
    d["financeData"] = {"total_difference": -50000}
    d["planningData"] = {"total_budget_change": -50000}
    r = verifyEventData(d)
    assert r["overall_status"] == "review_required", r
    assert "Finance total does not match the sponsor amounts." in r["errors"], r
    print("PASS 3 finance+planning agree but are wrong -> caught")

    # 4. Money must be an integer: float, string and bool are rejected
    for bad_amount in (100000.5, "100000", True):
        d = _good_data()
        d["communicationData"]["new_amount"] = bad_amount
        r = verifyEventData(d)
        assert "Invalid or missing sponsor amounts." in r["errors"], (bad_amount, r)
    print("PASS 4 float / string / bool amounts -> rejected")

    # 5. Sponsor name: blank and non-string are rejected
    for bad_name in ("   ", "", 12345, None):
        d = _good_data()
        d["communicationData"]["sponsor_name"] = bad_name
        r = verifyEventData(d)
        assert "Sponsor name is missing." in r["errors"], (bad_name, r)
    print("PASS 5 blank / number / None sponsor name -> rejected")

    # 6. Wrong change_type
    d = _good_data()
    d["communicationData"]["change_type"] = "increase"
    r = verifyEventData(d)
    assert "Incorrect change type detected." in r["errors"], r
    print("PASS 6 wrong change_type -> error")

    # 7. Unchanged amount is valid (difference 0)
    d = _good_data()
    d["communicationData"].update(old_amount=5000, new_amount=5000, change_type="unchanged")
    d["financeData"] = {"total_difference": 0}
    d["planningData"] = {"total_budget_change": 0}
    assert verifyEventData(d)["overall_status"] == "passed"
    print("PASS 7 unchanged amount (difference 0) -> passed")

    # 8. Knowledge agent: record not found -> warning, not pass
    d = _good_data()
    d["knowledgeData"] = {"record_found": False, "verification_status": "verified"}
    r = verifyEventData(d)
    assert r["overall_status"] == "review_required", r
    assert r["warnings"] == ["Sponsor record needs manual verification."], r
    print("PASS 8 record_found False -> warning")

    # 9. Backend error shape passed in as agent output
    d = _good_data()
    d["knowledgeData"] = {"error": True, "message": "Not found", "status_code": 404}
    r = verifyEventData(d)
    assert r["overall_status"] == "review_required", r
    assert any("Not found" in e and "404" in e for e in r["errors"]), r
    print("PASS 9 backend 404 error dict -> reported as error with message")

    # 10. planning_agent returns "total_budget_change" (the real key).
    #     finance returns "total_difference".
    #     When they match, verification must PASS (not raise false error).
    d = _good_data()
    # _good_data already uses total_budget_change in planningData, so just confirm:
    assert d["planningData"].get("total_budget_change") == d["financeData"].get("total_difference"), \
        "test fixture broken"
    r = verifyEventData(d)
    assert r["overall_status"] == "passed", ("PASS 10 fixture mismatch", r)
    print("PASS 10 planning total_budget_change == finance total_difference -> passed, no false error")

    # 11. Planning and finance DIFFER -> must catch the mismatch
    d = _good_data()
    d["planningData"] = {"total_budget_change": -50000}   # planning says -50k
    d["financeData"] = {"total_difference": -100000}       # finance says -100k
    r = verifyEventData(d)
    assert r["overall_status"] == "review_required", r
    assert "Planning and finance totals do not match." in r["errors"], r
    print("PASS 11 planning/finance mismatch (different values) -> caught")

    print("All tests passed.")


if __name__ == "__main__":
    test_verifyEventData()
