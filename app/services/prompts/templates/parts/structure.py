# ruff: noqa: E501
OUTPUT_FORMAT = """\
Output format (follow exactly):
Subject: <clear, specific subject line>

<greeting>,

<opening: 1-2 sentences stating purpose and context>

<body: weave every key fact naturally; use short paragraphs>

<closing: one clear call to action or next step>

<sign-off>
[Your Name]"""

WRITING_FRAMEWORK = """\
Writing framework:
1. Opening — connect to the intent in the first two sentences.
2. Body — include every key fact naturally; do not list facts mechanically unless tone is urgent.
3. Closing — one specific call to action or next step.
4. Sign-off — match the requested tone."""

COMPOSITION_CHECKLIST = """\
Before finalizing, verify:
- Every key fact appears in the body (not only the subject line).
- Tone is consistent in greeting, body, and sign-off.
- Subject line is specific and reflects the intent.
- No invented names, dates, numbers, or details beyond the inputs.
- Email is concise (aim for 80-180 words unless urgency requires brevity)."""

ANTI_PATTERNS = """\
Avoid:
- Generic AI phrases ("I hope this email finds you well", "In today's fast-paced world").
- Sales jargon ("synergy", "leverage", "circle back", "touch base").
- Placeholder brackets in the final output (e.g., [Name]) — use neutral phrasing instead.
- Bullet dumps that repeat facts without integrating them into prose."""
