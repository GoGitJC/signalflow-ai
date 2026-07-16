from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import Business, User, UserRole


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer access token required",
        )
    token = authorization.split(" ", 1)[1].strip()
    payload = decode_access_token(get_settings(), token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject"
        )
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    token_business = payload.get("business_id")
    if token_business and token_business != user.business_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token tenant mismatch"
        )
    return user


def require_owner_token(
    x_owner_token: str | None = Header(default=None),
    x_business_id: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> str:
    """Legacy shared-secret owner auth. Prefer Bearer JWT via require_business_admin."""
    settings = get_settings()
    if not settings.owner_api_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Owner API token is not configured",
        )
    if not x_owner_token or not x_business_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Owner authentication headers are required",
        )
    if x_owner_token != settings.owner_api_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid owner token")
    business = db.get(Business, x_business_id)
    if business is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")
    user = db.scalar(
        select(User).where(
            User.business_id == x_business_id,
            User.role.in_([UserRole.owner, UserRole.admin]),
        )
    )
    if user is None and settings.is_live_mode:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No owner/admin user found for this business",
        )
    return x_business_id


def require_business_admin(
    authorization: str | None = Header(default=None),
    x_owner_token: str | None = Header(default=None),
    x_business_id: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> str:
    """Resolve tenant from JWT membership, with legacy owner-token fallback."""
    if authorization and authorization.lower().startswith("bearer "):
        user = get_current_user(authorization=authorization, db=db)
        if user.role not in {UserRole.owner, UserRole.admin}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Owner or admin role required",
            )
        return user.business_id
    return require_owner_token(
        x_owner_token=x_owner_token,
        x_business_id=x_business_id,
        db=db,
    )
