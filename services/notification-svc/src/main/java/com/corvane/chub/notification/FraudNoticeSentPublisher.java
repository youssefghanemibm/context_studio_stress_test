package com.corvane.chub.notification;

import java.time.Instant;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

/**
 * Publishes an event when a fraud-referral customer notice has actually been sent, so that
 * fraud-referral-svc can close the notice deadline it opened (CHUB-421). The topic name is
 * configured in {@code notice.sent-event-topic}.
 */
@Component
public class FraudNoticeSentPublisher {

    private final KafkaTemplate<String, FraudNoticeSent> kafka;
    private final String topic;

    public FraudNoticeSentPublisher(KafkaTemplate<String, FraudNoticeSent> kafka,
                                    @Value("${notice.sent-event-topic}") String topic) {
        this.kafka = kafka;
        this.topic = topic;
    }

    public void published(String referralId, String claimId, String channel, String notifyMessageId, Instant sentAt) {
        kafka.send(topic, claimId, new FraudNoticeSent(referralId, claimId, channel, notifyMessageId, sentAt));
    }

    public record FraudNoticeSent(String referralId, String claimId, String channel, String notifyMessageId,
                                  Instant sentAt) {
    }
}
