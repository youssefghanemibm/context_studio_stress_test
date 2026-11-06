# Reserve movement bridge (CLX-IF-049)

1. The bridge reads RSVMOVE records from MQ queue CLR.RSVMOVE.OUT daily at 02:45 and publishes them to `claims.reserve.movement.v1`.
2. If the CLARA extract (CLX-IF-042) is late, the bridge finds an empty queue; rerun it once the extract completes.
3. Messages are keyed by claim_id and use Avro schema v3.
