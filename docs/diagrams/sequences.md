# Sequence diagrams

## Reserve movement synchronisation (CLARA to Claims Hub)

```mermaid
sequenceDiagram
    participant RS as CLARA CLRRS170
    participant MQ as MQ queue CLR.RSVMOVE.OUT
    participant BR as Bridge CLX-IF-049
    participant K as Kafka claims.reserve.movement.v1
    participant RE as reserve-engine
    participant GL as gl-posting-svc
    participant LED as Group Ledger
    RS->>MQ: MQPUT RSVMOVE records (CLX-IF-042)
    RS->>RS: set EXTRACTED_FLAG = 'Y' on CLR.T_RESERVE_MOVEMENT
    BR->>MQ: daily 02:45 read RSVMOVE records
    BR->>K: publish Avro schema v3, key claim_id
    K->>RE: consume for parallel run and Wave 2 sync
    RE->>GL: reserve.changed.v2
    GL->>LED: journals posted hourly (CLX-IF-050)
```

## Fraud referral and customer notice

```mermaid
sequenceDiagram
    participant TR as triage-svc
    participant SN as Sentinel
    participant FR as fraud-referral-svc
    participant SIU as SIU Case Manager
    participant NS as notification-svc
    participant NT as Notify
    TR->>SN: score claim over REST, timeout 800 ms (CLX-IF-036)
    SN-->>TR: Sentinel score
    TR->>FR: fraud.score.received.v1
    FR->>FR: refer if score >= 65; Tier-3 claims >= 60 from 2026-10-01
    FR->>SIU: create SIU referral (CLX-IF-041)
    FR->>NS: fraud.referral.notice-due.v1
    NS->>NS: due date = referral date + 10 business days
    NS->>NT: send notice FRN01 (letter) or FRN02 (SMS)
```
