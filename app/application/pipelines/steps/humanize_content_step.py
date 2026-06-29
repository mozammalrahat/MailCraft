"""Humanize generated content after formatting."""

from app.application.pipelines.generation_context import GenerationContext
from app.application.services.content_humanization_service import (
    parse_humanized_output,
    resolve_content_type_label,
)
from app.application.services.email_formatting_service import build_clipboard_text
from app.prompts.builders.content_humanizer_prompt_builder import (
    HUMANIZER_PROMPT_VERSION,
    build_content_humanizer_prompt,
)


class HumanizeContentStep:
    """Rewrite AI-generated text to sound more natural and human."""

    async def process(self, context: GenerationContext) -> GenerationContext:
        """Humanize subject and body while preserving factual content."""
        if context.validation_errors or not context.settings.humanize_content_enabled:
            return context

        context.raw_subject = context.subject
        context.raw_body = context.body

        tone_label = context.tone.value if context.tone else "formal"
        if context.generation_kind.value == "application_document" and context.document_metadata:
            tone_label = str(
                context.document_metadata.get("tone_used") or tone_label
            )

        facts_to_preserve = list(context.key_facts)
        if context.intent:
            facts_to_preserve.insert(0, context.intent)

        prompt = build_content_humanizer_prompt(
            subject=context.subject,
            body=context.body,
            content_type_label=resolve_content_type_label(
                context.generation_kind,
                context.document_type,
            ),
            tone_label=tone_label,
            must_preserve_facts=facts_to_preserve or None,
        )

        humanizer_model = (
            context.settings.humanize_model or context.settings.google_model_a
        )
        raw_output = await context.language_model_client.generate_content(
            prompt,
            model=humanizer_model,
        )

        subject, body = parse_humanized_output(raw_output)
        context.subject = subject
        context.body = body
        context.clipboard_text = build_clipboard_text(subject=subject, body=body)
        context.humanization_applied = True
        context.humanizer_prompt_version = HUMANIZER_PROMPT_VERSION
        context.humanizer_model_name = humanizer_model
        return context
