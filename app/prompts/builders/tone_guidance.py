"""Tone-specific writing guidance for email prompts."""

TONE_GUIDANCE: dict[str, str] = {
    "formal": (
        "Use complete sentences, professional titles where appropriate, and a "
        "respectful sign-off (e.g., Best regards). Avoid slang and contractions. "
        "Open with context, state purpose within the first two sentences, and "
        "close with a clear next step."
    ),
    "casual": (
        "Use a conversational but professional voice. Contractions are fine. "
        "Keep sentences short and scannable. Use first names in greeting and "
        "a friendly sign-off (e.g., Thanks)."
    ),
    "urgent": (
        "Signal urgency in the subject line when appropriate. Lead with the "
        "required action or deadline. Use direct language, short paragraphs, "
        "and an explicit call to action with a specific timeframe."
    ),
    "empathetic": (
        "Acknowledge the situation or feelings first. Take responsibility where "
        "relevant. Offer a concrete next step or solution. Keep the tone sincere "
        "and supportive without being overly casual."
    ),
}


def get_tone_guidance(tone: str) -> str:
    """Return tone guidance text for the given tone name."""
    return TONE_GUIDANCE.get(tone.lower(), TONE_GUIDANCE["formal"])
