def format_key_facts_bulleted(key_facts: list[str], indent: str = "") -> str:
    return "\n".join(f"{indent}- {fact}" for fact in key_facts)
