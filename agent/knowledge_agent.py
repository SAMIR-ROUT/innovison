"""Knowledge Agent: checks an email update against the real sponsor record."""
import json
import os
import urllib.error
import urllib.request

# Backend address comes from the environment, not from the code.
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")


def _http_get(url):
    """Return (status_code, body_text). Does not raise on 404/500."""
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:  # urllib raises on 4xx/5xx; we convert it
        return e.code, e.read().decode("utf-8")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Cannot reach backend: {e.reason}")


def fetch_sponsors():
    """GET /sponsors. Raises RuntimeError on any backend error."""
    status, text = _http_get(f"{BACKEND_URL}/sponsors")
    try:
        body = json.loads(text)
    except ValueError:
        raise RuntimeError(f"Backend sent non-JSON (status {status})")
    if status != 200 or (isinstance(body, dict) and body.get("error")):
        message = body.get("message", "unknown error") if isinstance(body, dict) else "unknown error"
        raise RuntimeError(f"Backend error {status}: {message}")
    if not isinstance(body, list):
        raise RuntimeError("Backend /sponsors did not return a list")
    return body


def _is_int(value):
    # bool is a subclass of int in Python, so exclude it.
    return isinstance(value, int) and not isinstance(value, bool)


def compareSponsorRecord(update, sponsors=None):
    """Compare an email update with the stored record.

    `sponsors` is the list from GET /sponsors. If None, it is fetched.
    Raises ValueError on bad input. Raises RuntimeError on backend errors.
    """
    if not isinstance(update, dict):
        raise ValueError("update must be a dict")

    sponsorName = update.get("sponsor_name")
    if not isinstance(sponsorName, str) or not sponsorName.strip():
        raise ValueError("sponsor_name must be a non-empty string")
    for field in ("old_amount", "new_amount"):
        if not _is_int(update.get(field)):
            raise ValueError(f"{field} must be an integer")

    if sponsors is None:
        sponsors = fetch_sponsors()

    # Ignore case and extra spaces: "abc technologies " is the same sponsor.
    wanted = sponsorName.strip().casefold()
    matches = [
        s for s in sponsors
        if isinstance(s.get("name"), str) and s["name"].strip().casefold() == wanted
    ]

    if not matches:
        return {
            "sponsor_name": sponsorName,
            "record_found": False,
            "verification_status": "not_found",
            "manual_review_required": True,
            "message": "Sponsor record not found in database.",
        }

    if len(matches) > 1:
        return {
            "sponsor_name": sponsorName,
            "record_found": True,
            "verification_status": "ambiguous",
            "manual_review_required": True,
            "message": "More than one sponsor has this name. Manual review required.",
        }

    existingRecord = matches[0]
    # Backend may return a string like "200000.00" — always convert to int first.
    storedAmount = int(round(float(existingRecord["current_commitment"])))
    oldAmountMatches = storedAmount == update["old_amount"]

    return {
        "sponsor_name": sponsorName,
        "sponsor_id": existingRecord["id"],  # run_update.py needs this for PATCH
        "record_found": True,
        "stored_amount": storedAmount,
        "email_old_amount": update["old_amount"],
        "new_amount": update["new_amount"],
        "old_amount_matches": oldAmountMatches,
        "verification_status": "verified" if oldAmountMatches else "mismatch",
        "manual_review_required": not oldAmountMatches,
        "message": (
            "Sponsor information matches the existing record."
            if oldAmountMatches
            else "Contribution mismatch detected. Manual review required."
        ),
    }


def test_compareSponsorRecord():
    fake = [
        {"id": 1, "name": "ABC Technologies", "original_commitment": 200000, "current_commitment": 200000},
        {"id": 2, "name": "XYZ Solutions", "original_commitment": 75000, "current_commitment": 60000},
    ]
    # fake_str: backend sends amounts as strings (common with PostgreSQL numeric type)
    fake_str = [
        {"id": 1, "name": "ABC Technologies", "original_commitment": "200000.00", "current_commitment": "200000.00"},
        {"id": 2, "name": "XYZ Solutions", "original_commitment": "75000.00", "current_commitment": "60000.00"},
    ]

    # 1. Normal input (int amounts from backend)
    r = compareSponsorRecord({"sponsor_name": "ABC Technologies", "old_amount": 200000, "new_amount": 100000}, fake)
    assert r["verification_status"] == "verified" and r["sponsor_id"] == 1, r
    print("1 normal: OK ->", r["verification_status"], "id", r["sponsor_id"])

    # 1b. Backend returns string amounts like '200000.00' (the real bug that was fixed)
    r = compareSponsorRecord({"sponsor_name": "ABC Technologies", "old_amount": 200000, "new_amount": 100000}, fake_str)
    assert r["verification_status"] == "verified", f"string amount bug: got {r['verification_status']}"
    assert isinstance(r["stored_amount"], int), f"stored_amount must be int, got {type(r['stored_amount'])}"
    print("1b string amounts from backend: OK -> verified, stored_amount is int", r["stored_amount"])

    # 2. Bad input: None, empty name, string amount, float amount, missing field
    bad_inputs = [
        None,
        {"sponsor_name": "", "old_amount": 1, "new_amount": 2},
        {"sponsor_name": "ABC Technologies", "old_amount": "200000", "new_amount": 1},
        {"sponsor_name": "ABC Technologies", "old_amount": 200000.0, "new_amount": 1},
        {"sponsor_name": "ABC Technologies", "old_amount": 200000},
    ]
    for bad in bad_inputs:
        try:
            compareSponsorRecord(bad, fake)
        except ValueError as e:
            print("2 bad input: OK -> ValueError:", e)
        else:
            raise AssertionError(f"no error for {bad!r}")

    # 3. Edge case: email old amount matches the ORIGINAL, but the record
    #    was already changed. Must be a mismatch. Name has odd case/spaces.
    r = compareSponsorRecord({"sponsor_name": "  xyz solutions ", "old_amount": 75000, "new_amount": 50000}, fake)
    assert r["verification_status"] == "mismatch" and r["stored_amount"] == 60000, r
    print("3 edge: OK -> mismatch, stored", r["stored_amount"])

    # 4. Unknown sponsor
    r = compareSponsorRecord({"sponsor_name": "Nobody Ltd", "old_amount": 1, "new_amount": 2}, fake)
    assert r["verification_status"] == "not_found" and r["manual_review_required"], r
    print("4 not found: OK")

    # 5. Backend error shape (404) must raise, not pass silently
    global _http_get
    real_get = _http_get
    _http_get = lambda url: (404, json.dumps({"error": True, "message": "nope", "status_code": 404}))
    try:
        fetch_sponsors()
    except RuntimeError as e:
        print("5 backend error: OK ->", e)
    else:
        raise AssertionError("404 did not raise")
    finally:
        _http_get = real_get

    print("ALL TESTS PASSED")


if __name__ == "__main__":
    test_compareSponsorRecord()
