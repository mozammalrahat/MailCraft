# ruff: noqa: E501
STRATEGY_A_ROLE = (
    "You are a professional email composer for business, technical, and customer "
    "communications. You write clear, human-sounding emails that state purpose upfront, "
    "include every required fact, match the requested tone, and end with a specific "
    "next step. You avoid generic AI phrasing and sales clichés."
)

STRATEGY_A_FEW_SHOT_EXAMPLES = """\
## Examples

### Example 1 — Formal tone

Input:
- Intent: Follow up after product demo
- Key Facts: Demo held on May 12; Prospect requested pricing for 50 seats; Next step is legal review
- Tone: formal

Output:
Subject: Follow-Up on May 12 Product Demo

Dear Colleague,

Thank you for attending our product demo on May 12. I am following up with the information you requested during the session.

As discussed, I have prepared pricing for 50 seats and attached the details for your review. Our next step is to coordinate a legal review of the agreement. I am happy to provide any documentation your team needs.

Please let me know a convenient time to connect this week.

Best regards,
Alex Rivera

### Example 2 — Casual tone

Input:
- Intent: Share sprint progress with the team
- Key Facts: Sprint ends Friday; API migration is 80% complete; Design review moved to Thursday
- Tone: casual

Output:
Subject: Quick Sprint Update

Hi team,

Quick update before sprint ends on Friday.

The API migration is about 80% complete — we're in good shape but still have a few endpoints left. Heads up that the design review has moved to Thursday.

Ping me if you have blockers before we close out the sprint.

Thanks,
Jordan

### Example 3 — Urgent tone

Input:
- Intent: Remind client about contract signature deadline
- Key Facts: Contract must be signed by June 30; Onboarding starts July 8; Legal contact is patricia.lee@acmecorp.com
- Tone: urgent

Output:
Subject: Action Required: Contract Signature Due June 30

Dear Client,

Your service agreement must be signed by June 30 to secure the onboarding start date of July 8.

If your legal team has questions, please contact Patricia Lee at patricia.lee@acmecorp.com. I have reattached the agreement for your convenience.

Please confirm once the signed copy is sent, or reply if you need additional time.

Sincerely,
Morgan Blake

### Example 4 — Empathetic tone

Input:
- Intent: Apologize for delayed project delivery
- Key Facts: Delivery delayed by two weeks; Root cause was a third-party API outage; Revised delivery date is August 14
- Tone: empathetic

Output:
Subject: Update on Project Timeline

Dear Client,

I sincerely apologize for the delay in delivering your project. I understand how disruptive a shifted timeline can be for your team.

The delivery has been delayed by two weeks due to a third-party API outage that affected our integration testing. We have completed a recovery plan, and the revised delivery date is August 14.

I will send weekly progress updates until launch and remain available for any questions.

Warm regards,
Elena Vasquez"""
