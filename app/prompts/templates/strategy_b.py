STRATEGY_B_TEMPLATE = """\
Write a professional email based on the following inputs.

Intent: {intent}

Key Facts (must all appear in the email body):
{key_facts}

Tone: {tone}
Tone note: {tone_guidance}

{output_format}

Rules:
1. Include every key fact naturally in the email body.
2. Match the requested tone throughout.
3. No hallucinations: Do not invent facts, names, dates, or details beyond inputs.
4. No vague language: Be concrete and specific; avoid words like "things", "stuff", or
   "various aspects".
5. Humanized flow: Avoid rigid or robotic structures; keep phrasing natural and active.
"""
