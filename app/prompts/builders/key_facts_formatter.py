"""Format key facts for inclusion in prompts."""


def format_key_facts_bulleted(key_facts: list[str], indent: str = "") -> str:
    """Return key facts as a bulleted list."""
    return "\n".join(f"{indent}- {fact}" for fact in key_facts)
