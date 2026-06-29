JUDGE_QUALITY_TEMPLATE = """\
You are evaluating the professional quality of a business email.

{quality_rubric}

Email:
{generated_email}

Respond exactly as:
GRAMMAR: <1-5>
CLARITY: <1-5>
OPENING: <1-5>"""
