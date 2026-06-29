"""Authentication request schemas."""

from pydantic import BaseModel, EmailStr, Field


class UserRegistrationRequest(BaseModel):
    """Registration payload."""

    email: EmailStr
    password: str = Field(min_length=8)


class UserLoginRequest(BaseModel):
    """Login payload."""

    email: EmailStr
    password: str
