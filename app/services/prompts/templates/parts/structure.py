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
- No hallucinations: Absolutely no invented names, dates, numbers, or details beyond the inputs.
- No vague language: All statements are concrete and directly reference the provided facts.
- Natural flow: Sentences are humanized, smooth, and free of robotic transitions or abstract jargon.
- Email is concise (aim for 80-180 words unless urgency requires brevity)."""

ANTI_PATTERNS = """\
Avoid:
- Generic AI phrases ("I hope this email finds you well", "In today's fast-paced world", "Please do not hesitate to contact me, etc.").
- Sales jargon and buzzwords ("synergy", "leverage", "circle back", "touch base", "optimize", "paradigm shift, etc.").
- Bullet dumps that repeat facts without integrating them into prose.
- Rigid, robotic, or abstract sentence structures. Keep sentences natural, active, and human-sounding.
- Vague or ambiguous words (e.g., "things", "stuff", "various aspects", "some issues") — be concrete and specific based on the provided facts."""
