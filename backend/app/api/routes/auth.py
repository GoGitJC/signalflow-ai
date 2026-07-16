from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_business_admin
from app.core.config import get_settings
from app.core.cookies import clear_auth_cookies, set_auth_cookies
from app.core.security import (
    create_access_token,
    create_refresh_token_value,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.db.session import get_db
from app.models import (
    Business,
    Invitation,
    PasswordResetToken,
    RefreshToken,
    User,
    UserRole,
)
from app.schemas.auth import (
    AcceptInviteRequest,
    ForgotPasswordRequest,
    InvitationResponse,
    InviteCreateRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResetPasswordRequest,
    SessionResponse,
    UserResponse,
    VerifyEmailRequest,
)
from app.services.audit import record_auth_audit

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        business_id=user.business_id,
        name=user.name,
        email=user.email,
        role=user.role.value,
        email_verified=user.email_verified_at is not None,
        created_at=user.created_at,
    )


def _session_response(user: User) -> SessionResponse:
    return SessionResponse(
        user_id=user.id,
        business_id=user.business_id,
        role=user.role.value,
        email=user.email,
        name=user.name,
        email_verified=user.email_verified_at is not None,
        expires_in=settings.jwt_access_ttl_minutes * 60,
    )


def _issue_session(
    db: Session,
    response: Response,
    user: User,
    *,
    remember_me: bool = False,
) -> SessionResponse:
    access = create_access_token(
        settings=settings,
        user_id=user.id,
        business_id=user.business_id,
        role=user.role.value,
    )
    refresh_days = (
        settings.jwt_refresh_remember_days if remember_me else settings.jwt_refresh_ttl_days
    )
    refresh = create_refresh_token_value()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh),
            expires_at=datetime.now(UTC) + timedelta(days=refresh_days),
        )
    )
    db.commit()
    set_auth_cookies(
        response,
        settings=settings,
        access_token=access,
        refresh_token=refresh,
        remember_me=remember_me,
    )
    return _session_response(user)


@router.post("/register", response_model=SessionResponse, status_code=201)
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    existing = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Email already registered")

    business = Business(name=payload.business_name)
    db.add(business)
    db.flush()
    user = User(
        business_id=business.id,
        name=payload.name,
        email=str(payload.email).lower(),
        password_hash=hash_password(payload.password),
        role=UserRole.owner,
        email_verified_at=None,
    )
    db.add(user)
    db.flush()
    record_auth_audit(
        db,
        action="register",
        status="ok",
        business_id=business.id,
        user_id=user.id,
    )
    return _issue_session(db, response, user, remember_me=payload.remember_me)


@router.post("/login", response_model=SessionResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    email = str(payload.email).lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(payload.password, user.password_hash):
        record_auth_audit(db, action="login", status="denied", detail=f"email={email}")
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid email or password")
    record_auth_audit(
        db,
        action="login",
        status="ok",
        business_id=user.business_id,
        user_id=user.id,
    )
    return _issue_session(db, response, user, remember_me=payload.remember_me)


@router.post("/refresh", response_model=SessionResponse)
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    token = request.cookies.get(settings.auth_refresh_cookie_name)
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token required")

    token_hash = hash_refresh_token(token)
    stored = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if stored is None or stored.revoked_at is not None:
        record_auth_audit(db, action="refresh", status="denied", detail="invalid_token")
        db.commit()
        clear_auth_cookies(response, settings=settings)
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    expires_at = (
        stored.expires_at.replace(tzinfo=UTC)
        if stored.expires_at.tzinfo is None
        else stored.expires_at
    )
    if expires_at <= datetime.now(UTC):
        record_auth_audit(db, action="refresh", status="denied", detail="expired")
        db.commit()
        clear_auth_cookies(response, settings=settings)
        raise HTTPException(status_code=401, detail="Refresh token expired")

    user = db.get(User, stored.user_id)
    if user is None:
        record_auth_audit(db, action="refresh", status="denied", detail="user_missing")
        db.commit()
        clear_auth_cookies(response, settings=settings)
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    stored.revoked_at = datetime.now(UTC)
    record_auth_audit(
        db,
        action="refresh",
        status="ok",
        business_id=user.business_id,
        user_id=user.id,
    )
    db.flush()
    return _issue_session(db, response, user, remember_me=False)


@router.post("/logout", response_model=MessageResponse)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(settings.auth_refresh_cookie_name)
    if token:
        stored = db.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(token))
        )
        if stored and stored.revoked_at is None:
            stored.revoked_at = datetime.now(UTC)
            record_auth_audit(
                db,
                action="logout",
                status="ok",
                user_id=stored.user_id,
            )
            db.commit()
    clear_auth_cookies(response, settings=settings)
    return MessageResponse(detail="Logged out")


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return _user_response(user)


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    email = str(payload.email).lower()
    user = db.scalar(select(User).where(User.email == email))
    # Always return success to avoid account enumeration.
    reset_token = None
    if user is not None:
        reset_token = create_refresh_token_value()
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=hash_refresh_token(reset_token),
                expires_at=datetime.now(UTC) + timedelta(hours=1),
            )
        )
        record_auth_audit(
            db,
            action="forgot_password",
            status="ok",
            business_id=user.business_id,
            user_id=user.id,
        )
        db.commit()
    return MessageResponse(
        detail="If that email is registered, a reset link has been prepared.",
        reset_token=reset_token,
    )


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    token_hash = hash_refresh_token(payload.token)
    stored = db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )
    if stored is None or stored.used_at is not None:
        raise HTTPException(status_code=400, detail="Invalid or used reset token")
    expires_at = (
        stored.expires_at.replace(tzinfo=UTC)
        if stored.expires_at.tzinfo is None
        else stored.expires_at
    )
    if expires_at <= datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Reset token expired")
    user = db.get(User, stored.user_id)
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid reset token")
    user.password_hash = hash_password(payload.password)
    stored.used_at = datetime.now(UTC)
    # Revoke all refresh tokens on password change.
    for item in db.scalars(select(RefreshToken).where(RefreshToken.user_id == user.id)):
        if item.revoked_at is None:
            item.revoked_at = datetime.now(UTC)
    record_auth_audit(
        db,
        action="reset_password",
        status="ok",
        business_id=user.business_id,
        user_id=user.id,
    )
    db.commit()
    return MessageResponse(detail="Password updated")


@router.post("/verify-email", response_model=MessageResponse)
def verify_email(
    payload: VerifyEmailRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Placeholder verification: any non-empty token marks the current user verified.
    if not payload.token.strip():
        raise HTTPException(status_code=400, detail="Verification token required")
    user.email_verified_at = datetime.now(UTC)
    record_auth_audit(
        db,
        action="verify_email",
        status="ok",
        business_id=user.business_id,
        user_id=user.id,
    )
    db.commit()
    return MessageResponse(detail="Email verified", verify_token=payload.token)


@router.get("/users", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    tenant_id: Annotated[str, Depends(require_business_admin)] = "",
):
    users = list(db.scalars(select(User).where(User.business_id == tenant_id)))
    return [_user_response(user) for user in users]


@router.get("/invitations", response_model=list[InvitationResponse])
def list_invitations(
    db: Session = Depends(get_db),
    tenant_id: Annotated[str, Depends(require_business_admin)] = "",
):
    rows = list(
        db.scalars(
            select(Invitation)
            .where(Invitation.business_id == tenant_id)
            .order_by(Invitation.created_at.desc())
        )
    )
    return [
        InvitationResponse(
            id=row.id,
            business_id=row.business_id,
            email=row.email,
            role=row.role,
            expires_at=row.expires_at,
            accepted_at=row.accepted_at,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.post("/invitations", response_model=InvitationResponse, status_code=201)
def create_invitation(
    payload: InviteCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    tenant_id: Annotated[str, Depends(require_business_admin)] = "",
):
    email = str(payload.email).lower()
    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise HTTPException(status_code=409, detail="User already exists")
    token = create_refresh_token_value()
    invite = Invitation(
        business_id=tenant_id,
        email=email,
        role=payload.role,
        token_hash=hash_refresh_token(token),
        invited_by_user_id=user.id,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db.add(invite)
    record_auth_audit(
        db,
        action="invite_create",
        status="ok",
        business_id=tenant_id,
        user_id=user.id,
        detail=f"email={email}",
    )
    db.commit()
    db.refresh(invite)
    return InvitationResponse(
        id=invite.id,
        business_id=invite.business_id,
        email=invite.email,
        role=invite.role,
        expires_at=invite.expires_at,
        accepted_at=invite.accepted_at,
        created_at=invite.created_at,
        invite_token=token,
    )


@router.post("/invitations/accept", response_model=SessionResponse, status_code=201)
def accept_invitation(
    payload: AcceptInviteRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    stored = db.scalar(
        select(Invitation).where(Invitation.token_hash == hash_refresh_token(payload.token))
    )
    if stored is None or stored.accepted_at is not None:
        raise HTTPException(status_code=400, detail="Invalid or used invitation")
    expires_at = (
        stored.expires_at.replace(tzinfo=UTC)
        if stored.expires_at.tzinfo is None
        else stored.expires_at
    )
    if expires_at <= datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Invitation expired")
    if db.scalar(select(User).where(User.email == stored.email)) is not None:
        raise HTTPException(status_code=409, detail="Email already registered")

    role = UserRole.admin if stored.role == "admin" else UserRole.member
    user = User(
        business_id=stored.business_id,
        name=payload.name,
        email=stored.email,
        password_hash=hash_password(payload.password),
        role=role,
        email_verified_at=datetime.now(UTC),
    )
    db.add(user)
    stored.accepted_at = datetime.now(UTC)
    db.flush()
    record_auth_audit(
        db,
        action="invite_accept",
        status="ok",
        business_id=stored.business_id,
        user_id=user.id,
    )
    return _issue_session(db, response, user, remember_me=False)
