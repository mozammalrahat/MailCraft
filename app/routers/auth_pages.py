from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.session import get_db
from app.routers.api.auth_api import clear_auth_cookies, set_auth_cookies
from app.services.auth_service import (
    REFRESH_COOKIE,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_optional_user,
    register_user,
    revoke_refresh_token,
)

router = APIRouter(tags=["auth-pages"])
templates = Jinja2Templates(directory="app/templates")

DbDep = Annotated[Session, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.get("/auth/login")
def login_page(request: Request, user=Depends(get_optional_user)):
    if user:
        return RedirectResponse("/dashboard", status_code=303)
    return templates.TemplateResponse(
        request,
        "pages/auth/login.html",
        {"error": None},
    )


@router.post("/auth/login")
def login_submit(
    request: Request,
    response: Response,
    db: DbDep,
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
    redirect = RedirectResponse("/dashboard", status_code=303)
    set_auth_cookies(redirect, access, refresh, settings)
    return redirect


@router.get("/auth/register")
def register_page(request: Request, user=Depends(get_optional_user)):
    if user:
        return RedirectResponse("/dashboard", status_code=303)
    return templates.TemplateResponse(
        request,
        "pages/auth/register.html",
        {"error": None},
    )


@router.post("/auth/register")
def register_submit(
    request: Request,
    db: DbDep,
    settings: SettingsDep,
    email: Annotated[str, Form(...)],
    password: Annotated[str, Form(...)],
):
    from fastapi import HTTPException

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
    redirect = RedirectResponse("/dashboard", status_code=303)
    set_auth_cookies(redirect, access, refresh, settings)
    return redirect


@router.post("/auth/logout")
def logout_submit(request: Request, db: DbDep, settings: SettingsDep):
    refresh = request.cookies.get(REFRESH_COOKIE)
    if refresh:
        try:
            payload = decode_token(refresh, settings)
            jti = payload.get("jti")
            if payload.get("type") == "refresh" and jti:
                revoke_refresh_token(db, str(jti))
        except HTTPException:
            pass

    redirect = RedirectResponse("/", status_code=303)
    clear_auth_cookies(redirect)
    return redirect
