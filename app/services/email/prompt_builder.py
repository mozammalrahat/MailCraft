from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.schemas.email import EmailGenerationRequest

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"
PROMPT_VERSION = "1.0.0"

SUPPORTED_STRATEGIES = frozenset({"strategy_a", "strategy_b"})

_jinja_env = Environment(
    loader=FileSystemLoader(PROMPTS_DIR),
    autoescape=select_autoescape(default=False),
    trim_blocks=True,
    lstrip_blocks=True,
)


def build_prompt(request: EmailGenerationRequest, strategy: str = "strategy_a") -> str:
    if strategy not in SUPPORTED_STRATEGIES:
        msg = f"Unsupported strategy: {strategy}"
        raise ValueError(msg)

    template_name = f"{strategy}.jinja"
    template = _jinja_env.get_template(template_name)
    return template.render(
        intent=request.intent,
        key_facts=request.key_facts,
        tone=request.tone,
    )


def get_prompt_version() -> str:
    return PROMPT_VERSION
