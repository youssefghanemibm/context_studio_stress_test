"""CM-09 (variant c): the modern half of the follow-up commit dated 2026-11-12.

- .github/CODEOWNERS: /services/recovery-svc/ and /services/document-svc/ move to the
  Recoveries & Documents squad (override built in docs.py).
- services/notification-svc: new producer of the fraud-notice "sent" topic (application.yaml
  override plus a new publisher class).  The topic name appears only in the c application.yaml
  (and in the CM-09 commit message), never in another file.
"""
from __future__ import annotations

from services import T, jbase

TOPIC = "notification.fraud-notice.sent.v1"
YAML = "services/notification-svc/src/main/resources/application.yaml"
PUBLISHER = f"{jbase('notification-svc')}/FraudNoticeSentPublisher.java"

PUBLISHER_JAVA = """
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
"""


def build(repo):
    a_text = repo.files[YAML].content
    mods = [
        ("    produces:\n      - notification.sent.v1\n",
         f"    produces:\n      - notification.sent.v1\n      - {TOPIC}\n"),
        ("  holiday-calendars: [UK, NO, SE, DK]\n",
         "  holiday-calendars: [UK, NO, SE, DK]\n"
         "  # CHUB-421: event published once a fraud-referral notice has been sent\n"
         f"  sent-event-topic: {TOPIC}\n"),
    ]
    c_text = a_text
    for before, after in mods:
        assert c_text.count(before) == 1, before
        c_text = c_text.replace(before, after, 1)
    repo.c_overrides[YAML] = c_text
    repo.c_new[PUBLISHER] = T(PUBLISHER_JAVA)
    # CM-09 modifications for history.yaml (before = variant a text, after = variant c text)
    repo.cm09_mods = {YAML: [{"commit": "CM-09", "before": b, "after": a} for b, a in mods]}
    a_own = repo.files[".github/CODEOWNERS"].content
    c_own = repo.c_overrides[".github/CODEOWNERS"]
    own_mods = []
    for la, lc in zip(a_own.splitlines(), c_own.splitlines()):
        if la != lc:
            own_mods.append({"commit": "CM-09", "before": la + "\n", "after": lc + "\n"})
    assert len(own_mods) == 2, own_mods
    repo.cm09_mods[".github/CODEOWNERS"] = own_mods
