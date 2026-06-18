from dataclasses import dataclass, field
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.templating import Jinja2Templates

from app.config import Settings, get_settings
from app.dependencies import get_llm_client
from app.schemas.email import EmailGenerationRequest, EmailStrategy, EmailTone
from app.services.email.generation import generate_email
from app.services.errors import LlmError, ServiceValidationError
from app.services.llm.client import LlmClient

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="app/templates")

TONE_OPTIONS = [tone.value for tone in EmailTone]

IntentForm = Annotated[str, Form(...)]
KeyFactsForm = Annotated[list[str], Form(...)]
ToneForm = Annotated[str, Form(...)]
StrategyForm = Annotated[str, Form()]
LlmClientDep = Annotated[LlmClient, Depends(get_llm_client)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


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


def _render_generate_page(
    request: Request,
    *,
    form: FormState | None = None,
    email_result: EmailPreview | None = None,
    messages: list[FlashMessage] | None = None,
) -> object:
    return templates.TemplateResponse(
        request=request,
        name="pages/generate.html",
        context={
            "form": form or FormState(),
            "email_result": email_result,
            "messages": messages or [],
            "tone_options": TONE_OPTIONS,
        },
    )


@router.get("/")
def index(request: Request) -> object:
    return templates.TemplateResponse(
        request=request,
        name="pages/index.html",
        context={"title": "MailCraft"},
    )


@router.get("/generate")
def generate_form(request: Request) -> object:
    return _render_generate_page(request)


@router.post("/generate")
async def generate_submit(
    request: Request,
    llm_client: LlmClientDep,
    settings: SettingsDep,
    intent: IntentForm,
    key_facts: KeyFactsForm,
    tone: ToneForm,
    strategy: StrategyForm = "strategy_a",
) -> object:
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
            form=form,
            messages=[FlashMessage("error", "At least one key fact is required.")],
        )

    try:
        email_tone = EmailTone(tone)
    except ValueError:
        return _render_generate_page(
            request,
            form=form,
            messages=[FlashMessage("error", f"Invalid tone: {tone}")],
        )

    try:
        email_strategy = EmailStrategy(strategy)
    except ValueError:
        return _render_generate_page(
            request,
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
        result = await generate_email(generation_request, llm_client, settings)
    except ServiceValidationError as exc:
        return _render_generate_page(
            request,
            form=form,
            messages=[FlashMessage("error", exc.message)],
        )
    except LlmError as exc:
        return _render_generate_page(
            request,
            form=form,
            messages=[FlashMessage("error", exc.message)],
        )

    return _render_generate_page(
        request,
        form=form,
        email_result=EmailPreview(
            email=result.email,
            subject=result.subject,
            tone=tone,
            strategy=result.strategy,
        ),
    )
