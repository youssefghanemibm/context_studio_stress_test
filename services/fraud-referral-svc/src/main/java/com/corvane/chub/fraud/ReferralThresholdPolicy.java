package com.corvane.chub.fraud;

import java.time.LocalDate;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * Sentinel score cut-offs for fraud referral (BR-FRD-031), held as effective-dated
 * configuration rather than code (ADR-020). A claim is referred to SIU when its Sentinel
 * score reaches the threshold that applies on the scoring date. The score alone never
 * declines a claim (BR-FRD-033).
 */
@Component
public class ReferralThresholdPolicy {

    private final int defaultThreshold;
    private final int tier3Threshold;
    private final LocalDate tier3EffectiveFrom;

    public ReferralThresholdPolicy(@Value("${referral.threshold.default}") int defaultThreshold,
                                   @Value("${referral.threshold.tier3}") int tier3Threshold,
                                   @Value("${referral.threshold.tier3.effective-from}") LocalDate tier3EffectiveFrom) {
        this.defaultThreshold = defaultThreshold;
        this.tier3Threshold = tier3Threshold;
        this.tier3EffectiveFrom = tier3EffectiveFrom;
    }

    /** Threshold for a claim of the given tier scored on the given date. */
    public int thresholdFor(int tier, LocalDate scoredOn) {
        if (tier == 3 && !scoredOn.isBefore(tier3EffectiveFrom)) {
            return tier3Threshold;
        }
        return defaultThreshold;
    }

    public boolean shouldRefer(int sentinelScore, int tier, LocalDate scoredOn) {
        return sentinelScore >= thresholdFor(tier, scoredOn);
    }
}
