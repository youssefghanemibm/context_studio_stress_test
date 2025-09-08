package com.corvane.chub.recovery;

import java.math.BigDecimal;
import java.util.Objects;

/**
 * Recovery write-off authority, BR-REC-011 v2 (effective 2025-09-01).
 *
 * <p>A write-off above the approval threshold must be approved by the Head of Recoveries
 * &amp; Subrogation before the recovery case can be closed. Amounts are tested in GBP; Nordic
 * cases use the GBP equivalent held on the recovery case.
 */
public final class WriteOffPolicy {

    /** Write-offs strictly above this amount need approval. */
    public static final BigDecimal APPROVAL_THRESHOLD_GBP = new BigDecimal("10000");

    /** Role that may approve a write-off above the threshold. */
    public static final String APPROVER_ROLE = "HEAD_RECOVERIES_SUBROGATION";

    private WriteOffPolicy() {
    }

    public static boolean requiresApproval(BigDecimal amountGbp) {
        Objects.requireNonNull(amountGbp, "amountGbp");
        return amountGbp.compareTo(APPROVAL_THRESHOLD_GBP) > 0;
    }

    public static boolean mayApprove(BigDecimal amountGbp, String approverRole) {
        return !requiresApproval(amountGbp) || APPROVER_ROLE.equals(approverRole);
    }
}
