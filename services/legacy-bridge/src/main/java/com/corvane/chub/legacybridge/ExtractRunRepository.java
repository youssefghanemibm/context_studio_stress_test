package com.corvane.chub.legacybridge;

import java.time.LocalDateTime;
import java.util.List;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

@Repository
public class ExtractRunRepository {

    private static final String SQL =
            "SELECT IF_RUN_ID, INTERFACE_ID, RUN_TS, RECORD_COUNT, HASH_TOTAL, RUN_STATUS, BRANCH_CD"
            + " FROM CLR.T_INTERFACE_LOG"
            + " WHERE INTERFACE_ID = ? AND RUN_TS > ?"
            + " ORDER BY RUN_TS";

    private final JdbcTemplate jdbc;

    public ExtractRunRepository(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public List<ExtractRun> runsSince(String interfaceId, LocalDateTime since) {
        return jdbc.query(SQL, (rs, i) -> new ExtractRun(
                rs.getLong("IF_RUN_ID"), rs.getString("INTERFACE_ID").trim(),
                rs.getTimestamp("RUN_TS").toLocalDateTime(), rs.getLong("RECORD_COUNT"),
                rs.getBigDecimal("HASH_TOTAL"), rs.getString("RUN_STATUS").trim(),
                rs.getString("BRANCH_CD")), interfaceId, since);
    }
}
