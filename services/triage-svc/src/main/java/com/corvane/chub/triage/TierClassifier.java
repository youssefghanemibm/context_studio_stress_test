package com.corvane.chub.triage;

import java.math.BigDecimal;
import java.util.Map;
import org.springframework.stereotype.Component;

/**
 * Claim tier classification, BR-TRI-003 v3 (approved 2024-11-26, effective 2025-01-01).
 *
 * <p>Tier-3 if any trigger applies: estimated incurred at or above the currency threshold,
 * any bodily injury, solicitor or litigation involvement at notification, or a property
 * total loss. Tier-2 covers incurred from the GBP Tier-2 floor or any third-party
 * involvement. Everything else is Tier-1.
 *
 * <p>Tiering is owned by triage-svc (ADR-030); other services call the triage API rather
 * than re-implementing these constants.
 */
@Component
public class TierClassifier {

    // --- BR-TRI-003 v3 thresholds -------------------------------------------------------
    static final BigDecimal TIER3_MIN_GBP = new BigDecimal("50000");
    static final BigDecimal TIER3_MIN_NOK = new BigDecimal("650000");
    static final BigDecimal TIER3_MIN_SEK = new BigDecimal("680000");
    static final BigDecimal TIER3_MIN_DKK = new BigDecimal("430000");
    static final BigDecimal TIER2_MIN_GBP = new BigDecimal("5000");

    private static final Map<String, BigDecimal> TIER3_MIN = Map.of(
            "GBP", TIER3_MIN_GBP,
            "NOK", TIER3_MIN_NOK,
            "SEK", TIER3_MIN_SEK,
            "DKK", TIER3_MIN_DKK);

    public Tier classify(TriageInput in) {
        BigDecimal floor = TIER3_MIN.get(in.currency());
        if (floor == null) {
            throw new IllegalArgumentException("Unsupported claim currency " + in.currency());
        }
        if (in.estimatedIncurred().compareTo(floor) >= 0
                || in.bodilyInjury()
                || in.litigationAtNotification()
                || in.propertyTotalLoss()) {
            return Tier.TIER_3;
        }
        if (in.estimatedIncurredGbp().compareTo(TIER2_MIN_GBP) >= 0 || in.thirdPartyInvolved()) {
            return Tier.TIER_2;
        }
        return Tier.TIER_1;
    }

    public enum Tier { TIER_1, TIER_2, TIER_3 }

    public record TriageInput(String claimId,
                              String currency,
                              BigDecimal estimatedIncurred,
                              BigDecimal estimatedIncurredGbp,
                              boolean bodilyInjury,
                              boolean litigationAtNotification,
                              boolean propertyTotalLoss,
                              boolean thirdPartyInvolved) {
    }
}
