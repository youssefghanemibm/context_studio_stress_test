package com.corvane.chub.recovery;

import static org.assertj.core.api.Assertions.assertThat;

import java.math.BigDecimal;
import org.junit.jupiter.api.Test;

class WriteOffPolicyTest {

    @Test
    void exactlyTheThresholdDoesNotNeedApproval() {
        assertThat(WriteOffPolicy.requiresApproval(new BigDecimal("10000.00"))).isFalse();
    }

    @Test
    void aboveTheThresholdNeedsTheHeadOfRecoveries() {
        BigDecimal amount = new BigDecimal("10000.01");
        assertThat(WriteOffPolicy.requiresApproval(amount)).isTrue();
        assertThat(WriteOffPolicy.mayApprove(amount, "RECOVERIES_TEAM_LEADER")).isFalse();
        assertThat(WriteOffPolicy.mayApprove(amount, WriteOffPolicy.APPROVER_ROLE)).isTrue();
    }
}
