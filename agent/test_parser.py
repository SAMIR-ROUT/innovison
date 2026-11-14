from sponsor_parser import extract_sponsor_update, check_against_database

def show(title, r): print(f"\n--- {title}\n{r}")

# 1 original email
e1 = """
Sponsor: ABC Technologies

We previously committed Rs. 2,00,000.
Our revised contribution is Rs. 1,00,000.
The change is effective 20 December 2026.
"""
r = extract_sponsor_update(e1); show("1 original", r)
assert (r["sponsor_name"], r["old_amount"], r["new_amount"], r["change_type"], r["effective_date"]) == ("ABC Technologies", 200000, 100000, "decrease", "2026-12-20")
assert not r["manual_review_required"]

# 2 reversed order (old bug 1)
e2 = "Sponsor: ABC Technologies\nOur revised contribution is Rs. 1,00,000. Earlier we committed Rs. 2,00,000."
r = extract_sponsor_update(e2); show("2 reversed", r)
assert (r["old_amount"], r["new_amount"], r["change_type"]) == (200000, 100000, "decrease")

# 3 three amounts (old bug 4)
e3 = e1 + "\nWe have already paid Rs. 50,000."
r = extract_sponsor_update(e3); show("3 three amounts", r)
assert r["manual_review_required"]

# 4 'Rs' inside a word (old bug 2)
e4 = "Sponsor: XYZ\nDear partners 2026 event: we will pay Rs. 80,000."
r = extract_sponsor_update(e4); show("4 rs inside word", r)
assert "2026" not in str(r["issues"])
assert r["manual_review_required"]

# 5 no Sponsor line, name known from database
e5 = "Hi team, ABC Technologies will reduce its contribution to Rs 1,20,000."
r = extract_sponsor_update(e5, known_names=["ABC Technologies", "Other Co"]); show("5 name from db", r)
assert r["sponsor_name"] == "ABC Technologies" and r["new_amount"] == 120000 and not r["manual_review_required"]

# 6 date formats (old bug 6)
for txt in ["effective from 20th December 2026", "effective 5 Dec 2026", "effective on 1 January, 2027"]:
    r = extract_sponsor_update("Sponsor: A\nOur revised contribution is Rs 10,000. The change is " + txt + ".")
    print(txt, "->", r["effective_date"])
    assert r["effective_date"] is not None

# 7 lakh / k (old bug 7)
r = extract_sponsor_update("Sponsor: A\nOur revised contribution is Rs 1.2 lakh."); assert r["new_amount"] == 120000
r = extract_sponsor_update("Sponsor: A\nOur revised contribution is ₹50k."); assert r["new_amount"] == 50000
r = extract_sponsor_update("Sponsor: A\nOur revised contribution is Rs 1.2L."); assert r["new_amount"] == 120000

# 8 from X to Y
r = extract_sponsor_update("Sponsor: A\nWe are reducing our contribution from Rs. 2,00,000 to Rs. 1,20,000."); show("8 from-to", r)
assert (r["old_amount"], r["new_amount"]) == (200000, 120000)

# 9 crash case (old bug 3): 'Rs ,' must not crash
extract_sponsor_update("Sponsor: A\nRs , and INR , and Rs. 5,")

# 10 no amounts at all
r = extract_sponsor_update("Sponsor: A\nHello there."); assert r["manual_review_required"]

# 11 database checks
dbs = [{"id": 1, "name": "ABC Technologies", "current_commitment": "200000.00"}]
r = check_against_database(extract_sponsor_update(e1), dbs); show("11a db ok", r)
assert r["sponsor_id"] == 1 and not r["manual_review_required"] and r["current_in_database"] == 200000
dbs2 = [{"id": 1, "name": "ABC Technologies", "current_commitment": 150000}]
r = check_against_database(extract_sponsor_update(e1), dbs2); show("11b mismatch", r)
assert r["manual_review_required"]
r = check_against_database(extract_sponsor_update(e1), [{"id": 2, "name": "Other", "current_commitment": 1}]); assert r["manual_review_required"]
print("\nALL PARSER TESTS PASSED")
