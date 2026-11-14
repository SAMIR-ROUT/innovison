"""
sponsor_parser.py

A RULE-BASED parser for sponsor emails. It has NO AI model inside.
Job 1: pull sponsor name, old amount, new amount and date out of email text.
Job 2: check those facts against what the database says.
If anything is unclear, it asks for manual review instead of guessing.
"""
import re
from datetime import datetime

# ---------------------------------------------------------------
# Amounts: Rs 1,00,000 | Rs. 1,00,000 | INR 50000 | ₹1.2 lakh | Rs 50k
# \b means "word boundary". It stops "Rs" matching inside words like "partners".
# ---------------------------------------------------------------
AMOUNT_RE = re.compile(
    r"(?:₹|\bRs\b\.?|\bINR\b)\s*(\d[\d,]*(?:\.\d+)?)\s*(lakhs?|lacs?|crores?|cr|l|k)?\b",
    re.IGNORECASE,
)

# Words that tell us a sentence is about the OLD / NEW amount
OLD_RE = re.compile(
    r"\b(previous\w*|earlier|original\w*|initial\w*|committed|pledged|promised)\b",
    re.IGNORECASE,
)
NEW_RE = re.compile(
    r"\b(revis\w*|new|reduc\w*|decreas\w*|increas\w*|updat\w*|now|lower\w*|rais\w*|instead|chang\w*)\b",
    re.IGNORECASE,
)

NAME_RE = re.compile(
    r"^\s*(?:sponsor|company|organi[sz]ation)\s*[:\-]\s*(.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

DATE_RE = re.compile(
    r"effective(?:\s+(?:from|on|date))?\s*[:\-]?\s*"
    r"(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+),?\s+(\d{4})",
    re.IGNORECASE,
)


def _to_number(number_text, unit):
    """'1,00,000' -> 100000 | '1.2' + 'lakh' -> 120000 | '50' + 'k' -> 50000"""
    value = float(number_text.replace(",", ""))
    unit = (unit or "").lower()
    if unit.startswith(("lakh", "lac")) or unit == "l":
        value *= 100_000
    elif unit == "k":
        value *= 1_000
    elif unit.startswith("cr"):
        value *= 10_000_000
    return int(round(value))


def _normalize(name):
    return " ".join(str(name).lower().split())


def _parse_date(day, month, year):
    """Return 'YYYY-MM-DD' or None if the date cannot be read."""
    for fmt in ("%d %B %Y", "%d %b %Y"):
        try:
            return datetime.strptime(f"{day} {month} {year}", fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _split_sentences(text):
    text = re.sub(r"\bRs\.", "Rs", text, flags=re.IGNORECASE)  # so "Rs." does not end a sentence
    parts = re.split(r"\n\s*\n", text)                           # blank line = new block
    sentences = []
    for part in parts:
        part = " ".join(part.split())                            # join wrapped lines
        sentences.extend(re.split(r"(?<=[.!?])\s+", part))
    return [s for s in sentences if s]


def extract_sponsor_update(email_text, known_names=None):
    issues = []     # problems that REQUIRE a human to look
    warnings = []   # small notes, no review needed

    # ---- sponsor name ----
    sponsor_name = None
    match = NAME_RE.search(email_text)
    if match:
        sponsor_name = match.group(1).strip()
    elif known_names:
        # no "Sponsor:" line: look for a name we already know from the database
        lowered = email_text.lower()
        hits = [n for n in known_names if n and n.strip().lower() in lowered]
        if len(hits) == 1:
            sponsor_name = hits[0]
        elif len(hits) > 1:
            issues.append("More than one known sponsor name appears in the email")
    if not sponsor_name and not any("known sponsor" in i for i in issues):
        issues.append("Sponsor name not found")

    # ---- amounts: decide old / new by the WORDS in the sentence, not by order ----
    old_values, new_values, unknown_values = [], [], []
    for sentence in _split_sentences(email_text):
        found = list(AMOUNT_RE.finditer(sentence))
        if not found:
            continue
        values = [_to_number(m.group(1), m.group(2)) for m in found]

        # special case: "from X to Y"
        if len(found) == 2:
            before = sentence[: found[0].start()]
            between = sentence[found[0].end(): found[1].start()]
            if re.search(r"\bfrom\b", before, re.I) and re.search(r"\bto\b|→|->", between, re.I):
                old_values.append(values[0])
                new_values.append(values[1])
                continue

        has_old = bool(OLD_RE.search(sentence))
        has_new = bool(NEW_RE.search(sentence))
        for value in values:
            if has_old and not has_new:
                old_values.append(value)
            elif has_new and not has_old:
                new_values.append(value)
            else:
                unknown_values.append(value)

    if unknown_values:
        issues.append(f"Could not tell if these amounts are old or new: {sorted(set(unknown_values))}")
    if not new_values:
        issues.append("New amount not found")
    elif len(set(new_values)) > 1:
        issues.append(f"More than one possible new amount: {sorted(set(new_values))}")
    if len(set(old_values)) > 1:
        issues.append(f"More than one possible old amount: {sorted(set(old_values))}")

    new_amount = new_values[0] if len(set(new_values)) == 1 else None
    old_amount = old_values[0] if len(set(old_values)) == 1 else None

    # ---- change type (from the email only; the database check can override it) ----
    if old_amount is None or new_amount is None:
        change_type = "unknown"
    elif new_amount > old_amount:
        change_type = "increase"
    elif new_amount < old_amount:
        change_type = "decrease"
    else:
        change_type = "unchanged"

    # ---- effective date (missing date is only a warning) ----
    effective_date = None
    date_match = DATE_RE.search(email_text)
    if date_match:
        effective_date = _parse_date(*date_match.groups())
        if effective_date is None:
            warnings.append("Effective date found but could not be read")
    else:
        warnings.append("No effective date found")

    return {
        "sponsor_name": sponsor_name,
        "old_amount": old_amount,
        "new_amount": new_amount,
        "change_type": change_type,
        "effective_date": effective_date,
        "manual_review_required": len(issues) > 0,
        "issues": issues,
        "warnings": warnings,
    }


def check_against_database(result, sponsors):
    """
    result   : output of extract_sponsor_update
    sponsors : the list returned by GET /sponsors
    The DATABASE is the truth for the old amount, not the email.
    """
    result = dict(result)
    issues = list(result["issues"])
    result["sponsor_id"] = None
    result["current_in_database"] = None

    if result["sponsor_name"]:
        key = _normalize(result["sponsor_name"])
        matches = [s for s in sponsors if _normalize(s["name"]) == key]
        if len(matches) == 0:
            issues.append(f"Sponsor '{result['sponsor_name']}' not found in database")
        elif len(matches) > 1:
            issues.append(f"More than one sponsor named '{result['sponsor_name']}' in database")
        else:
            sponsor = matches[0]
            # The API may send 120000, "120000" or "120000.00": handle all of them
            current = int(round(float(sponsor["current_commitment"])))
            result["sponsor_id"] = sponsor["id"]
            result["current_in_database"] = current

            if result["old_amount"] is not None and result["old_amount"] != current:
                issues.append(
                    f"Email says old amount is {result['old_amount']} "
                    f"but database says {current}"
                )
            if result["new_amount"] is not None:
                if result["new_amount"] > current:
                    result["change_type"] = "increase"
                elif result["new_amount"] < current:
                    result["change_type"] = "decrease"
                else:
                    result["change_type"] = "unchanged"
                    issues.append("New amount is the same as the database amount")

    result["issues"] = issues
    result["manual_review_required"] = len(issues) > 0
    return result
