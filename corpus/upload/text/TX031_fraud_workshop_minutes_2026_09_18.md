# Minutes – Fraud Rules Workshop

*Claims Fraud Forum – extended workshop session. Classification: Internal.*

| | |
|---|---|
| **Meeting** | Fraud Rules Workshop (Claims Fraud Forum) |
| **Date** | Thursday 17 September 2026 |
| **Time** | 09:30–11:30 |
| **Location** | Room 2.14, Corvane House, in person and on video |
| **Chair** | Niall Brannigan, Head of Counter-Fraud & SIU |
| **Minutes** | Hannah Lyle, Business Analyst – Claims (IBM Consulting) |
| **Status** | Final – approved by the chair on 18 September 2026 |

## Document control

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 17 Sep 2026 | Hannah Lyle | First draft from workshop notes and the recording |
| 0.2 | 18 Sep 2026 | Niall Brannigan | Chair review – wording of decisions D1 and D2 |
| 1.0 | 18 Sep 2026 | Hannah Lyle | Final for circulation |

## Attendees

| Name | Role | Organisation |
|---|---|---|
| Niall Brannigan | Head of Counter-Fraud & SIU (Chair) | Corvane Mutual |
| Ingrid Ashby | Claims Director | Corvane Mutual |
| Oskar Lindgren | Senior Fraud Analyst | Corvane Mutual |
| Rachel Dunmore | SIU Investigations Manager (UK) | Corvane Mutual |
| Ruth Okafor | Compliance Manager – Conduct & Counter-Fraud | Corvane Mutual |
| Linnea Sjöberg | Engineering Lead – Fraud & Settlement Squad | Corvane Mutual |
| Hannah Lyle | Business Analyst – Claims (minutes) | IBM Consulting |
| Aisha Siddiqui | Head of Claims Hub Product | Corvane Mutual |

## Apologies

- Rob Tennant, Head of Claims Operations (Group)

## Agenda

1. Welcome, apologies and previous actions
2. Circular 2026/04: six months of operation
3. Referral threshold for Tier-3 claims
4. Approval of customer-notice deferrals
5. Option: a single lower threshold for all claims
6. Implementation, communications and documentation
7. Any other business

## 1. Welcome, apologies and previous actions

The chair opened the meeting, welcomed attendees and confirmed quorum. Attendees confirmed they had no interests to declare against the agenda. Apologies were received from Rob Tennant.

The minutes of the previous meeting were accepted as an accurate record. The action log was reviewed. Closed items have been removed; carried-forward items are listed below.

## 2. Circular 2026/04: six months of operation

Ruth Okafor summarised how the fraud rule set has operated since NISA Circular 2026/04 took effect on 1 April 2026. Under BR-FRD-031 v1 every claim with a Sentinel score of 65 or more is referred to SIU, in line with paragraph 3.3 of the Circular, which says a score-based cut-off on the 0–100 scale must not exceed 65.

The first NISA-FR1 return (Q2 2026) went to NISA on 29 July 2026, ahead of the 30 July deadline; the Q3 return is due by 30 October 2026.

Ruth also reminded the group that the batch-sweep problem found in May (INC-2026-0518) is still covered by the daily Compliance query; the permanent fix for CLRFR040 is tracked as CHUB-298, which remains open.

Discussion covered the following:

- Attendees agreed that any residual questions should be raised through the usual channel rather than reopened here.
- It was noted that the outcome should be recorded in the programme decision log.

## 3. Referral threshold for Tier-3 claims

Oskar Lindgren presented an analysis of Sentinel scores (model SNT-4.2, calibrated on 16 March 2026) for claims that meet the Tier-3 definition in BR-TRI-003 v3. The analysis concentrated on Tier-3 claims scoring between 60 and 64, which are not referred under the current rule.

Points raised in discussion:

- Ruth Okafor confirmed that a Tier-3 threshold below 65 is consistent with paragraph 3.3 of the Circular, which sets a maximum cut-off rather than a minimum.
- Rachel Dunmore asked that the effect on SIU workload is monitored against the 3-business-day triage standard in BR-FRD-035 v2.
- Linnea Sjöberg confirmed that fraud-referral-svc and triage-svc can apply a separate threshold for Tier-3 claims, and that configuration can be ready for 1 October.
- Aisha Siddiqui asked how claims still on CLARA would be covered. CLRFR030 (online) and CLRFR040 (batch) both apply the referral rule; because CHUB-298 is open, the daily Compliance query will be extended to Tier-3 claims scoring 60–64 from 1 October.
- Ingrid Ashby supported the proposal and noted that the Claims Handling Manual v7.2, approved on 30 June 2026, states 65 for all claims and therefore predates this decision.

The outcome is recorded as decision D1 below.

## 4. Approval of customer-notice deferrals

Rachel Dunmore described how deferrals of the customer notice (BR-FRD-036) have been used since April where SIU certifies a tipping-off risk. Without a deferral, the customer must be told in writing within 10 business days of the referral that the claim is subject to additional checks (BR-FRD-032 v2). Deferrals remain capped at 60 days.

Members agreed that long deferrals warrant more senior sign-off and that Compliance should know about them on the day they are approved. The outcome is recorded as decision D2.

## 5. Option: a single lower threshold for all claims

The workshop considered lowering the general referral threshold to 60 for all claims. Oskar Lindgren presented an estimate of the additional referral volume; the figure is in the analysis pack and the workshop recording and is not repeated here.

Members concluded that the targeted Tier-3 change addresses the risk identified, and the option was not taken forward (decision D3).

## 6. Implementation, communications and documentation

- BR-FRD-031 v2 and BR-FRD-036 v2 were approved at the workshop by Niall Brannigan and Ingrid Ashby, effective 1 October 2026.
- The fraud-referral BRD will be updated to reflect both rule versions.
- A change request will be raised so the next revision of the Claims Handling Manual reflects the Tier-3 threshold and the deferral approval.
- SIU, Major & Complex Loss and the claims handling teams will be briefed before 1 October.

In discussion the following points were made:

- The group noted the dependency on testing being completed and signed off before the change goes live.
- It was agreed that training material for handlers would be updated alongside the system change.

## 7. Any other business

No other business was raised.

The meeting closed at 11:30.

## Decisions

D1 (DEC-014) – From 1 October 2026, Tier-3 claims (BR-TRI-003) are referred to SIU at a Sentinel score of 60 or more; the general referral threshold stays at 65 (BR-FRD-031 v2). Decided by Niall Brannigan and Ingrid Ashby.

D2 (DEC-015) – From 1 October 2026, customer-notice deferrals beyond 30 days need the approval of the Head of Counter-Fraud & SIU, and Compliance is notified the same day (BR-FRD-036 v2).

D3 (DEC-016) – The option to lower the general referral threshold to 60 for all claims was rejected.

## Actions

| # | Action | Owner | Due | Status |
|---|---|---|---|---|
| A1 | Configure the Tier-3 threshold of 60 in fraud-referral-svc and triage-svc for 1 October | Linnea Sjöberg | 30 Sep 2026 | Open |
| A2 | Extend the daily Compliance query to Tier-3 claims scoring 60–64 from 1 October | Ruth Okafor | 1 Oct 2026 | Open |
| A3 | Update the fraud-referral BRD for BR-FRD-031 v2 and BR-FRD-036 v2 | Hannah Lyle | 25 Sep 2026 | Open |
| A4 | Brief SIU investigators on the Tier-3 threshold and the deferral approval change | Rachel Dunmore | 30 Sep 2026 | Open |
| A5 | Raise the manual change request for the next revision | Ingrid Ashby | 16 Oct 2026 | Open |
| A6 | Confirm with Legacy Claims Platforms how the Tier-3 threshold is applied in CLARA while CHUB-298 is open | Aisha Siddiqui | 25 Sep 2026 | Open |

## Papers

1. Sentinel SNT-4.2 – Tier-3 score analysis (Oskar Lindgren)
2. Customer-notice deferrals since April 2026 – SIU summary (Rachel Dunmore)
3. Circular 2026/04 compliance status – September 2026 (Ruth Okafor)
4. Option paper: single lower referral threshold (Oskar Lindgren)

## Appendix A – rule text referred to in these minutes

- **BR-FRD-031 v2** – Fraud referral threshold (NISA Circular 2026/04)
  Text: Refer a claim to SIU when the Sentinel score is 65 or more; for Tier-3 claims (BR-TRI-003) refer at a Sentinel score of 60 or more.
  Status: approved 17 September 2026 by Niall Brannigan, Ingrid Ashby; effective from 1 October 2026.
- **BR-FRD-036 v2** – Deferral of customer notice (tipping-off risk)
  Text: The customer notice may be deferred for up to 60 days where SIU certifies a tipping-off risk; deferrals beyond 30 days require the Head of Counter-Fraud & SIU and Compliance must be notified the same day.
  Status: approved 17 September 2026 by Niall Brannigan, Ingrid Ashby; effective from 1 October 2026.
- **BR-TRI-003 v3** – Claim tier classification (Tier-1 / Tier-2 / Tier-3)
  Text: A claim is Tier-3 if any of: estimated incurred ≥ £50,000 (NOK 650,000 / SEK 680,000 / DKK 430,000); any bodily injury; solicitor or litigation involvement at notification; property total loss. Tier-2: £5,000–£49,999 or any third-party involvement. Tier-1: below £5,000, no injury, no third party.
  Status: approved 26 November 2024 by Ingrid Sørensen; effective from 1 January 2025.
- **BR-FRD-032 v2** – Customer notification of fraud referral
  Text: Notify the customer in writing within 10 business days of a fraud referral that the claim is subject to additional checks, unless the notice is deferred under BR-FRD-036.
  Status: approved 12 March 2026 by Niall Brannigan, Ingrid Ashby; effective from 1 April 2026.
- **BR-FRD-035 v2** – SIU triage of new referrals
  Text: SIU must triage a new referral within 3 business days.
  Status: approved 12 March 2026 by Niall Brannigan; effective from 1 April 2026.

## Abbreviations

| Term | Meaning |
|---|---|
| SIU | Special Investigations Unit (Counter-Fraud & SIU from 1 September 2025) |
| FR1 | NISA-FR1 Quarterly Fraud Referral Return |
| NISA | National Insurance Supervisory Authority |
| BRD | Business Requirements Document |
| SNT-4.2 | Current Sentinel scoring model version |
| Tier-3 | Claim tier defined by BR-TRI-003 |
| CLARA | Claims Ledger And Reserve Application (legacy mainframe claims system) |
| CHUB | Jira project key for Claims Hub |

## Distribution

- Niall Brannigan (Head of Counter-Fraud & SIU)
- Ingrid Ashby (Claims Director)
- Oskar Lindgren (Senior Fraud Analyst)
- Rachel Dunmore (SIU Investigations Manager (UK))
- Ruth Okafor (Compliance Manager – Conduct & Counter-Fraud)
- Linnea Sjöberg (Engineering Lead – Fraud & Settlement Squad)
- Hannah Lyle (Business Analyst – Claims)
- Aisha Siddiqui (Head of Claims Hub Product)
- Rob Tennant (Head of Claims Operations (Group))
- Programme Skerry decision log (PMO)

*Minutes prepared by Hannah Lyle. Approved by Niall Brannigan, chair.*
