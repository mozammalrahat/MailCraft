import re

_SUBJECT_LINE_PATTERN = re.compile(
    r"^Subject:\s*(.+?)(?:\n+|$)",
    re.IGNORECASE | re.MULTILINE,
)
_SUBJECT_STRIP_PATTERN = re.compile(
    r"^Subject:\s*.+?\n+",
    re.IGNORECASE | re.MULTILINE,
)
_GREETING_PATTERN = re.compile(
    r"^(Dear [^,\n]+,\s*|Hi [^,\n]+,\s*|Hello [^,\n]+,\s*|Hey [^,\n]+,\s*)",
    re.IGNORECASE,
)
_SIGN_OFF_PATTERN = re.compile(
    r"\s+(Best regards|Kind regards|Warm regards|Yours sincerely|Sincerely|"
    r"Respectfully|Regards|Thanks|Thank you),?\s*(.*)$",
    re.IGNORECASE | re.DOTALL,
)
_SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")

BODY_FORMAT_INSTRUCTIONS = """\
Body formatting (required):
- Put the subject ONLY in the subject field, not in the body.
- Use blank lines between sections in the body (\\n\\n in JSON).
- Structure: greeting, opening paragraph, 1-3 body paragraphs, closing, sign-off.
- Never output the entire email as one long line."""


def resolve_subject_and_body(
    body: str,
    subject: str | None,
) -> tuple[str | None, str]:
    cleaned_body = body.strip()
    resolved_subject = subject.strip() if subject and subject.strip() else None

    if resolved_subject is None:
        match = _SUBJECT_LINE_PATTERN.search(cleaned_body)
        if match:
            resolved_subject = match.group(1).strip()

    cleaned_body = _strip_subject_line(cleaned_body, resolved_subject)
    return resolved_subject, cleaned_body


def format_document_body(body: str) -> str:
    text = body.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return text

    if "\n\n" in text:
        return _normalize_paragraphs(text)

    if "\n" in text:
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return "\n\n".join(lines)

    return _format_single_line_body(text)


def build_clipboard_text(*, subject: str | None, body: str) -> str:
    formatted_body = format_document_body(body)
    if subject and subject.strip():
        return f"Subject: {subject.strip()}\n\n{formatted_body}"
    return formatted_body


def _strip_subject_line(body: str, subject: str | None) -> str:
    text = _SUBJECT_STRIP_PATTERN.sub("", body.strip(), count=1)
    if subject:
        specific = re.compile(
            rf"^Subject:\s*{re.escape(subject.strip())}\s*\n+",
            re.IGNORECASE | re.MULTILINE,
        )
        text = specific.sub("", text.strip(), count=1)
    return text.strip()


def _normalize_paragraphs(text: str) -> str:
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    return "\n\n".join(paragraphs)


def _format_single_line_body(text: str) -> str:
    sign_off_match = _SIGN_OFF_PATTERN.search(text)
    sign_off_block = ""
    if sign_off_match:
        phrase = sign_off_match.group(1).strip().rstrip(",")
        name = sign_off_match.group(2).strip()
        sign_off_block = f"{phrase},\n{name}" if name else f"{phrase},"
        text = text[: sign_off_match.start()].strip()

    greeting_match = _GREETING_PATTERN.match(text)
    greeting = ""
    if greeting_match:
        greeting = greeting_match.group(1).strip()
        text = text[greeting_match.end() :].strip()

    parts: list[str] = []
    if greeting:
        parts.append(greeting)
    parts.extend(_split_sentences_into_paragraphs(text))
    if sign_off_block:
        parts.append(sign_off_block)

    return "\n\n".join(parts)


def _split_sentences_into_paragraphs(text: str) -> list[str]:
    if not text:
        return []

    sentences = [
        sentence.strip()
        for sentence in _SENTENCE_SPLIT_PATTERN.split(text)
        if sentence.strip()
    ]
    if not sentences:
        return [text]

    if len(sentences) <= 2:
        return [" ".join(sentences)]

    paragraphs: list[str] = []
    index = 0
    while index < len(sentences):
        remaining = len(sentences) - index
        chunk_size = 2 if remaining > 2 else remaining
        paragraphs.append(" ".join(sentences[index : index + chunk_size]))
        index += chunk_size

    return paragraphs
