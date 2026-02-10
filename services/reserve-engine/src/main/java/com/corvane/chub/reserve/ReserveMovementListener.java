package com.corvane.chub.reserve;

import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

/**
 * Consumes CLARA reserve movements republished by the MQ-to-Kafka bridge CLX-IF-049
 * (ADR-012): RSVMOVE records from CLX-IF-042, converted to Avro (schema v3) and keyed by
 * claim_id. Used for the reserve parallel run and for Wave 2 synchronisation.
 */
@Component
public class ReserveMovementListener {

    private final ReserveMovementService movements;

    public ReserveMovementListener(ReserveMovementService movements) {
        this.movements = movements;
    }

    @KafkaListener(topics = "claims.reserve.movement.v1", groupId = "reserve-engine-sync")
    public void onClaraMovement(ClaraReserveMovement movement) {
        movements.applyFromClara(movement);
    }

    public record ClaraReserveMovement(String claimId, String movementType, long amountMinor,
                                       String currency, int recVersion) {
    }
}
