package com.corvane.chub.fraud;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.OffsetDateTime;
import java.util.UUID;

/**
 * JPA mapping of fraud.referral in database chub_fraud (owned by fraud-referral-svc, ADR-003).
 */
@Entity
@Table(schema = "fraud", name = "referral")
public class Referral {

    /** Referral. */
    @Id
    @Column(name = "referral_id", nullable = false)
    private UUID referralId;

    /** Claim. */
    @Column(name = "claim_id", nullable = false, length = 20)
    private String claimId;

    /** Score. */
    @Column(name = "sentinel_score", nullable = false)
    private short sentinelScore;

    /** Threshold applied (65, or 60 for Tier-3 from 2026-10-01). */
    @Column(name = "threshold_applied", nullable = false)
    private short thresholdApplied;

    /** Tier. */
    @Column(name = "tier", nullable = false)
    private short tier;

    /** Referred. */
    @Column(name = "referred_at", nullable = false)
    private OffsetDateTime referredAt;

    /** SIU case. */
    @Column(name = "siu_case_id", length = 12)
    private String siuCaseId;

    /** Rule (BR-FRD-031). */
    @Column(name = "rule_id", nullable = false, length = 12)
    private String ruleId;

    protected Referral() {
    }

    public UUID getReferralId() {
        return referralId;
    }

    public String getClaimId() {
        return claimId;
    }

    public short getSentinelScore() {
        return sentinelScore;
    }

    public short getThresholdApplied() {
        return thresholdApplied;
    }

    public short getTier() {
        return tier;
    }

    public OffsetDateTime getReferredAt() {
        return referredAt;
    }

    public String getSiuCaseId() {
        return siuCaseId;
    }

    public String getRuleId() {
        return ruleId;
    }
}
