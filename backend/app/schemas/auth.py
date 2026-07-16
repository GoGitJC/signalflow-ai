from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    business_name: str = Field(min_length=1, max_length=200)
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    remember_me: bool = False


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    remember_me: bool = False


class RefreshRequest(BaseModel):
    refresh_token: str | None = Field(default=None, min_length=20)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20)
    password: str = Field(min_length=8, max_length=128)


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=8)


class InviteCreateRequest(BaseModel):
    email: EmailStr
    role: str = Field(default="member", pattern="^(admin|member)$")


class AcceptInviteRequest(BaseModel):
    token: str = Field(min_length=20)
    name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=8, max_length=128)


class SessionResponse(BaseModel):
    """Cookie-based session payload — tokens are HttpOnly cookies, not returned."""

    user_id: str
    business_id: str
    role: str
    email: str
    name: str
    email_verified: bool
    expires_in: int


class UserResponse(BaseModel):
    id: str
    business_id: str
    name: str
    email: str
    role: str
    email_verified: bool = False
    created_at: datetime


class InvitationResponse(BaseModel):
    id: str
    business_id: str
    email: str
    role: str
    expires_at: datetime
    accepted_at: datetime | None
    created_at: datetime
    invite_token: str | None = None


class MessageResponse(BaseModel):
    detail: str
    reset_token: str | None = None
    verify_token: str | None = None
