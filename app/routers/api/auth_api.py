from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.models import User
from app.db.session import get_db
from app.schemas.stateful import UserLogin, UserRegister
from app.services.auth_service import (
    ACCESS_COOKIE,
    REFRESH_COOKIE,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    register_user,
    rotate_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["auth-api"])

DbDep = Annotated[Session, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


class TokenResponse(BaseModel):
    message: str


def set_auth_cookies(response: Response, access: str, refresh: str, settings: Settings) -> None:
    response.set_cookie(
        ACCESS_COOKIE,
        access,
        httponly=True,
        samesite="lax",
        max_age=settings.jwt_access_expire_minutes * 60,
    )
    response.set_cookie(
        REFRESH_COOKIE,
        refresh,
        httponly=True,
        samesite="lax",
        max_age=settings.jwt_refresh_expire_days * 86400,
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE)
    response.delete_cookie(REFRESH_COOKIE)


@router.post("/register", response_model=TokenResponse)
def api_register(
    payload: UserRegister,
    response: Response,
    db: DbDep,
    settings: SettingsDep,
) -> TokenResponse:
    user = register_user(db, payload.email, payload.password)
    access = create_access_token(user.id, settings)
    refresh = create_refresh_token(user.id, db, settings)
    set_auth_cookies(response, access, refresh, settings)
    return TokenResponse(message="Registered successfully")


@router.post("/login", response_model=TokenResponse)
def api_login(
    payload: UserLogin,
    response: Response,
    db: DbDep,
    settings: SettingsDep,
) -> TokenResponse:
    from fastapi import HTTPException

    user = authenticate_user(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    access = create_access_token(user.id, settings)
    refresh = create_refresh_token(user.id, db, settings)
    set_auth_cookies(response, access, refresh, settings)
    return TokenResponse(message="Logged in successfully")


@router.get("/me")
def api_me(user: CurrentUserDep) -> dict:
    return {"id": user.id, "email": user.email}


@router.post("/refresh", response_model=TokenResponse)
def api_refresh(
    request: Request,
    response: Response,
    db: DbDep,
    settings: SettingsDep,
) -> TokenResponse:
    refresh = request.cookies.get(REFRESH_COOKIE)
    if not refresh:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_token(refresh, settings)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    access, new_refresh = rotate_refresh_token(db, payload, settings)
    set_auth_cookies(response, access, new_refresh, settings)
    return TokenResponse(message="Token refreshed")
