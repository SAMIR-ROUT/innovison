import pytest
from fastapi.testclient import TestClient


# ==========================================
# HEALTH TESTS
# ==========================================

def test_health(client: TestClient):
    """GET /health returns 200 with status ok."""
    response = client.get("/health")
    assert response.status_code == 200, response.json()
    assert response.json() == {"status": "ok"}, response.json()


def test_health_db(client: TestClient):
    """GET /health/db returns 200 with db connected."""
    response = client.get("/health/db")
    assert response.status_code == 200, response.json()
    data = response.json()
    assert data.get("status") == "ok", data
    assert data.get("db") == "connected", data


# ==========================================
# SPONSOR CREATE TESTS
# ==========================================

def test_create_sponsor_valid(client: TestClient, api_key: str):
    """POST /sponsors with valid data and correct API key returns 201 and correct fields."""
    payload = {
        "name": "TEST_SPONSOR_DO_NOT_KEEP_VALID",
        "original_commitment": 250000,
        "current_commitment": 250000,
    }
    response = client.post(
        "/sponsors",
        json=payload,
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 201, response.json()
    data = response.json()
    assert data["name"] == payload["name"], data
    assert float(data["original_commitment"]) == 250000.0, data
    assert float(data["current_commitment"]) == 250000.0, data
    assert "id" in data, data
    assert "created_at" in data, data


def test_create_sponsor_no_key(client: TestClient):
    """POST /sponsors without API key returns 403."""
    payload = {
        "name": "TEST_SPONSOR_DO_NOT_KEEP_NO_KEY",
        "original_commitment": 100000,
        "current_commitment": 100000,
    }
    response = client.post("/sponsors", json=payload)
    assert response.status_code == 403, response.json()
    data = response.json()
    assert data.get("error") is True, data
    assert data.get("status_code") == 403, data


def test_create_sponsor_wrong_key(client: TestClient):
    """POST /sponsors with wrong key returns 403."""
    payload = {
        "name": "TEST_SPONSOR_DO_NOT_KEEP_WRONG_KEY",
        "original_commitment": 100000,
        "current_commitment": 100000,
    }
    response = client.post(
        "/sponsors",
        json=payload,
        headers={"X-API-Key": "completely_wrong_key_xyz"},
    )
    assert response.status_code == 403, response.json()
    data = response.json()
    assert data.get("error") is True, data
    assert data.get("status_code") == 403, data


def test_create_sponsor_empty_name(client: TestClient, api_key: str):
    """POST /sponsors with empty name returns 422."""
    payload = {
        "name": "   ",
        "original_commitment": 100000,
        "current_commitment": 100000,
    }
    response = client.post(
        "/sponsors",
        json=payload,
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 422, response.json()
    data = response.json()
    assert data.get("error") is True, data
    assert data.get("status_code") == 422, data
    assert "details" in data, data


def test_create_sponsor_negative_commitment(client: TestClient, api_key: str):
    """POST /sponsors with negative original_commitment returns 422."""
    payload = {
        "name": "TEST_SPONSOR_DO_NOT_KEEP_NEG",
        "original_commitment": -50000,
        "current_commitment": 50000,
    }
    response = client.post(
        "/sponsors",
        json=payload,
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 422, response.json()
    data = response.json()
    assert data.get("error") is True, data
    assert data.get("status_code") == 422, data
    assert "details" in data, data


# ==========================================
# SPONSOR READ TESTS
# ==========================================

def test_get_all_sponsors(client: TestClient):
    """GET /sponsors returns 200 and a list."""
    response = client.get("/sponsors")
    assert response.status_code == 200, response.json()
    data = response.json()
    assert isinstance(data, list), data


def test_get_sponsor_valid(client: TestClient, api_key: str):
    """GET /sponsors/{id} with a valid id returns 200 and correct sponsor data."""
    # Create an independent test sponsor
    create_res = client.post(
        "/sponsors",
        json={
            "name": "TEST_SPONSOR_DO_NOT_KEEP_READ",
            "original_commitment": 120000,
            "current_commitment": 120000,
        },
        headers={"X-API-Key": api_key},
    )
    assert create_res.status_code == 201, create_res.json()
    sponsor_id = create_res.json()["id"]

    # Read sponsor
    response = client.get(f"/sponsors/{sponsor_id}")
    assert response.status_code == 200, response.json()
    data = response.json()
    assert data["id"] == sponsor_id, data
    assert data["name"] == "TEST_SPONSOR_DO_NOT_KEEP_READ", data


def test_get_sponsor_invalid(client: TestClient):
    """GET /sponsors/99999 returns 404 with error shape {"error": true, ...}."""
    response = client.get("/sponsors/99999")
    assert response.status_code == 404, response.json()
    data = response.json()
    assert data.get("error") is True, data
    assert data.get("status_code") == 404, data
    assert data.get("message") == "Sponsor not found", data


# ==========================================
# SPONSOR UPDATE TESTS
# ==========================================

def test_patch_sponsor_valid(client: TestClient, api_key: str):
    """PATCH /sponsors/{id} with valid current_commitment and correct API key returns 200."""
    create_res = client.post(
        "/sponsors",
        json={
            "name": "TEST_SPONSOR_DO_NOT_KEEP_PATCH",
            "original_commitment": 200000,
            "current_commitment": 200000,
        },
        headers={"X-API-Key": api_key},
    )
    sponsor_id = create_res.json()["id"]

    # Update commitment with note
    patch_res = client.patch(
        f"/sponsors/{sponsor_id}",
        json={
            "current_commitment": 175000,
            "note": "Negotiated reduced package",
        },
        headers={"X-API-Key": api_key},
    )
    assert patch_res.status_code == 200, patch_res.json()
    data = patch_res.json()
    assert data["id"] == sponsor_id, data
    assert float(data["current_commitment"]) == 175000.0, data


def test_patch_sponsor_no_key(client: TestClient, api_key: str):
    """PATCH /sponsors/{id} without key returns 403."""
    create_res = client.post(
        "/sponsors",
        json={
            "name": "TEST_SPONSOR_DO_NOT_KEEP_NO_KEY_PATCH",
            "original_commitment": 100000,
            "current_commitment": 100000,
        },
        headers={"X-API-Key": api_key},
    )
    sponsor_id = create_res.json()["id"]

    patch_res = client.patch(
        f"/sponsors/{sponsor_id}",
        json={"current_commitment": 90000},
    )
    assert patch_res.status_code == 403, patch_res.json()
    data = patch_res.json()
    assert data.get("error") is True, data
    assert data.get("status_code") == 403, data


def test_patch_sponsor_invalid_id(client: TestClient, api_key: str):
    """PATCH /sponsors/99999 with correct key returns 404."""
    patch_res = client.patch(
        "/sponsors/99999",
        json={"current_commitment": 50000},
        headers={"X-API-Key": api_key},
    )
    assert patch_res.status_code == 404, patch_res.json()
    data = patch_res.json()
    assert data.get("error") is True, data
    assert data.get("status_code") == 404, data


def test_patch_sponsor_zero_commitment(client: TestClient, api_key: str):
    """PATCH /sponsors/{id} with current_commitment = 0 returns 422."""
    create_res = client.post(
        "/sponsors",
        json={
            "name": "TEST_SPONSOR_DO_NOT_KEEP_ZERO",
            "original_commitment": 100000,
            "current_commitment": 100000,
        },
        headers={"X-API-Key": api_key},
    )
    sponsor_id = create_res.json()["id"]

    patch_res = client.patch(
        f"/sponsors/{sponsor_id}",
        json={"current_commitment": 0},
        headers={"X-API-Key": api_key},
    )
    assert patch_res.status_code == 422, patch_res.json()
    data = patch_res.json()
    assert data.get("error") is True, data
    assert data.get("status_code") == 422, data


# ==========================================
# HISTORY TESTS
# ==========================================

def test_get_history_valid(client: TestClient, api_key: str):
    """GET /sponsors/{id}/history after a PATCH returns 200 and at least one history row."""
    # Create sponsor
    create_res = client.post(
        "/sponsors",
        json={
            "name": "TEST_SPONSOR_DO_NOT_KEEP_HIST",
            "original_commitment": 200000,
            "current_commitment": 200000,
        },
        headers={"X-API-Key": api_key},
    )
    sponsor_id = create_res.json()["id"]

    # Apply PATCH
    patch_res = client.patch(
        f"/sponsors/{sponsor_id}",
        json={
            "current_commitment": 150000,
            "note": "Budget cut adjustment",
        },
        headers={"X-API-Key": api_key},
    )
    assert patch_res.status_code == 200, patch_res.json()

    # Query history
    history_res = client.get(f"/sponsors/{sponsor_id}/history")
    assert history_res.status_code == 200, history_res.json()
    history = history_res.json()
    assert isinstance(history, list), history
    assert len(history) >= 1, history
    row = history[0]
    assert row["sponsor_id"] == sponsor_id, row
    assert float(row["old_commitment"]) == 200000.0, row
    assert float(row["new_commitment"]) == 150000.0, row
    assert row["note"] == "Budget cut adjustment", row


def test_get_history_no_history(client: TestClient, api_key: str):
    """GET /sponsors/{id}/history for a sponsor with no changes returns 200 and empty list []."""
    create_res = client.post(
        "/sponsors",
        json={
            "name": "TEST_SPONSOR_DO_NOT_KEEP_NO_HIST",
            "original_commitment": 80000,
            "current_commitment": 80000,
        },
        headers={"X-API-Key": api_key},
    )
    sponsor_id = create_res.json()["id"]

    history_res = client.get(f"/sponsors/{sponsor_id}/history")
    assert history_res.status_code == 200, history_res.json()
    assert history_res.json() == [], history_res.json()


def test_get_history_invalid_id(client: TestClient):
    """GET /sponsors/99999/history returns 404."""
    response = client.get("/sponsors/99999/history")
    assert response.status_code == 404, response.json()
    data = response.json()
    assert data.get("error") is True, data
    assert data.get("status_code") == 404, data
