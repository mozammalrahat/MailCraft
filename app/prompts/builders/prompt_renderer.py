"""Render static prompt templates with injected variables."""


def render_prompt(template: str, **variables: str) -> str:
    """Format a template string with keyword variables."""
    return template.format(**variables)
