"""Authentication service for users and JWT tokens."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

import bcrypt
import jwt
from app.application.services.default_scenario_templates import (
    DEFAULT_SCENARIO_TEMPLATES,
)
from app.core.configuration import Settings, get_settings
from app.database.models.refresh_token import RefreshToken
from app.database.models.scenario import Scenario
from app.database.models.user import User
from app.database.session import get_database_session
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

ACCESS_COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"
JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Hash a plaintext password."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a hash."""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def _hash_token(token: str) -> str:
    """Hash a refresh token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(user_id: int, settings: Settings) -> str:
    """Create a short-lived access JWT."""
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_access_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: int, database_session: Session, settings: Settings) -> str:
    """Create and store a refresh token."""
    token_identifier = secrets.token_urlsafe(32)
    token = secrets.token_urlsafe(48)
    expire = datetime.now(UTC) + timedelta(days=settings.jwt_refresh_expire_days)
    database_session.add(
        RefreshToken(
            jti=token_identifier,
            token_hash=_hash_token(token),
            user_id=user_id,
            expires_at=expire,
        )
    )
    database_session.commit()
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
        "jti": token_identifier,
        "token": token,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=JWT_ALGORITHM)


def decode_token(token: str, settings: Settings) -> dict:
    """Decode and validate a JWT."""
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc


def revoke_refresh_token(database_session: Session, token_identifier: str) -> None:
    """Revoke a refresh token by identifier."""
    record = (
        database_session.query(RefreshToken)
        .filter(RefreshToken.jti == token_identifier)
        .first()
    )
    if record and record.revoked_at is None:
        record.revoked_at = datetime.now(UTC)
        database_session.commit()


def rotate_refresh_token(
    database_session: Session, payload: dict, settings: Settings
) -> tuple[str, str]:
    """Rotate refresh token and issue new access token."""
    token_identifier = payload.get("jti")
    token = payload.get("token")
    user_id = int(payload["sub"])
    if not token_identifier or not token:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    record = (
        database_session.query(RefreshToken)
        .filter(RefreshToken.jti == token_identifier)
        .first()
    )
    if (
        record is None
        or record.revoked_at is not None
        or record.token_hash != _hash_token(str(token))
        or record.expires_at < datetime.now(UTC)
    ):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    revoke_refresh_token(database_session, str(token_identifier))
    access = create_access_token(user_id, settings)
    refresh = create_refresh_token(user_id, database_session, settings)
    return access, refresh


def seed_default_scenarios(database_session: Session, user_id: int) -> None:
    """Seed default scenarios for a new user."""
    for template in DEFAULT_SCENARIO_TEMPLATES:
        database_session.add(
            Scenario(
                user_id=user_id,
                name=template["name"],
                purpose=template["purpose"],
                document_type=template["document_type"],
                system_prompt=template["system_prompt"],
                is_default=True,
            )
        )
    database_session.commit()


def register_user(database_session: Session, email: str, password: str) -> User:
    """Register a new user and seed default scenarios."""
    existing = database_session.query(User).filter(User.email == email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=email.lower(), hashed_password=hash_password(password))
    database_session.add(user)
    database_session.commit()
    database_session.refresh(user)
    seed_default_scenarios(database_session, user.id)
    return user


def authenticate_user(
    database_session: Session, email: str, password: str,
) -> User | None:
    """Authenticate a user by email and password."""
    user = database_session.query(User).filter(User.email == email.lower()).first()
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user


def get_user_from_access_token(
    database_session: Session, token: str, settings: Settings,
) -> User:
    """Resolve a user from an access token."""
    payload = decode_token(token, settings)
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid access token")
    user = database_session.query(User).filter(User.id == int(payload["sub"])).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_current_user(
    request: Request,
    database_session: Annotated[Session, Depends(get_database_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    """FastAPI dependency returning the authenticated user."""
    token = request.cookies.get(ACCESS_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return get_user_from_access_token(database_session, token, settings)


def get_optional_user(
    request: Request,
    database_session: Annotated[Session, Depends(get_database_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User | None:
    """Return authenticated user when present, otherwise None."""
    token = request.cookies.get(ACCESS_COOKIE_NAME)
    if not token:
        return None
    try:
        return get_user_from_access_token(database_session, token, settings)
    except HTTPException:
        return None
