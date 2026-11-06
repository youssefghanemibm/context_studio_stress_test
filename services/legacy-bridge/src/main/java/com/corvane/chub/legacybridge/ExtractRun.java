package com.corvane.chub.legacybridge;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/** One row of CLR.T_INTERFACE_LOG as seen by the bridge. */
public record ExtractRun(long ifRunId, String interfaceId, LocalDateTime runTs, long recordCount,
                         BigDecimal hashTotal, String runStatus, String branchCd) {

    public boolean completed() {
        return "OK".equals(runStatus);
    }
}
