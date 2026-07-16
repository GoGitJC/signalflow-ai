from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import Business, User, UserRole


def _extract_access_token(
    authorization: str | None,
    access_cookie: str | None,
) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return access_cookie


def get_current_user(
    authorization: str | None = Header(default=None),
    sf_access: str | None = Cookie(default=None, alias="sf_access"),
    db: Session = Depends(get_db),
) -> User:
    settings = get_settings()
    cookie_name = settings.auth_access_cookie_name
    # Prefer configured cookie name; TestClient may still use default alias.
    token = _extract_access_token(authorization, sf_access)
    if token is None and cookie_name != "sf_access":
        # Fallback handled via request cookies in route layer when needed.
        pass
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    payload = decode_access_token(settings, token)
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


def require_bootstrap_owner(
    x_owner_token: str | None = Header(default=None),
) -> None:
    """Shared-secret gate for bootstrap endpoints (e.g. create business without JWT)."""
    settings = get_settings()
    if not settings.owner_api_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Owner API token is not configured",
        )
    if not x_owner_token or x_owner_token != settings.owner_api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Owner authentication required",
        )


def require_owner_token(
    x_owner_token: str | None = Header(default=None),
    x_business_id: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> str:
    """Legacy shared-secret owner auth. Prefer cookie/JWT session auth."""
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


def _resolve_authenticated_business_id(
    *,
    authorization: str | None,
    access_cookie: str | None,
    x_owner_token: str | None,
    x_business_id: str | None,
    db: Session,
    admin_only: bool,
) -> str:
    token = _extract_access_token(authorization, access_cookie)
    if token:
        user = get_current_user(authorization=authorization, sf_access=access_cookie, db=db)
        if admin_only and user.role not in {UserRole.owner, UserRole.admin}:
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


def require_business_member(
    authorization: str | None = Header(default=None),
    sf_access: str | None = Cookie(default=None, alias="sf_access"),
    x_owner_token: str | None = Header(default=None),
    x_business_id: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> str:
    """Resolve tenant from cookie/JWT membership (any role) or legacy owner-token fallback."""
    return _resolve_authenticated_business_id(
        authorization=authorization,
        access_cookie=sf_access,
        x_owner_token=x_owner_token,
        x_business_id=x_business_id,
        db=db,
        admin_only=False,
    )


def require_business_admin(
    authorization: str | None = Header(default=None),
    sf_access: str | None = Cookie(default=None, alias="sf_access"),
    x_owner_token: str | None = Header(default=None),
    x_business_id: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> str:
    """Resolve tenant from cookie/JWT membership, with legacy owner-token fallback."""
    return _resolve_authenticated_business_id(
        authorization=authorization,
        access_cookie=sf_access,
        x_owner_token=x_owner_token,
        x_business_id=x_business_id,
        db=db,
        admin_only=True,
    )


def assert_tenant_access(authenticated_business_id: str, requested_business_id: str) -> None:
    if authenticated_business_id != requested_business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed for this business",
        )
