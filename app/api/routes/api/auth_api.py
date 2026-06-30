from typing import Annotated

from app.api.dependencies.authentication import CurrentUserDependency
from app.api.dependencies.database import DatabaseSessionDependency
from app.application.services.authentication_service import (
    ACCESS_COOKIE_NAME,
    REFRESH_COOKIE_NAME,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    register_user,
    rotate_refresh_token,
)
from app.core.configuration import Settings, get_settings
from app.core.rate_limits import limiter
from app.schemas.authentication import UserLoginRequest, UserRegistrationRequest
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth-api"])

SettingsDep = Annotated[Settings, Depends(get_settings)]


class TokenResponse(BaseModel):
    message: str


def _cookie_kwargs(settings: Settings) -> dict:
    return {
        "httponly": True,
        "samesite": "lax",
        "secure": not settings.debug,
        "path": "/",
    }


def set_auth_cookies(
    response: Response,
    access: str,
    refresh: str,
    settings: Settings,
) -> None:
    cookie_kwargs = _cookie_kwargs(settings)
    response.set_cookie(
        ACCESS_COOKIE_NAME,
        access,
        max_age=settings.jwt_access_expire_minutes * 60,
        **cookie_kwargs,
    )
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        refresh,
        max_age=settings.jwt_refresh_expire_days * 86400,
        **cookie_kwargs,
    )


def clear_auth_cookies(response: Response, settings: Settings) -> None:
    cookie_kwargs = _cookie_kwargs(settings)
    response.delete_cookie(ACCESS_COOKIE_NAME, **cookie_kwargs)
    response.delete_cookie(REFRESH_COOKIE_NAME, **cookie_kwargs)


@router.post("/register", response_model=TokenResponse)
@limiter.limit("10/minute")
def api_register(
    request: Request,
    payload: UserRegistrationRequest,
    response: Response,
    db: DatabaseSessionDependency,
    settings: SettingsDep,
) -> TokenResponse:
    user = register_user(db, payload.email, payload.password)
    access = create_access_token(user.id, settings)
    refresh = create_refresh_token(user.id, db, settings)
    set_auth_cookies(response, access, refresh, settings)
    return TokenResponse(message="Registered successfully")


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def api_login(
    request: Request,
    payload: UserLoginRequest,
    response: Response,
    db: DatabaseSessionDependency,
    settings: SettingsDep,
) -> TokenResponse:
    user = authenticate_user(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    access = create_access_token(user.id, settings)
    refresh = create_refresh_token(user.id, db, settings)
    set_auth_cookies(response, access, refresh, settings)
    return TokenResponse(message="Logged in successfully")


@router.get("/me")
def api_me(user: CurrentUserDependency) -> dict:
    return {"id": user.id, "email": user.email}


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("30/minute")
def api_refresh(
    request: Request,
    response: Response,
    db: DatabaseSessionDependency,
    settings: SettingsDep,
) -> TokenResponse:
    refresh = request.cookies.get(REFRESH_COOKIE_NAME)
    if not refresh:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_token(refresh, settings)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    access, new_refresh = rotate_refresh_token(db, payload, settings)
    set_auth_cookies(response, access, new_refresh, settings)
    return TokenResponse(message="Token refreshed")
