# Post-mortem – INC-2026-0518

**Batch fraud sweep used pre-2026 referral threshold**

| | |
|---|---|
| **Incident** | INC-2026-0518 |
| **Severity** | Sev2 |
| **Detected** | 12 May 2026, 10:00 |
| **Mitigated** | 13 May 2026, 16:00 |
| **Systems** | CLARA – CLRFR040 (batch fraud sweep) |
| **Incident owner** | Niall Brannigan, Head of Counter-Fraud & SIU |
| **Review date** | 20 May 2026 |
| **Status** | Final |

## Review participants

- Niall Brannigan, Head of Counter-Fraud & SIU
- Ruth Okafor, Compliance Manager – Conduct & Counter-Fraud
- Graham Pocock, Head of Legacy Claims Platforms
- Keith Barraclough, Senior Mainframe Developer
- Pauline Ashworth, Mainframe Developer
- Rachel Dunmore, SIU Investigations Manager (UK)
- Oskar Lindgren, Senior Fraud Analyst

## Summary

On 12 May 2026 Compliance sampling found that the CLARA batch fraud sweep had not referred claims
scoring 65 to 69 since the referral threshold changed to 65 on 1 April 2026 under BR-FRD-031 v1. The
online referral path was not affected.

## Impact

37 claims scored 65–69 between 1 April and 12 May 2026 were not referred by the batch path. All 37
were referred to SIU manually on 13 May 2026. No customer outcome is known to have been affected;
SIU triage of the 37 referrals is tracked separately.

## Timeline

- 12 May 2026 10:00 – Compliance sampling identifies unreferred claims scoring 65–69.
- 12 May 2026, late morning – Ruth Okafor reports the gap; incident logged as Sev2 with Niall
  Brannigan as owner.
- 12 May 2026, afternoon – Legacy Claims Platforms begins analysis of CLRFR040.
- 13 May 2026 – the 37 claims are referred to SIU manually; CHUB-298 raised for the permanent fix.
- 13 May 2026 16:00 – incident mitigated; daily Compliance query in place.

## Root cause

CLRFR040 still carried the old referral threshold of 70 as a hard-coded working-storage value
instead of reading it from CLR.T_PARAM. The online program, CLRFR030, reads the parameter and
referred correctly at 65.

## Contributing factors

- The review asked why the batch path was not caught in testing of the April change; the team will
  look at regression coverage for parameter-driven rules in both online and batch programs.
- Sampling by Compliance found the issue; there was no automated reconciliation of batch referrals
  against scores at the time.

## Regulatory considerations

Ruth Okafor confirmed that customer notices for the 37 referred claims follow the normal BR-FRD-032
v2 process – written notice within 10 business days of referral unless a deferral is certified – and
that Compliance will keep the incident record with the Circular 2026/04 implementation evidence.

## What went well

- Compliance sampling detected the gap and the incident was raised the same morning.
- SIU referred all affected claims the next day.

## Actions

Workaround (in place): Compliance runs a daily query for unreferred claims scoring 65–69 until the
permanent fix is released.

| # | Action | Owner | Due | Status |
|---|---|---|---|---|
| PM-1 | Permanent fix to CLRFR040 (CHUB-298) | Keith Barraclough | To be scheduled | Open |
| PM-2 | Run the daily Compliance query until the fix is released | Ruth Okafor | Daily | In place |
| PM-3 | Review regression coverage for parameter-driven fraud rules | Graham Pocock | 19 Jun 2026 | Open |
| PM-4 | Check other CLARA batch programs for hard-coded rule parameters | Pauline Ashworth | 19 Jun 2026 | Open |

## Lessons

Parameter-driven rules must be tested on every path that applies them. Where a rule exists in both
CLARA and Claims Hub during migration, both implementations need to be in scope of any change.

## Appendix – rule versions involved

- **BR-FRD-031 v1** – Fraud referral threshold (NISA Circular 2026/04)
  Text: Refer a claim to SIU when the Sentinel score is 65 or more (all tiers).
  Status: approved 12 March 2026 by Niall Brannigan, Ingrid Ashby; effective from 1 April 2026.
- **BR-FRD-012 v2** – Fraud referral threshold (pre-2026)
  Text: Refer a claim to SIU when the FRAUDNET/Sentinel score is 70 or more.
  Status: approved 9 March 2023 by Niall Brannigan; effective from 1 April 2023; effective to 31
  March 2026.

## Distribution

- Niall Brannigan (Head of Counter-Fraud & SIU)
- Ruth Okafor (Compliance Manager – Conduct & Counter-Fraud)
- Graham Pocock (Head of Legacy Claims Platforms)
- Keith Barraclough (Senior Mainframe Developer)
- Pauline Ashworth (Mainframe Developer)
- Rachel Dunmore (SIU Investigations Manager (UK))
- Oskar Lindgren (Senior Fraud Analyst)
- Karin Holmberg (Chief Risk Officer)
