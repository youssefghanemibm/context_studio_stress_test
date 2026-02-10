package com.corvane.chub.reserve;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.UUID;

/**
 * JPA mapping of reserve.reserve in database chub_reserve (owned by reserve-engine, ADR-003).
 */
@Entity
@Table(schema = "reserve", name = "reserve")
public class Reserve {

    /** Reserve. */
    @Id
    @Column(name = "reserve_id", nullable = false)
    private UUID reserveId;

    /** Claim. */
    @Column(name = "claim_id", nullable = false, length = 20)
    private String claimId;

    /** Indemnity, expense, legal. */
    @Column(name = "reserve_type", nullable = false, length = 10)
    private String reserveType;

    /** Currency. */
    @Column(name = "currency", nullable = false, length = 3)
    private String currency;

    /** Outstanding (maps from RSV_OUTSTANDING_AMT). */
    @Column(name = "outstanding_amount", nullable = false, precision = 13, scale = 2)
    private BigDecimal outstandingAmount;

    /** GBP equivalent. */
    @Column(name = "gbp_equivalent", nullable = false, precision = 13, scale = 2)
    private BigDecimal gbpEquivalent;

    /** Next review. */
    @Column(name = "next_review_date")
    private LocalDate nextReviewDate;

    /** Open or closed. */
    @Column(name = "status", nullable = false, length = 8)
    private String status;

    protected Reserve() {
    }

    public UUID getReserveId() {
        return reserveId;
    }

    public String getClaimId() {
        return claimId;
    }

    public String getReserveType() {
        return reserveType;
    }

    public String getCurrency() {
        return currency;
    }

    public BigDecimal getOutstandingAmount() {
        return outstandingAmount;
    }

    public BigDecimal getGbpEquivalent() {
        return gbpEquivalent;
    }

    public LocalDate getNextReviewDate() {
        return nextReviewDate;
    }

    public String getStatus() {
        return status;
    }
}
