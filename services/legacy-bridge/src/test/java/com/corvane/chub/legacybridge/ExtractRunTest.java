package com.corvane.chub.legacybridge;

import static org.assertj.core.api.Assertions.assertThat;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import org.junit.jupiter.api.Test;

class ExtractRunTest {

    private static ExtractRun run(String status) {
        return new ExtractRun(1L, "CLX-IF-042", LocalDateTime.parse("2026-11-02T03:00:00"), 10L,
                BigDecimal.TEN, status, "UK ");
    }

    @Test
    void onlyOkRunsAreCompleted() {
        assertThat(run("OK").completed()).isTrue();
        assertThat(run("ER").completed()).isFalse();
        assertThat(run("RR").completed()).isFalse();
    }
}
