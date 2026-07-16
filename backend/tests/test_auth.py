from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.api.deps import require_business_admin
from app.models import User, UserRole


def test_register_login_refresh_and_me(client):
    registered = client.post(
        "/api/auth/register",
        json={
            "business_name": "Auth Dental",
            "name": "Owner",
            "email": "owner@auth-test.example",
            "password": "securepass1",
        },
    )
    assert registered.status_code == 201
    body = registered.json()
    assert body["token_type"] == "bearer"
    assert body["business_id"]
    assert body["access_token"]
    assert body["refresh_token"]

    me = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == "owner@auth-test.example"
    assert me.json()["role"] == "owner"

    login = client.post(
        "/api/auth/login",
        json={"email": "owner@auth-test.example", "password": "securepass1"},
    )
    assert login.status_code == 200
    refresh = client.post(
        "/api/auth/refresh",
        json={"refresh_token": login.json()["refresh_token"]},
    )
    assert refresh.status_code == 200
    assert refresh.json()["access_token"]

    reused = client.post(
        "/api/auth/refresh",
        json={"refresh_token": login.json()["refresh_token"]},
    )
    assert reused.status_code == 401


def test_login_rejects_bad_password(client):
    client.post(
        "/api/auth/register",
        json={
            "business_name": "Auth Dental 2",
            "name": "Owner",
            "email": "owner2@auth-test.example",
            "password": "securepass1",
        },
    )
    bad = client.post(
        "/api/auth/login",
        json={"email": "owner2@auth-test.example", "password": "wrong-password"},
    )
    assert bad.status_code == 401


def test_jwt_protects_integrations_and_legacy_owner_token(client):
    registered = client.post(
        "/api/auth/register",
        json={
            "business_name": "JWT Dental",
            "name": "Owner",
            "email": "jwt-owner@auth-test.example",
            "password": "securepass1",
        },
    )
    assert registered.status_code == 201
    owner_token = registered.json()["access_token"]
    business_id = registered.json()["business_id"]

    ok = client.get(
        "/api/integrations/retell/status",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert ok.status_code == 200

    missing = client.get("/api/integrations/retell/status")
    assert missing.status_code == 401

    legacy = client.get(
        "/api/integrations/retell/status",
        headers={
            "X-Owner-Token": "test-owner-token",
            "X-Business-Id": business_id,
        },
    )
    assert legacy.status_code == 200


def test_require_business_admin_rejects_member_role():
    member = User(
        id="u1",
        business_id="b1",
        name="Member",
        email="m@example.com",
        role=UserRole.member,
    )
    db = MagicMock()
    with patch("app.api.deps.get_current_user", return_value=member):
        try:
            require_business_admin(
                authorization="Bearer unused",
                x_owner_token=None,
                x_business_id=None,
                db=db,
            )
            raised = False
        except HTTPException as exc:
            raised = True
            assert exc.status_code == 403
    assert raised
