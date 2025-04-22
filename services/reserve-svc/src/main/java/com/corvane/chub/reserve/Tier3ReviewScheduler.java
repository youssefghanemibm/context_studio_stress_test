package com.corvane.chub.reserve;

import java.time.Clock;
import java.time.LocalDate;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

/**
 * Keeps reserve.review_schedule up to date for Tier-3 claims (BR-RSV-007). The cadence comes
 * from {@code reserve.tier3-review-days}; CLARA's CLRRS110 reads the same value from
 * CLR.T_PARAM (RSV_T3_REVIEW_DAYS), so both must be changed together.
 */
@Component
public class Tier3ReviewScheduler {

    private final ReviewScheduleRepository schedule;
    private final Clock clock;
    private final int cadenceDays;

    public Tier3ReviewScheduler(ReviewScheduleRepository schedule, Clock clock,
                                @Value("${reserve.tier3-review-days}") int cadenceDays) {
        this.schedule = schedule;
        this.clock = clock;
        this.cadenceDays = cadenceDays;
    }

    @KafkaListener(topics = "triage.completed.v1", groupId = "reserve-svc-review")
    public void onTriage(TriageCompleted event) {
        if (event.tier() == 3) {
            LocalDate next = LocalDate.now(clock).plusDays(cadenceDays);
            schedule.upsert(event.claimId(), next, cadenceDays);
        }
    }

    public record TriageCompleted(String claimId, int tier) {
    }
}
