package com.corvane.chub.fraud;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.LocalDate;
import org.junit.jupiter.api.Test;

class ReferralThresholdPolicyTest {

    private final ReferralThresholdPolicy policy =
            new ReferralThresholdPolicy(65, 60, LocalDate.parse("2026-10-01"));

    @Test
    void tier3ClaimsUseTheLowerThresholdFromTheEffectiveDate() {
        assertThat(policy.thresholdFor(3, LocalDate.parse("2026-10-01"))).isEqualTo(60);
        assertThat(policy.shouldRefer(61, 3, LocalDate.parse("2026-10-02"))).isTrue();
    }

    @Test
    void tier3ClaimsScoredBeforeTheEffectiveDateKeepTheDefault() {
        assertThat(policy.thresholdFor(3, LocalDate.parse("2026-09-30"))).isEqualTo(65);
    }

    @Test
    void otherTiersAlwaysUseTheDefault() {
        assertThat(policy.shouldRefer(64, 2, LocalDate.parse("2026-11-02"))).isFalse();
        assertThat(policy.shouldRefer(65, 1, LocalDate.parse("2026-11-02"))).isTrue();
    }
}
