from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models import Business, User, UserRole


def require_owner_token(
    x_owner_token: str | None = Header(default=None),
    x_business_id: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> str:
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
