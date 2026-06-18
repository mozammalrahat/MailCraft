JUDGE_TONE_TEMPLATE = """\
You are evaluating whether a generated business email matches the requested tone.

Requested tone: {tone}

{tone_rubric}

Generated email:
{generated_email}

Respond in this exact format:
SCORE: <integer 1-5>
JUSTIFICATION: <one sentence explaining the score>"""
