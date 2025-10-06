package com.corvane.chub.triage;

import static org.assertj.core.api.Assertions.assertThat;

import java.math.BigDecimal;
import org.junit.jupiter.api.Test;

class TierClassifierTest {

    private final TierClassifier classifier = new TierClassifier();

    private static TierClassifier.TriageInput input(String ccy, String amount, String gbp) {
        return new TierClassifier.TriageInput("CLM-TEST-0001", ccy, new BigDecimal(amount), new BigDecimal(gbp),
                false, false, false, false);
    }

    @Test
    void gbpClaimAtTheTier3FloorIsTier3() {
        assertThat(classifier.classify(input("GBP", "50000", "50000"))).isEqualTo(TierClassifier.Tier.TIER_3);
    }

    @Test
    void gbpClaimJustBelowTheFloorIsTier2() {
        assertThat(classifier.classify(input("GBP", "49999", "49999"))).isEqualTo(TierClassifier.Tier.TIER_2);
    }

    @Test
    void nordicThresholdsAreInLocalCurrency() {
        assertThat(classifier.classify(input("NOK", "650000", "48000"))).isEqualTo(TierClassifier.Tier.TIER_3);
        assertThat(classifier.classify(input("SEK", "679999", "49000"))).isEqualTo(TierClassifier.Tier.TIER_2);
        assertThat(classifier.classify(input("DKK", "430000", "49500"))).isEqualTo(TierClassifier.Tier.TIER_3);
    }

    @Test
    void smallClaimWithoutTriggersIsTier1() {
        assertThat(classifier.classify(input("GBP", "1200", "1200"))).isEqualTo(TierClassifier.Tier.TIER_1);
    }
}
