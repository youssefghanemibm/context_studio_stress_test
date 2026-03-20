package com.corvane.chub.reserve;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.YearMonth;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

/**
 * Currency revaluation run for non-GBP reserves (POST /revaluation-runs).
 *
 * <p>Replaces CLARA's year-end revaluation program CLRGL090 from Wave 2 (ADR-028). CLRGL090
 * updates the GBP equivalent on CLR.T_RESERVE in place and writes no movement, which is
 * why CDC on the movement table was abandoned (ADR-005, ADR-017). Here every revaluation is
 * posted as an RV reserve movement so the audit trail is complete (DEC-005, closing audit
 * finding IA-25-07 in the target). Rates are the Group Ledger month-end rates, the same
 * rates BR-RSV-003 uses for authority checks on Nordic reserves.
 */
@Component
public class ReserveRevaluationJob {

    private final ReserveRepository reserves;
    private final ReserveMovementService movements;
    private final GroupLedgerRateProvider rates;

    public ReserveRevaluationJob(ReserveRepository reserves, ReserveMovementService movements,
                                 GroupLedgerRateProvider rates) {
        this.reserves = reserves;
        this.movements = movements;
        this.rates = rates;
    }

    @Transactional
    public RevaluationResult run(YearMonth period) {
        GroupLedgerRateProvider.RateTable monthEnd = rates.groupLedgerMonthEnd(period);
        int posted = 0;
        for (Reserve reserve : reserves.findOpenByCurrencyNot("GBP")) {
            BigDecimal rate = monthEnd.toGbp(reserve.getCurrency());
            BigDecimal revalued = reserve.getOutstandingAmount().multiply(rate).setScale(2, RoundingMode.HALF_EVEN);
            BigDecimal delta = revalued.subtract(reserve.getGbpEquivalent());
            if (delta.signum() == 0) {
                continue;
            }
            // Every revaluation becomes an RV movement; the reserve row is never updated silently.
            movements.post(reserve, MovementType.RV, delta, "REVALUATION " + period);
            posted++;
        }
        return new RevaluationResult(period, monthEnd.source(), posted);
    }

    public record RevaluationResult(YearMonth period, String rateSource, int movementsPosted) {
    }
}
