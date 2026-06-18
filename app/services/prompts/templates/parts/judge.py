# ruff: noqa: E501
TONE_JUDGE_RUBRIC = """\
Score each dimension from 1-5, then give an overall tone score.

Tone rubric:
- formal: professional language, structured greeting/sign-off, no slang, purpose stated early
- casual: conversational, friendly, relaxed phrasing, still professional
- urgent: clear time sensitivity, direct call to action, priority language, action upfront
- empathetic: acknowledges feelings or situation, sincere tone, supportive language

Scoring guide:
5 = tone is consistent and appropriate throughout
3 = mostly correct tone with minor mismatches
1 = tone clearly wrong or inconsistent"""

QUALITY_JUDGE_RUBRIC = """\
Score each dimension from 1-5:
- GRAMMAR: correctness, spelling, and sentence fluency
- CLARITY: easy to understand, logical flow, no ambiguity
- OPENING: purpose stated clearly in the first two sentences; professional greeting

Scoring guide:
5 = excellent, production-ready
3 = acceptable with minor issues
1 = significant problems"""
