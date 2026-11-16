"""Variant-b-only extras: legacy-bridge, tools/zz-reconcile, fixtures/claims, docs/runbooks,
analytics/notebooks.  Each canary statement (CN-01, 02, 03, 05, 06) appears ONLY in its own
b-only file; sibling files read the canary values from configuration instead of stating them.
"""
from __future__ import annotations

import datetime as dt
import json
from decimal import Decimal, ROUND_HALF_EVEN

from lib import W, SVC, rng, B_COMMIT
from services import T

B = B_COMMIT[0]
V = ("b",)
N_FIXTURES = 100          # sized so variant b lands inside 600-700 files with the legacy half (see build/notes)


def canary(cid):
    return W.canaries[cid]["statement"]


def wave_scope_name(w):
    """'Wave 2 – UK home, ...' -> 'UK home, ...' (the wave number is already in the sentence)."""
    name = w["name"].replace("–", "-")
    return name.split(" - ", 1)[1] if " - " in name else name


# ---------------------------------------------------------------------------------------------
# services/legacy-bridge (CN-01)
# ---------------------------------------------------------------------------------------------

def legacy_bridge(repo):
    base = "services/legacy-bridge"
    jb = f"{base}/src/main/java/com/corvane/chub/legacybridge"
    readme = "\n".join([
        "# legacy-bridge",
        "",
        "Small Spring Boot module that tells Claims Hub tooling when a CLARA extract has finished.",
        "It is not deployed with the Claims Hub services; it runs alongside the reserve parallel run",
        "and the Wave 2 synchronisation tooling and is removed when CLARA is decommissioned.",
        "",
        "## What it does",
        "",
        canary("CN-01"),
        "A run counts as completed when its `RUN_STATUS` is `OK`; runs in `ER` or `RR` are reported",
        "as failed or rerun and are never forwarded. For each completed run the bridge records the",
        "interface id, `RUN_TS`, `RECORD_COUNT` and `HASH_TOTAL`, and serves them on",
        "`GET /extract-runs?interface=CLX-IF-042&since=<timestamp>`.",
        "",
        "The record count and hash total let consumers check that they have read the whole extract",
        "before they act on it. The bridge only reads `CLR.T_INTERFACE_LOG`; it never writes to DB2.",
        "",
        "## Configuration",
        "",
        "| Property | Meaning |",
        "|---|---|",
        "| `bridge.poll-interval` | How often the interface log is read (set per environment) |",
        "| `bridge.interfaces` | Interface ids to watch, for example `CLX-IF-042` |",
        "| `clara.db2.url` | JDBC URL of the CLARA DB2 subsystem (read-only user) |",
        "",
        "## Running locally",
        "",
        "`mvn -f services/legacy-bridge/pom.xml spring-boot:run -Dspring-boot.run.profiles=local`",
        "",
        "A local profile points at the DB2 test copy used by the mainframe team; ask the CLARA",
        "platform team for read access before running it.",
        "",
    ])
    repo.add(f"{base}/README.md", readme, B, V, author="P050")
    repo.add(f"{base}/pom.xml", T("""
        <?xml version="1.0" encoding="UTF-8"?>
        <project xmlns="http://maven.apache.org/POM/4.0.0"
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
            <modelVersion>4.0.0</modelVersion>
            <parent>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-starter-parent</artifactId>
                <version>3.4.5</version>
                <relativePath/>
            </parent>
            <groupId>com.corvane.chub</groupId>
            <artifactId>legacy-bridge</artifactId>
            <version>0.3.0-SNAPSHOT</version>
            <name>legacy-bridge</name>
            <properties>
                <java.version>21</java.version>
            </properties>
            <dependencies>
                <dependency>
                    <groupId>org.springframework.boot</groupId>
                    <artifactId>spring-boot-starter-web</artifactId>
                </dependency>
                <dependency>
                    <groupId>org.springframework.boot</groupId>
                    <artifactId>spring-boot-starter-jdbc</artifactId>
                </dependency>
                <dependency>
                    <groupId>org.springframework.boot</groupId>
                    <artifactId>spring-boot-starter-test</artifactId>
                    <scope>test</scope>
                </dependency>
            </dependencies>
        </project>
    """), B, V, author="P050")
    repo.add(f"{base}/src/main/resources/application.yaml", T("""
        spring:
          application:
            name: legacy-bridge
        clara:
          db2:
            url: ${CLARA_DB2_URL}
            username: ${CLARA_DB2_USER}
            password: ${CLARA_DB2_PASSWORD}
        bridge:
          poll-interval: ${BRIDGE_POLL_INTERVAL}
          interfaces:
            - CLX-IF-042
        server:
          port: 8080
    """), B, V, author="P050")
    files = {
        "LegacyBridgeApplication.java": """
            package com.corvane.chub.legacybridge;

            import org.springframework.boot.SpringApplication;
            import org.springframework.boot.autoconfigure.SpringBootApplication;
            import org.springframework.boot.context.properties.ConfigurationPropertiesScan;
            import org.springframework.scheduling.annotation.EnableScheduling;

            @SpringBootApplication
            @EnableScheduling
            @ConfigurationPropertiesScan
            public class LegacyBridgeApplication {

                public static void main(String[] args) {
                    SpringApplication.run(LegacyBridgeApplication.class, args);
                }
            }
        """,
        "BridgeProperties.java": """
            package com.corvane.chub.legacybridge;

            import java.time.Duration;
            import java.util.List;
            import org.springframework.boot.context.properties.ConfigurationProperties;

            /** Bound from {@code bridge.*}; the poll interval is set per environment. */
            @ConfigurationProperties(prefix = "bridge")
            public record BridgeProperties(Duration pollInterval, List<String> interfaces) {
            }
        """,
        "ExtractRun.java": """
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
        """,
        "ExtractRunRepository.java": """
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
        """,
        "InterfaceLogPoller.java": """
            package com.corvane.chub.legacybridge;

            import java.time.LocalDateTime;
            import java.util.Map;
            import java.util.concurrent.ConcurrentHashMap;
            import org.springframework.scheduling.annotation.Scheduled;
            import org.springframework.stereotype.Component;

            /** Reads the CLARA interface log on the configured interval and remembers completed runs. */
            @Component
            public class InterfaceLogPoller {

                private final ExtractRunRepository repository;
                private final BridgeProperties properties;
                private final CompletedRunStore store;
                private final Map<String, LocalDateTime> highWater = new ConcurrentHashMap<>();

                public InterfaceLogPoller(ExtractRunRepository repository, BridgeProperties properties,
                                          CompletedRunStore store) {
                    this.repository = repository;
                    this.properties = properties;
                    this.store = store;
                }

                @Scheduled(fixedDelayString = "${bridge.poll-interval}")
                public void poll() {
                    for (String interfaceId : properties.interfaces()) {
                        LocalDateTime since = highWater.getOrDefault(interfaceId, LocalDateTime.now().minusDays(1));
                        for (ExtractRun run : repository.runsSince(interfaceId, since)) {
                            if (run.completed()) {
                                store.add(run);
                            }
                            highWater.put(interfaceId, run.runTs());
                        }
                    }
                }
            }
        """,
        "CompletedRunStore.java": """
            package com.corvane.chub.legacybridge;

            import java.time.LocalDateTime;
            import java.util.List;
            import java.util.concurrent.CopyOnWriteArrayList;
            import org.springframework.stereotype.Component;

            @Component
            public class CompletedRunStore {

                private final List<ExtractRun> runs = new CopyOnWriteArrayList<>();

                public void add(ExtractRun run) {
                    runs.add(run);
                }

                public List<ExtractRun> since(String interfaceId, LocalDateTime since) {
                    return runs.stream()
                            .filter(r -> r.interfaceId().equals(interfaceId) && r.runTs().isAfter(since))
                            .toList();
                }
            }
        """,
        "ExtractRunController.java": """
            package com.corvane.chub.legacybridge;

            import java.time.LocalDateTime;
            import java.util.List;
            import org.springframework.format.annotation.DateTimeFormat;
            import org.springframework.web.bind.annotation.GetMapping;
            import org.springframework.web.bind.annotation.RequestParam;
            import org.springframework.web.bind.annotation.RestController;

            @RestController
            public class ExtractRunController {

                private final CompletedRunStore store;

                public ExtractRunController(CompletedRunStore store) {
                    this.store = store;
                }

                @GetMapping("/extract-runs")
                public List<ExtractRun> completed(@RequestParam("interface") String interfaceId,
                                                  @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
                                                  LocalDateTime since) {
                    return store.since(interfaceId, since);
                }
            }
        """,
    }
    for fname, body in files.items():
        repo.add(f"{jb}/{fname}", T(body), B, V, author="P050")
    repo.add(f"{base}/src/test/java/com/corvane/chub/legacybridge/ExtractRunTest.java", T("""
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
    """), B, V, author="P050")


# ---------------------------------------------------------------------------------------------
# tools/zz-reconcile (CN-02)
# ---------------------------------------------------------------------------------------------

def zz_reconcile(repo):
    base = "tools/zz-reconcile"
    wave2 = W.waves["MW-2"]
    scope = wave2["scope"]
    readme = "\n".join([
        "# zz-reconcile",
        "",
        "Reconciliation tooling for the Wave 2 migration (" + wave_scope_name(wave2) + "; planned "
        + wave2["date"] + ").",
        "",
        canary("CN-02"),
        "",
        "For every claim in scope it compares the outstanding case reserve held in CLARA",
        "(`CLR.T_RESERVE.RSV_OUTSTANDING_AMT`) with the migrated reserve in Claims Hub",
        "(`reserve.reserve.outstanding_amount`), in original currency and as a GBP equivalent.",
        "A claim that exists on only one side is reported as a difference of its own kind.",
        "",
        "## Scope",
        "",
        "Products in Wave 2: " + scope + ".",
        "",
        "## Usage",
        "",
        "```",
        "python -m zz_reconcile --config config.yaml --business-date 2026-11-05",
        "python -m zz_reconcile --config config.yaml --business-date 2026-11-05 --dry-run",
        "```",
        "",
        "`--dry-run` prints the differences instead of writing them. Tolerances are not hard-coded:",
        "they are read from the run configuration agreed with the migration team.",
        "",
        "## Layout",
        "",
        "- `zz_reconcile/clara.py` reads the CLARA side (DB2 unload or the read replica)",
        "- `zz_reconcile/hub.py` reads the Claims Hub side",
        "- `zz_reconcile/compare.py` matches claims and classifies differences",
        "- `zz_reconcile/report.py` writes differences and a run summary",
        "",
    ])
    repo.add(f"{base}/README.md", readme, B, V, author="P051")
    repo.add(f"{base}/pyproject.toml", T("""
        [project]
        name = "zz-reconcile"
        version = "0.4.0"
        description = "Wave 2 reserve reconciliation between CLARA and Claims Hub"
        requires-python = ">=3.11"
        dependencies = ["pyyaml>=6", "psycopg[binary]>=3.1"]

        [project.scripts]
        zz-reconcile = "zz_reconcile.cli:main"

        [tool.pytest.ini_options]
        testpaths = ["tests"]
    """), B, V, author="P051")
    repo.add(f"{base}/config.example.yaml", T("""
        # Copy to config.yaml and fill in per environment. Never commit real connection strings.
        clara:
          source: db2-unload            # or: read-replica
          unload_dir: /data/clara/unload
        hub:
          dsn_env: CHUB_RESERVE_DSN     # environment variable holding the reserve database DSN
        target:
          dsn_env: RECON_DSN
          table_env: RECON_TARGET_TABLE
        tolerance:
          per_claim: null               # set from the agreed migration reconciliation standard
          portfolio: null
        products:
    """) + "".join(f"  - {p.strip()}\n" for p in scope.split(",")), B, V, author="P051")
    mods = {
        "zz_reconcile/__init__.py": '"""Wave 2 reserve reconciliation between CLARA and Claims Hub."""\n\n__version__ = "0.4.0"\n',
        "zz_reconcile/__main__.py": "from zz_reconcile.cli import main\n\nif __name__ == \"__main__\":\n    raise SystemExit(main())\n",
        "zz_reconcile/cli.py": T('''
            """Command line entry point."""
            import argparse
            import datetime as dt

            import yaml

            from zz_reconcile import clara, compare, hub, report


            def main(argv=None) -> int:
                ap = argparse.ArgumentParser(prog="zz-reconcile")
                ap.add_argument("--config", required=True)
                ap.add_argument("--business-date", required=True, type=dt.date.fromisoformat)
                ap.add_argument("--dry-run", action="store_true")
                args = ap.parse_args(argv)
                with open(args.config, encoding="utf-8") as fh:
                    cfg = yaml.safe_load(fh)
                left = clara.load(cfg["clara"], cfg["products"], args.business_date)
                right = hub.load(cfg["hub"], cfg["products"], args.business_date)
                diffs = compare.diff(left, right, cfg["tolerance"])
                if args.dry_run:
                    report.print_diffs(diffs)
                else:
                    report.write(cfg["target"], args.business_date, diffs)
                return 0 if not diffs else 2
        '''),
        "zz_reconcile/clara.py": T('''
            """CLARA side: reserve rows per claim from CLR.T_RESERVE (unload file or read replica)."""
            import csv
            import pathlib
            from decimal import Decimal


            def load(cfg, products, business_date):
                if cfg["source"] != "db2-unload":
                    raise NotImplementedError("read-replica source is configured per environment")
                path = pathlib.Path(cfg["unload_dir"]) / f"T_RESERVE_{business_date:%Y%m%d}.csv"
                out = {}
                with open(path, newline="", encoding="utf-8") as fh:
                    for row in csv.DictReader(fh):
                        if row["PRODUCT_CD"] not in products:
                            continue
                        out[row["CLAIM_ID"].strip()] = (Decimal(row["RSV_OUTSTANDING_AMT"]), row["RSV_CURRENCY_CD"])
                return out
        '''),
        "zz_reconcile/hub.py": T('''
            """Claims Hub side: outstanding reserve per claim from reserve.reserve."""
            import os

            import psycopg

            SQL = """
                SELECT r.claim_id, r.outstanding_amount, r.currency
                  FROM reserve.reserve r
                 WHERE r.status = 'OPEN'
            """


            def load(cfg, products, business_date):
                out = {}
                with psycopg.connect(os.environ[cfg["dsn_env"]]) as conn:
                    for claim_id, amount, currency in conn.execute(SQL):
                        out[claim_id] = (amount, currency)
                return out
        '''),
        "zz_reconcile/compare.py": T('''
            """Match claims between CLARA and Claims Hub and classify differences."""
            from dataclasses import dataclass
            from decimal import Decimal


            @dataclass(frozen=True)
            class Difference:
                claim_id: str
                kind: str            # MISSING_IN_HUB, MISSING_IN_CLARA, AMOUNT, CURRENCY
                clara_amount: Decimal | None
                hub_amount: Decimal | None


            def to_hub_id(clara_id: str) -> str:
                """UK2025118204 -> CLM-UK-2025-118204."""
                return f"CLM-{clara_id[:2]}-{clara_id[2:6]}-{clara_id[6:]}"


            def diff(clara, hub, tolerance):
                per_claim = tolerance.get("per_claim")
                if per_claim is None:
                    raise ValueError("tolerance.per_claim must be set in the run configuration")
                per_claim = Decimal(str(per_claim))
                out = []
                hub_seen = set()
                for cid, (amount, ccy) in clara.items():
                    hid = to_hub_id(cid)
                    if hid not in hub:
                        out.append(Difference(hid, "MISSING_IN_HUB", amount, None))
                        continue
                    hub_seen.add(hid)
                    h_amount, h_ccy = hub[hid]
                    if h_ccy != ccy:
                        out.append(Difference(hid, "CURRENCY", amount, h_amount))
                    elif abs(h_amount - amount) > per_claim:
                        out.append(Difference(hid, "AMOUNT", amount, h_amount))
                for hid, (h_amount, _) in hub.items():
                    if hid not in hub_seen:
                        out.append(Difference(hid, "MISSING_IN_CLARA", None, h_amount))
                return out
        '''),
        "zz_reconcile/report.py": T('''
            """Write differences to the configured target table, or print them."""
            import os

            import psycopg


            def print_diffs(diffs):
                for d in diffs:
                    print(f"{d.claim_id:22} {d.kind:18} {d.clara_amount!s:>16} {d.hub_amount!s:>16}")
                print(f"{len(diffs)} difference(s)")


            def write(target, business_date, diffs):
                table = os.environ[target["table_env"]]
                with psycopg.connect(os.environ[target["dsn_env"]]) as conn:
                    with conn.cursor() as cur:
                        cur.executemany(
                            f"INSERT INTO {table} (business_date, claim_id, kind, clara_amount, hub_amount)"
                            " VALUES (%s, %s, %s, %s, %s)",
                            [(business_date, d.claim_id, d.kind, d.clara_amount, d.hub_amount) for d in diffs])
        '''),
        "tests/test_compare.py": T('''
            from decimal import Decimal

            import pytest

            from zz_reconcile.compare import diff, to_hub_id


            def test_claim_id_mapping():
                assert to_hub_id("SE2026001234") == "CLM-SE-2026-001234"


            def test_missing_and_amount_differences():
                clara = {"SE2026000001": (Decimal("100.00"), "SEK"), "SE2026000002": (Decimal("50.00"), "SEK")}
                hub = {"CLM-SE-2026-000001": (Decimal("100.00"), "SEK"), "CLM-SE-2026-000009": (Decimal("1.00"), "SEK")}
                kinds = sorted(d.kind for d in diff(clara, hub, {"per_claim": "0"}))
                assert kinds == ["MISSING_IN_CLARA", "MISSING_IN_HUB"]


            def test_tolerance_must_be_configured():
                with pytest.raises(ValueError):
                    diff({}, {}, {"per_claim": None})
        '''),
        "tests/conftest.py": T('''
            import pathlib
            import sys

            sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
        '''),
    }
    for rel, body in mods.items():
        repo.add(f"{base}/{rel}", body, B, V, author="P051")


# ---------------------------------------------------------------------------------------------
# fixtures/claims (CN-03)
# ---------------------------------------------------------------------------------------------

T3 = {"GBP": Decimal(50000), "NOK": Decimal(650000), "SEK": Decimal(680000), "DKK": Decimal(430000)}
T2_GBP = Decimal(5000)
AVOID_IDS = {"CLM-UK-2025-118204", "CLM-UK-2026-207731", "CLM-SE-2026-004417"}


def fixtures(repo):
    r = rng("fixtures")
    products = sorted(W.products.values(), key=lambda p: p["id"])
    made = []
    used = set()
    for i in range(1, N_FIXTURES + 1):
        prod = products[(i - 1) % len(products)]
        ct = W.claim_types[r.choice(prod["claim_types"])]
        region, ccy = prod["region"], prod["currency"]
        rate = (T3["GBP"] / T3[ccy]) if ccy != "GBP" else Decimal(1)
        band = r.random()
        if band < 0.35:
            gbp = Decimal(r.randint(300, 4900))
        elif band < 0.75:
            gbp = Decimal(r.randint(5000, 48000))
        else:
            gbp = Decimal(r.randint(51000, 420000))
        local = (gbp / rate).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN)
        gbp_eq = (local * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        bi = ct["id"] == "CT-BIJ"
        third = ct["id"] in ("CT-TPD", "CT-PLB", "CT-BIJ") or r.random() < 0.1
        lit = bi and r.random() < 0.3
        total_loss = ct["id"] in ("CT-FIR", "CT-FLD") and gbp > 60000 and r.random() < 0.5
        tier = 3 if (local >= T3[ccy] or bi or lit or total_loss) else (2 if (gbp_eq >= T2_GBP or third) else 1)
        while True:
            claim_id = f"CLM-{region}-2026-{r.randint(100000, 299999):06d}"
            if claim_id not in used and claim_id not in AVOID_IDS:
                used.add(claim_id)
                break
        loss = dt.date(2026, 10, 1) + dt.timedelta(days=r.randint(0, 30))
        notified = dt.datetime(loss.year, loss.month, loss.day, r.randint(7, 20), r.randint(0, 59)) + \
            dt.timedelta(days=r.randint(0, 4))
        score = r.randint(3, 97)
        threshold = 60 if tier == 3 else 65
        fx = {
            "fixture_id": f"fx-{i:03d}",
            "description": f"Tier-{tier} {ct['name'].lower()} claim, {prod['name']}",
            "claim": {
                "claim_id": claim_id,
                "legacy_claim_id": claim_id[4:6] + claim_id[7:11] + claim_id[12:],
                "policy_no": f"POL{r.randint(1000000, 9999999)}",
                "product_code": prod["id"],
                "claim_type": ct["id"],
                "loss_date": loss.isoformat(),
                "notified_at": notified.isoformat(timespec="minutes"),
                "status": "OPEN",
                "tier": tier,
                "region": region,
                "currency": ccy,
            },
            "triage_input": {
                "estimated_incurred": str(local),
                "estimated_incurred_gbp": str(gbp_eq),
                "bodily_injury": bi,
                "litigation_at_notification": lit,
                "property_total_loss": total_loss,
                "third_party_involved": third,
            },
            "sentinel_score": score,
            "expected": {
                "tier": tier,
                "threshold_applied": threshold,
                "fraud_referral": score >= threshold,
            },
        }
        slug = f"fx_{i:03d}_{prod['id'][4:].lower().replace('-', '_')}_{ct['peril_code'].lower()}.json"
        repo.add(f"fixtures/claims/{slug}", json.dumps(fx, indent=2, ensure_ascii=False) + "\n", B, V, author="P053")
        made.append(fx)
    by_tier = {t: sum(1 for f in made if f["expected"]["tier"] == t) for t in (1, 2, 3)}
    referred = sum(1 for f in made if f["expected"]["fraud_referral"])
    by_prod = {}
    for f in made:
        by_prod[f["claim"]["product_code"]] = by_prod.get(f["claim"]["product_code"], 0) + 1
    lines = [
        "# Claim fixture index",
        "",
        f"`fixtures/claims/` holds {len(made)} claim fixtures used by the triage, fraud-referral and",
        "reserve contract tests. Every fixture records the triage input, a Sentinel score and the",
        "expected outcome under the current rules (BR-TRI-003 v3 tiers; BR-FRD-031 v2 thresholds of",
        "65, or 60 for Tier-3 claims scored from 2026-10-01). Fixtures contain no personal data.",
        "",
        "## Canonical cases",
        "",
        canary("CN-03") + " It is built by the test",
        "harness at start-up rather than stored here, because its reserve history is long.",
        "",
        "## Counts",
        "",
        "| Tier | Fixtures |",
        "|---|---|",
    ] + [f"| Tier-{t} | {n} |" for t, n in by_tier.items()] + [
        "",
        f"{referred} fixtures are expected to be referred to SIU.",
        "",
        "| Product | Fixtures |",
        "|---|---|",
    ] + [f"| {p} | {n} |" for p, n in sorted(by_prod.items())] + [
        "",
        "## Adding a fixture",
        "",
        "Name new files `fx_<nnn>_<product>_<peril>.json`, keep the expected block in step with the",
        "rule versions in force, and run `make test SERVICE=triage-svc` before opening a pull request.",
        "",
    ]
    repo.add("fixtures/claims/zz_fixture_index.md", "\n".join(lines), B, V, author="P053")
    repo.add("fixtures/README.md", T("""
        # Test fixtures

        Shared test data for Claims Hub contract and integration tests. Claim fixtures live in
        `claims/`; see the index file there for what each set covers. Fixture data is synthetic.
    """), B, V, author="P053")
    return {"count": len(made), "by_tier": by_tier, "referred": referred}


# ---------------------------------------------------------------------------------------------
# docs/runbooks (CN-05)
# ---------------------------------------------------------------------------------------------

def runbooks(repo):
    base = "docs/runbooks"
    w2 = W.waves["MW-2"]
    rb = {}
    rb["wave2-dress-rehearsal.md"] = "\n".join([
        "# Wave 2 dress rehearsal runbook",
        "",
        f"Wave 2 ({wave_scope_name(w2)}) is planned for {w2['date']} with a migration freeze from",
        f"{w2['freeze']}. Dress rehearsals repeat the cut-over end to end on masked data (ADR-025).",
        "",
        "## Schedule",
        "",
        canary("CN-05"),
        "",
        "## Before the rehearsal",
        "",
        "1. Confirm the masked data set has been refreshed and signed off by the data protection officer.",
        "2. Scale the target services in the rehearsal environment to their production replica counts.",
        "3. Check that the reserve bridge (CLX-IF-049) consumer group has no lag before the extract starts.",
        "4. Announce the rehearsal window in the programme channel.",
        "",
        "## During the rehearsal",
        "",
        "1. Run the migration load for the Wave 2 products in scope: " + w2["scope"] + ".",
        "2. Run the reconciliation tooling in `tools/zz-reconcile` against the rehearsal databases.",
        "3. Record every manual step and its duration in the rehearsal log.",
        "",
        "## After the rehearsal",
        "",
        "1. Review the reconciliation differences with the migration lead.",
        "2. Raise defects for every unexpected difference and link them to the rehearsal log.",
        "3. Restore the rehearsal environment to its baseline.",
        "",
    ])
    svc_rb = {
        "reserve-engine": [
            "Consumer lag on `claims.reserve.movement.v1` usually means the bridge delivered a large batch; let it drain before restarting pods.",
            "The Tier-3 review cadence (`reserve.tier3-review-days`) must match CLARA's RSV_T3_REVIEW_DAYS in CLR.T_PARAM; a mismatch caused INC-2026-0702.",
            "A currency revaluation run is started with `POST /revaluation-runs`; every revaluation is posted as an RV movement.",
        ],
        "fraud-referral-svc": [
            "Referral thresholds are effective-dated configuration (ADR-020); change them by pull request, never by editing the ConfigMap.",
            "Customer-notice deadlines are referral date plus 10 business days; check `fraud.customer_notice.due_date` when a complaint arrives.",
            "If SIU Case Manager is unavailable, referrals queue and are retried; do not re-create them by hand.",
        ],
        "payment-orchestrator": [
            "Every instruction to the Corvane Payments Gateway carries an idempotency key (ADR-021); a retry after a timeout is safe.",
            "Before cancelling a payment, check its status in `payment.payment_instruction`.",
            "Duplicate-payment alerts are Sev2; follow the incident process used for INC-2026-0914.",
        ],
        "notification-svc": [
            "Fraud-referral notices use Notify templates FRN01 (letter) and FRN02 (SMS).",
            "If Notify is degraded, notices are held and sent in order once it recovers; the due date does not move.",
            "Holiday calendars for UK, NO, SE and DK drive the business-day arithmetic.",
        ],
    }
    for n, tips in svc_rb.items():
        s = SVC[n]
        rb[f"{n}.md"] = "\n".join([
            f"# Runbook: {n}",
            "",
            f"Namespace `{s['k8s_namespace']}`, {s['replicas']} replicas in production.",
            "",
            "## Health",
            "",
            f"- Readiness: `/actuator/health/readiness` on each pod of `{n}`",
            f"- Logs: `oc logs -n {s['k8s_namespace']} deploy/{n} --since=15m`",
            "",
            "## Known situations",
            "",
        ] + [f"- {t}" for t in tips] + [
            "",
            "## Restart",
            "",
            f"`oc rollout restart -n {s['k8s_namespace']} deploy/{n}` and watch `oc rollout status`.",
            "",
        ])
    generic = {
        "kafka-consumer-lag.md": ("Kafka consumer lag", [
            "Identify the consumer group and topic from the alert.",
            "Check whether the producer published an unusual volume (bridge batches arrive once a day).",
            "Scale the consumer deployment only if lag keeps growing after the batch has drained.",
            "If a poison message blocks a partition, move it to the dead-letter topic and replay later.",
        ]),
        "dead-letter-replay.md": ("Dead-letter replay", [
            "List the dead-letter records and group them by error.",
            "Fix the cause first: schema mismatch, missing reference data or a downstream outage.",
            "Replay in small batches and watch the consumer error rate.",
            "Record the replay in the incident ticket.",
        ]),
        "postgres-restore.md": ("PostgreSQL point-in-time restore", [
            "Agree the restore point with the service owner and record it in the change ticket.",
            "Scale the service to zero replicas before restoring its database.",
            "Restore into a new cluster, validate row counts, then switch the service over.",
            "Scale the service back to its production replica count.",
        ]),
        "release-rollback.md": ("Release rollback", [
            "Roll back with `oc rollout undo` to the previous ReplicaSet.",
            "Check that database migrations of the failed release are backward compatible before rolling back.",
            "Raise a problem record and attach the release notes of the failed release.",
        ]),
        "on-call-handover.md": ("On-call handover", [
            "Review open incidents and changes scheduled for the next 24 hours.",
            "Check the Kafka lag and error-rate dashboards for every Claims Hub namespace.",
            "Hand over any manual workarounds in writing.",
        ]),
        "reserve-bridge-clx-if-049.md": ("Reserve movement bridge (CLX-IF-049)", [
            "The bridge reads RSVMOVE records from MQ queue CLR.RSVMOVE.OUT daily at 02:45 and publishes them to `claims.reserve.movement.v1`.",
            "If the CLARA extract (CLX-IF-042) is late, the bridge finds an empty queue; rerun it once the extract completes.",
            "Messages are keyed by claim_id and use Avro schema v3.",
        ]),
    }
    for fname, (title, steps) in generic.items():
        rb[fname] = "\n".join([f"# {title}", ""] + [f"{i}. {s}" for i, s in enumerate(steps, 1)] + [""])
    rb["README.md"] = "\n".join(["# Runbooks", "", "Operational runbooks for Claims Hub and the migration.", ""] +
                                [f"- [{f[:-3]}]({f})" for f in sorted(rb) if f != "README.md"] + [""])
    for fname, text in rb.items():
        repo.add(f"{base}/{fname}", text, B, V, author="P048" if fname.startswith("wave2") else "P053")


# ---------------------------------------------------------------------------------------------
# analytics/notebooks (CN-06)
# ---------------------------------------------------------------------------------------------

NB_HEAD = '''# %% [markdown]
# # {title}
#
# {purpose}
# Connection settings come from the environment (`CDW_DSN`); see the README.

# %%
import os

import pandas as pd
import sqlalchemy as sa

engine = sa.create_engine(os.environ["CDW_DSN"])

'''


def notebooks(repo):
    base = "analytics/notebooks"
    readme = "\n".join([
        "# Analytics notebooks",
        "",
        "Exploratory notebooks for the Data & Analytics team, kept as plain Python files with",
        "`# %%` cell markers so they diff cleanly.",
        "",
        "## Data access",
        "",
        canary("CN-06"),
        "Set `CDW_DSN` in your environment before running a notebook; credentials come from",
        "the team vault and are never committed.",
        "",
        "## Notebooks",
        "",
    ])
    nbs = {
        "01_reserve_movement_profile.py": ("Reserve movement profile",
            "Distribution of reserve movements by movement type and product, including RV revaluation movements.",
            "SELECT movement_type, source, currency, amount_minor, created_at FROM reserve_movement",
            "df.groupby(['movement_type', 'currency'])['amount_minor'].describe()"),
        "02_fraud_referral_funnel.py": ("Fraud referral funnel",
            "Scored claims, referrals and SIU outcomes by tier and threshold applied.",
            "SELECT tier, threshold_applied, sentinel_score, referred_at FROM fraud_referral",
            "df.groupby(['tier', 'threshold_applied']).size()"),
        "03_tier_mix_by_product.py": ("Tier mix by product",
            "Share of Tier-1, Tier-2 and Tier-3 claims per product.",
            "SELECT product_code, tier FROM claim",
            "pd.crosstab(df['product_code'], df['tier'], normalize='index')"),
        "04_settlement_cycle_time.py": ("Settlement cycle time",
            "Days from first notice of loss to final settlement, by product and tier.",
            "SELECT c.product_code, c.tier, c.notified_at, s.agreed_at FROM claim c JOIN settlement s USING (claim_id) WHERE s.final",
            "(df['agreed_at'] - df['notified_at']).dt.days.groupby(df['product_code']).median()"),
        "05_recovery_pipeline.py": ("Recovery pipeline",
            "Open recovery cases by type and expected amount, and receipts over time.",
            "SELECT type, status, expected_amount FROM recovery_case",
            "df.pivot_table(index='type', columns='status', values='expected_amount', aggfunc='sum')"),
        "06_fnol_channel_trend.py": ("FNOL channel trend",
            "First notices of loss by channel and month.",
            "SELECT channel, date_trunc('month', received_at) AS month FROM fnol_notification",
            "df.groupby(['month', 'channel']).size().unstack(fill_value=0)"),
        "07_notice_deadline_compliance.py": ("Customer notice deadline compliance",
            "Fraud-referral customer notices sent before their due date, and deferrals.",
            "SELECT due_date, deferred_until, sent_at FROM fraud_customer_notice",
            "(df['sent_at'].dt.date <= df['due_date']).mean()"),
        "08_reserve_review_backlog.py": ("Tier-3 reserve review backlog",
            "Tier-3 claims whose next reserve review date has passed.",
            "SELECT claim_id, next_review_date, cadence_days FROM review_schedule",
            "df[df['next_review_date'] < pd.Timestamp.today().normalize()]"),
    }
    for fname, (title, purpose, sql, expr) in nbs.items():
        body = NB_HEAD.format(title=title, purpose=purpose) + (
            "# %%\n"
            f"df = pd.read_sql(sa.text(\"{sql}\"), engine)\n"
            "df.head()\n\n"
            "# %%\n"
            f"{expr}\n"
        )
        repo.add(f"{base}/{fname}", body, B, V, author="P036")
        readme += f"- `{fname}`: {purpose}\n"
    readme += "\n"
    repo.add(f"{base}/README.md", readme, B, V, author="P036")
    repo.add(f"{base}/requirements.txt", "pandas>=2.2\nsqlalchemy>=2.0\npsycopg[binary]>=3.1\nmatplotlib>=3.8\n", B, V,
             author="P036")


def build(repo):
    legacy_bridge(repo)
    zz_reconcile(repo)
    stats = fixtures(repo)
    runbooks(repo)
    notebooks(repo)
    return stats
