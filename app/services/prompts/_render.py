def render_prompt(template: str, **variables: str) -> str:
    return template.format(**variables)
