from app.api.dependencies.authentication import OptionalUserDependency
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def index(request: Request, user: OptionalUserDependency) -> object:
    return templates.TemplateResponse(
        request=request,
        name="pages/index.html",
        context={"title": "MailCraft", "user": user},
    )
