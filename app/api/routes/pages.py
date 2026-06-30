from dataclasses import dataclass, field
from typing import Annotated

from app.api.dependencies.authentication import (
    AuthenticatedPageUserDependency,
    OptionalUserDependency,
)
from app.api.dependencies.database import DatabaseSessionDependency
from app.api.dependencies.large_language_model import (
    LargeLanguageModelClientDependency,
    SettingsDependency,
)
from app.application.handlers.email_generation_handler import EmailGenerationHandler
from app.core.configuration import Settings, get_settings
from app.core.exceptions import LlmError, ServiceValidationError
from app.core.rate_limits import limiter
from app.domain.enums.email_strategy import EmailStrategy
from app.domain.enums.email_tone import EmailTone
from app.schemas.email_generation import EmailGenerationRequest
from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="app/templates")
_email_generation_handler = EmailGenerationHandler()

TONE_OPTIONS = [tone.value for tone in EmailTone]

IntentForm = Annotated[str, Form(...)]
KeyFactsForm = Annotated[list[str], Form(...)]
ToneForm = Annotated[str, Form(...)]
StrategyForm = Annotated[str, Form()]


@dataclass
class FormState:
    intent: str = ""
    key_facts: list[str] = field(default_factory=lambda: [""])
    tone: str = EmailTone.FORMAL.value
    strategy: str = "strategy_a"


@dataclass
class FlashMessage:
    type: str
    text: str


@dataclass
class EmailPreview:
    email: str
    subject: str | None
    tone: str
    strategy: str
    raw_email: str | None = None
    raw_subject: str | None = None
    show_comparison: bool = False


def _render_generate_page(
    request: Request,
    *,
    user: object | None = None,
    form: FormState | None = None,
    email_result: EmailPreview | None = None,
    messages: list[FlashMessage] | None = None,
    settings: Settings | None = None,
) -> object:
    app_settings = settings or get_settings()
    return templates.TemplateResponse(
        request=request,
        name="pages/generate.html",
        context={
            "user": user,
            "form": form or FormState(),
            "email_result": email_result,
            "messages": messages or [],
            "tone_options": TONE_OPTIONS,
            "debug": app_settings.debug,
        },
    )


@router.get("/")
def index(request: Request, user: OptionalUserDependency) -> object:
    return templates.TemplateResponse(
        request=request,
        name="pages/index.html",
        context={"title": "MailCraft", "user": user},
    )


@router.get("/generate")
def generate_form(
    request: Request,
    page_user: AuthenticatedPageUserDependency,
) -> object:
    if isinstance(page_user, RedirectResponse):
        return page_user
    return _render_generate_page(request, user=page_user)


@router.post("/generate")
@limiter.limit("20/hour")
async def generate_submit(
    request: Request,
    language_model_client: LargeLanguageModelClientDependency,
    settings: SettingsDependency,
    database_session: DatabaseSessionDependency,
    page_user: AuthenticatedPageUserDependency,
    intent: IntentForm,
    key_facts: KeyFactsForm,
    tone: ToneForm,
    strategy: StrategyForm = "strategy_a",
) -> object:
    if isinstance(page_user, RedirectResponse):
        return page_user

    form = FormState(
        intent=intent.strip(),
        key_facts=[fact.strip() for fact in key_facts if fact.strip()] or [""],
        tone=tone,
        strategy=strategy,
    )

    cleaned_facts = [fact for fact in form.key_facts if fact]
    if not cleaned_facts:
        return _render_generate_page(
            request,
            user=page_user,
            form=form,
            messages=[FlashMessage("error", "At least one key fact is required.")],
        )

    try:
        email_tone = EmailTone(tone)
    except ValueError:
        return _render_generate_page(
            request,
            user=page_user,
            form=form,
            messages=[FlashMessage("error", f"Invalid tone: {tone}")],
        )

    try:
        email_strategy = EmailStrategy(strategy)
    except ValueError:
        return _render_generate_page(
            request,
            user=page_user,
            form=form,
            messages=[FlashMessage("error", f"Invalid strategy: {strategy}")],
        )

    generation_request = EmailGenerationRequest(
        intent=form.intent,
        key_facts=cleaned_facts,
        tone=email_tone,
        strategy=email_strategy,
    )

    try:
        result = await _email_generation_handler.generate_from_api(
            request=generation_request,
            user_id=page_user.id,
            database_session=database_session,
            settings=settings,
            language_model_client=language_model_client,
        )
    except ServiceValidationError as exc:
        return _render_generate_page(
            request,
            user=page_user,
            form=form,
            messages=[FlashMessage("error", exc.message)],
        )
    except LlmError as exc:
        return _render_generate_page(
            request,
            user=page_user,
            form=form,
            messages=[FlashMessage("error", exc.message)],
        )

    return _render_generate_page(
        request,
        user=page_user,
        form=form,
        email_result=EmailPreview(
            email=result.email,
            subject=result.subject,
            tone=tone,
            strategy=result.strategy,
            raw_email=result.raw_email,
            raw_subject=result.raw_subject,
            show_comparison=settings.debug and bool(result.raw_email),
        ),
        messages=[FlashMessage("success", "Saved to history.")],
        settings=settings,
    )
