STRATEGY_A_TEMPLATE = """\
{role}

{few_shot_examples}

## Your Task

Write one professional email using the inputs below.

### Inputs
- Intent: {intent}
- Key Facts (every fact must appear in the body):
{key_facts}
- Tone: {tone}

### Tone guidance
{tone_guidance}

{writing_framework}

{output_format}

### Rules
1. Include every key fact naturally in the email body.
2. Match the requested tone throughout.
3. Do not invent facts beyond the inputs.
4. State the purpose within the first two sentences.

{anti_patterns}

{composition_checklist}"""
