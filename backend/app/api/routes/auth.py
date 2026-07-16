from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token_value,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.db.session import get_db
from app.models import Business, RefreshToken, User, UserRole
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


def _issue_tokens(db: Session, user: User) -> TokenResponse:
    access = create_access_token(
        settings=settings,
        user_id=user.id,
        business_id=user.business_id,
        role=user.role.value,
    )
    refresh = create_refresh_token_value()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh),
            expires_at=datetime.now(UTC) + timedelta(days=settings.jwt_refresh_ttl_days),
        )
    )
    db.commit()
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.jwt_access_ttl_minutes * 60,
        business_id=user.business_id,
        user_id=user.id,
        role=user.role.value,
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
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
    )
    db.add(user)
    db.flush()
    return _issue_tokens(db, user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return _issue_tokens(db, user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    token_hash = hash_refresh_token(payload.refresh_token)
    stored = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if stored is None or stored.revoked_at is not None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    if stored.expires_at.tzinfo is None:
        expires_at = stored.expires_at.replace(tzinfo=UTC)
    else:
        expires_at = stored.expires_at
    if expires_at <= datetime.now(UTC):
        raise HTTPException(status_code=401, detail="Refresh token expired")

    user = db.get(User, stored.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    stored.revoked_at = datetime.now(UTC)
    db.flush()
    return _issue_tokens(db, user)


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return UserResponse(
        id=user.id,
        business_id=user.business_id,
        name=user.name,
        email=user.email,
        role=user.role.value,
        created_at=user.created_at,
    )
