"""
Automated test suite for OmniPulse Backend Auth & Username-based Login.
Covers:
1. Username-to-email resolution for 'vaishnavi' and associated variants
2. Verification of confirmed Supabase Auth account and mapping
3. Login request handling, validation, and error propagation
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.v1.routes.auth import resolve_identifier_to_email

client = TestClient(app)


def test_username_resolution_vaishnavi():
    """Verify that 'vaishnavi' and aliases resolve to the active confirmed email."""
    # 1. Exact username
    resolved_1 = resolve_identifier_to_email("vaishnavi")
    assert resolved_1 == "vaishnavikolekar2023@gmail.com"

    # 2. Case-insensitive
    resolved_2 = resolve_identifier_to_email("Vaishnavi")
    assert resolved_2 == "vaishnavikolekar2023@gmail.com"

    # 3. Direct email preservation
    resolved_3 = resolve_identifier_to_email("vaishnavikolekar2023@gmail.com")
    assert resolved_3 == "vaishnavikolekar2023@gmail.com"

    # 4. Secondary profile alias
    resolved_4 = resolve_identifier_to_email("vaishnavi_pk")
    assert resolved_4 == "kolekarvaishnavi77@gmail.com"

    # 5. Full name variant for secondary profile
    resolved_5 = resolve_identifier_to_email("vaishnavi pandurang kolekar")
    assert resolved_5 == "kolekarvaishnavi77@gmail.com"

    # 6. Secondary profile direct email
    resolved_6 = resolve_identifier_to_email("kolekarvaishnavi77@gmail.com")
    assert resolved_6 == "kolekarvaishnavi77@gmail.com"


def test_resolve_username_api_endpoint():
    """Verify GET /api/v1/auth/resolve-username endpoint."""
    res = client.get("/api/v1/auth/resolve-username?username=vaishnavi")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["resolved_email"] == "vaishnavikolekar2023@gmail.com"
    assert data["username"] == "vaishnavi"


def test_login_missing_fields_validation():
    """Verify POST /api/v1/auth/login validates required identifier and password."""
    # Empty identifier
    res1 = client.post("/api/v1/auth/login", json={"identifier": "", "password": "anypassword"})
    assert res1.status_code == 400

    # Empty password
    res2 = client.post("/api/v1/auth/login", json={"identifier": "vaishnavi", "password": ""})
    assert res2.status_code == 400


def test_login_invalid_password_returns_401():
    """Verify that incorrect password returns 401 with standard error message."""
    res = client.post("/api/v1/auth/login", json={
        "identifier": "vaishnavi",
        "password": "this_is_an_intentionally_incorrect_password_123"
    })
    assert res.status_code == 401
    data = res.json()
    assert "Invalid login credentials" in data["detail"]

