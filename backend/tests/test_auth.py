from tests.conftest import create_business, tenant_headers


def test_register_login_refresh_cookie_session(client):
    registered = client.post(
        "/api/auth/register",
        json={
            "business_name": "Auth Dental",
            "name": "Owner",
            "email": "owner@auth-test.example",
            "password": "securepass1",
            "remember_me": True,
        },
    )
    assert registered.status_code == 201
    body = registered.json()
    assert body["business_id"]
    assert body["user_id"]
    assert "access_token" not in body
    assert client.cookies.get("sf_access")
    assert client.cookies.get("sf_refresh")

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "owner@auth-test.example"
    assert me.json()["role"] == "owner"
    assert me.json()["email_verified"] is False

    client.cookies.clear()
    login = client.post(
        "/api/auth/login",
        json={"email": "owner@auth-test.example", "password": "securepass1"},
    )
    assert login.status_code == 200
    assert client.cookies.get("sf_access")

    refresh = client.post("/api/auth/refresh")
    assert refresh.status_code == 200
    assert client.cookies.get("sf_access")

    logout = client.post("/api/auth/logout")
    assert logout.status_code == 200
    me_after = client.get("/api/auth/me")
    assert me_after.status_code == 401


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
    client.cookies.clear()
    bad = client.post(
        "/api/auth/login",
        json={"email": "owner2@auth-test.example", "password": "wrong-password"},
    )
    assert bad.status_code == 401


def test_forgot_reset_and_invite_flow(client):
    registered = client.post(
        "/api/auth/register",
        json={
            "business_name": "Invite Dental",
            "name": "Owner",
            "email": "invite-owner@auth-test.example",
            "password": "securepass1",
        },
    )
    assert registered.status_code == 201

    forgot = client.post(
        "/api/auth/forgot-password",
        json={"email": "invite-owner@auth-test.example"},
    )
    assert forgot.status_code == 200
    reset_token = forgot.json()["reset_token"]
    assert reset_token

    reset = client.post(
        "/api/auth/reset-password",
        json={"token": reset_token, "password": "newsecure1"},
    )
    assert reset.status_code == 200

    client.cookies.clear()
    login = client.post(
        "/api/auth/login",
        json={"email": "invite-owner@auth-test.example", "password": "newsecure1"},
    )
    assert login.status_code == 200

    invite = client.post(
        "/api/auth/invitations",
        json={"email": "member@auth-test.example", "role": "member"},
    )
    assert invite.status_code == 201
    token = invite.json()["invite_token"]
    assert token

    client.cookies.clear()
    accepted = client.post(
        "/api/auth/invitations/accept",
        json={"token": token, "name": "Member", "password": "memberpass1"},
    )
    assert accepted.status_code == 201
    assert accepted.json()["role"] == "member"

    verify = client.post("/api/auth/verify-email", json={"token": "placeholder-token"})
    assert verify.status_code == 200
    me = client.get("/api/auth/me")
    assert me.json()["email_verified"] is True


def test_jwt_cookie_protects_integrations_and_legacy_owner_token(client):
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
    business_id = registered.json()["business_id"]

    ok = client.get("/api/integrations/retell/status")
    assert ok.status_code == 200

    client.cookies.clear()
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


def test_jwt_protects_tenant_reads(client):
    registered = client.post(
        "/api/auth/register",
        json={
            "business_name": "Tenant Dental",
            "name": "Owner",
            "email": "tenant-owner@auth-test.example",
            "password": "securepass1",
        },
    )
    assert registered.status_code == 201
    business_id = registered.json()["business_id"]

    ok = client.get(f"/api/businesses/{business_id}/calls")
    assert ok.status_code == 200

    other = client.post(
        "/api/auth/register",
        json={
            "business_name": "Other Dental",
            "name": "Other",
            "email": "other-owner@auth-test.example",
            "password": "securepass1",
        },
    ).json()
    # Still authenticated as other owner after second register (cookies overwritten).
    denied = client.get(f"/api/businesses/{business_id}/calls")
    assert denied.status_code == 403
    assert other["business_id"] != business_id


def test_require_business_admin_rejects_member_role():
    from unittest.mock import MagicMock, patch

    from fastapi import HTTPException

    from app.api.deps import require_business_admin
    from app.models import User, UserRole

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
                sf_access=None,
                x_owner_token=None,
                x_business_id=None,
                db=db,
            )
            raised = False
        except HTTPException as exc:
            raised = True
            assert exc.status_code == 403
    assert raised


def test_create_business_still_requires_owner_token(client):
    denied = client.post("/api/businesses", json={"name": "No Auth"})
    assert denied.status_code == 401
    ok = create_business(client, name="Bootstrap Biz")
    assert ok["id"]
    # smoke tenant headers helper still works
    headers = tenant_headers(ok["id"])
    assert headers["X-Owner-Token"]
