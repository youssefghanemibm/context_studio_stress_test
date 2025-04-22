package com.corvane.chub.reserve;

import java.util.UUID;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

/**
 * Publishes the reserve change event after every committed reserve movement. The topic is the
 * single entry of {@code chub.kafka.produces}; gl-posting-svc and reporting-feed-svc consume it.
 */
@Component
public class ReserveChangedPublisher {

    private final KafkaTemplate<String, ReserveChanged> kafka;
    private final String topic;

    public ReserveChangedPublisher(KafkaTemplate<String, ReserveChanged> kafka,
                                   ReserveApplication.KafkaTopics topics) {
        this.kafka = kafka;
        this.topic = topics.produces().get(0);
    }

    public void published(Reserve reserve, UUID movementId, String movementType, long amountMinor) {
        kafka.send(topic, reserve.getClaimId(), new ReserveChanged(reserve.getClaimId(), reserve.getReserveId(),
                movementId, movementType, amountMinor, reserve.getCurrency()));
    }

    /** Amounts in minor units (pence / ore), original currency (ADR-016). */
    public record ReserveChanged(String claimId, UUID reserveId, UUID movementId, String movementType,
                                 long amountMinor, String currency) {
    }
}
