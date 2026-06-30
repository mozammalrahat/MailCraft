from typing import Annotated

from app.api.dependencies.authentication import OptionalUserDependency
from app.api.dependencies.database import DatabaseSessionDependency
from app.api.routes.api.auth_api import clear_auth_cookies, set_auth_cookies
from app.application.services.authentication_service import (
    REFRESH_COOKIE_NAME,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    purge_expired_tokens,
    register_user,
    revoke_refresh_token,
)
from app.core.configuration import Settings, get_settings
from app.core.rate_limits import limiter
from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["auth-pages"])
templates = Jinja2Templates(directory="app/templates")

SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.get("/auth/login")
def login_page(request: Request, user: OptionalUserDependency):
    if user:
        return RedirectResponse("/dashboard", status_code=303)
    return templates.TemplateResponse(
        request,
        "pages/auth/login.html",
        {"error": None},
    )


@router.post("/auth/login")
@limiter.limit("10/minute")
def login_submit(
    request: Request,
    response: Response,
    db: DatabaseSessionDependency,
    settings: SettingsDep,
    email: Annotated[str, Form(...)],
    password: Annotated[str, Form(...)],
):
    user = authenticate_user(db, email, password)
    if user is None:
        return templates.TemplateResponse(
            request,
            "pages/auth/login.html",
            {"error": "Invalid email or password"},
            status_code=400,
        )
    access = create_access_token(user.id, settings)
    refresh = create_refresh_token(user.id, db, settings)
    purge_expired_tokens(db, user.id)
    redirect = RedirectResponse("/dashboard", status_code=303)
    set_auth_cookies(redirect, access, refresh, settings)
    return redirect


@router.get("/auth/register")
def register_page(request: Request, user: OptionalUserDependency):
    if user:
        return RedirectResponse("/dashboard", status_code=303)
    return templates.TemplateResponse(
        request,
        "pages/auth/register.html",
        {"error": None},
    )


@router.post("/auth/register")
@limiter.limit("10/minute")
def register_submit(
    request: Request,
    db: DatabaseSessionDependency,
    settings: SettingsDep,
    email: Annotated[str, Form(...)],
    password: Annotated[str, Form(...)],
):
    try:
        user = register_user(db, email, password)
    except HTTPException as exc:
        return templates.TemplateResponse(
            request,
            "pages/auth/register.html",
            {"error": exc.detail},
            status_code=400,
        )

    access = create_access_token(user.id, settings)
    refresh = create_refresh_token(user.id, db, settings)
    purge_expired_tokens(db, user.id)
    redirect = RedirectResponse("/dashboard", status_code=303)
    set_auth_cookies(redirect, access, refresh, settings)
    return redirect


@router.post("/auth/logout")
def logout_submit(
    request: Request,
    db: DatabaseSessionDependency,
    settings: SettingsDep,
):
    refresh = request.cookies.get(REFRESH_COOKIE_NAME)
    if refresh:
        try:
            payload = decode_token(refresh, settings)
            jti = payload.get("jti")
            if payload.get("type") == "refresh" and jti:
                revoke_refresh_token(db, str(jti))
        except HTTPException:
            pass

    redirect = RedirectResponse("/", status_code=303)
    clear_auth_cookies(redirect, settings)
    return redirect
