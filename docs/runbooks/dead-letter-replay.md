# Dead-letter replay

1. List the dead-letter records and group them by error.
2. Fix the cause first: schema mismatch, missing reference data or a downstream outage.
3. Replay in small batches and watch the consumer error rate.
4. Record the replay in the incident ticket.
