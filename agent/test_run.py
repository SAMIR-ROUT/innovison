import json, httpx
from run_update import run

state = {"amount": "200000.00", "history": []}

def handler(request):
    p, m = request.url.path, request.method
    if p == "/sponsors" and m == "GET":
        return httpx.Response(200, json=[{"id": 1, "name": "ABC Technologies", "current_commitment": state["amount"]}])
    if p == "/sponsors/1" and m == "PATCH":
        if request.headers.get("X-API-Key") != "k":
            return httpx.Response(403, json={"error": True, "message": "Invalid or missing API key", "status_code": 403})
        body = json.loads(request.content)
        state["history"].append({"old": state["amount"], "new": body["current_commitment"], "note": body["note"]})
        state["amount"] = f'{body["current_commitment"]}.00'
        return httpx.Response(200, json={"id": 1})
    if p == "/sponsors/1" and m == "GET":
        return httpx.Response(200, json={"id": 1, "current_commitment": state["amount"]})
    if p == "/sponsors/1/history":
        return httpx.Response(200, json=state["history"])
    return httpx.Response(404, json={"error": True, "message": "nope", "status_code": 404})

client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://test")
email = "Sponsor: ABC Technologies\nWe previously committed Rs. 2,00,000.\nOur revised contribution is Rs. 1,20,000.\nThe change is effective 20 December 2026."

print("=== A: human says no");  assert run(client, email, "k", approve=lambda _: "no") is False and state["history"] == []
print("=== B: human says yes"); assert run(client, email, "k", approve=lambda _: "yes") is True and len(state["history"]) == 1
print("=== C: same email again -> db now 120000, email old=200000 -> must stop")
assert run(client, email, "k", approve=lambda _: "yes") is False and len(state["history"]) == 1
print("=== D: wrong key -> 403")
state["amount"] = "200000.00"
try:
    run(client, email, "WRONG", approve=lambda _: "yes"); raise SystemExit("should have failed")
except httpx.HTTPStatusError as e: print("got", e.response.status_code)
print("\nALL FLOW TESTS PASSED")
