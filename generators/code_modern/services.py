"""services/<service>/ for the 13 Claims Hub services (final state + history modifications)."""
from __future__ import annotations

import textwrap

from lib import (W, SVC, PKG, OLD_RESERVE, NEW_RESERVE, HEAD_DATE, rng, pick, commit_date)

SKELETON_COMMIT = {
    "claim-core-svc": "F-03", "fnol-intake-svc": "F-03", "triage-svc": "F-03", "assessment-svc": "F-03",
    "notification-svc": "F-03", "document-svc": "F-03",
    "reserve-engine": "F-04", "gl-posting-svc": "F-04", "reporting-feed-svc": "F-04",
    "fraud-referral-svc": "F-05", "settlement-svc": "F-05", "payment-orchestrator": "F-05",
    "recovery-svc": "F-06",
}
APP_CLASS = {
    "claim-core-svc": "ClaimCoreApplication", "fnol-intake-svc": "FnolIntakeApplication",
    "triage-svc": "TriageApplication", "assessment-svc": "AssessmentApplication",
    "reserve-engine": "ReserveApplication", "fraud-referral-svc": "FraudReferralApplication",
    "settlement-svc": "SettlementApplication", "payment-orchestrator": "PaymentOrchestratorApplication",
    "recovery-svc": "RecoveryApplication", "document-svc": "DocumentApplication",
    "notification-svc": "NotificationApplication", "gl-posting-svc": "GlPostingApplication",
    "reporting-feed-svc": "ReportingFeedApplication",
}
BOOT_FINAL, BOOT_HIST = "3.4.5", [("F-10", "3.3.2", "3.3.5"), ("F-15", "3.3.5", "3.4.1"), ("F-20", "3.4.1", "3.4.5")]


def T(s: str, **kw) -> str:
    s = textwrap.dedent(s).lstrip("\n")
    for k, v in kw.items():
        s = s.replace(f"@@{k}@@", str(v))
    assert "@@" not in s, s[:200]
    return s


def jbase(name):
    return f"services/{name}/src/main/java/com/corvane/chub/{PKG[name]}"


def tbase(name):
    return f"services/{name}/src/test/java/com/corvane/chub/{PKG[name]}"


def database(name):
    tabs = SVC[name]["postgres_tables"]
    return W.tables[tabs[0]]["database"]


# ---------------------------------------------------------------------------------------------
# pom.xml
# ---------------------------------------------------------------------------------------------

def pom(name: str) -> str:
    extra_deps = ""
    if SVC[name]["kafka_topics"]["consumes"] or SVC[name]["kafka_topics"]["produces"]:
        extra_deps += T("""
                <dependency>
                    <groupId>org.springframework.kafka</groupId>
                    <artifactId>spring-kafka</artifactId>
                </dependency>
        """)
    desc = SVC[name]["description"]
    return T("""
        <?xml version="1.0" encoding="UTF-8"?>
        <project xmlns="http://maven.apache.org/POM/4.0.0"
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
            <modelVersion>4.0.0</modelVersion>

            <parent>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-starter-parent</artifactId>
                <version>@@boot@@</version>
                <relativePath/>
            </parent>

            <groupId>com.corvane.chub</groupId>
            <artifactId>@@name@@</artifactId>
            <version>1.0.0-SNAPSHOT</version>
            <name>@@name@@</name>
            <description>@@desc@@</description>

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
                    <artifactId>spring-boot-starter-data-jpa</artifactId>
                </dependency>
                <dependency>
                    <groupId>org.springframework.boot</groupId>
                    <artifactId>spring-boot-starter-actuator</artifactId>
                </dependency>
                <dependency>
                    <groupId>org.springframework.boot</groupId>
                    <artifactId>spring-boot-starter-validation</artifactId>
                </dependency>
        @@extra@@        <dependency>
                    <groupId>org.postgresql</groupId>
                    <artifactId>postgresql</artifactId>
                    <scope>runtime</scope>
                </dependency>
                <dependency>
                    <groupId>org.springframework.boot</groupId>
                    <artifactId>spring-boot-starter-test</artifactId>
                    <scope>test</scope>
                </dependency>
            </dependencies>

            <build>
                <plugins>
                    <plugin>
                        <groupId>org.springframework.boot</groupId>
                        <artifactId>spring-boot-maven-plugin</artifactId>
                    </plugin>
                </plugins>
            </build>
        </project>
    """, boot=BOOT_FINAL, name=name, desc=desc.replace("&", "and"), extra=textwrap.indent(extra_deps, "        "))


def pom_mods(repo, name, path):
    for cid, old, new in BOOT_HIST:
        repo.modify(path, cid, f"<artifactId>spring-boot-starter-parent</artifactId>\n        <version>{old}</version>",
                    f"<artifactId>spring-boot-starter-parent</artifactId>\n        <version>{new}</version>")
    if name == "document-svc":
        repo.modify(path, "F-13b", "<description>Document metadata; stores binaries in DOCSTOR</description>",
                    "<description>Document metadata; stores binaries in Evidence Vault (formerly DOCSTOR)</description>")
    if name == NEW_RESERVE:
        repo.modify(path, "CM-04",
                    f"<artifactId>{OLD_RESERVE}</artifactId>\n    <version>1.0.0-SNAPSHOT</version>\n    <name>{OLD_RESERVE}</name>",
                    f"<artifactId>{NEW_RESERVE}</artifactId>\n    <version>1.0.0-SNAPSHOT</version>\n    <name>{NEW_RESERVE}</name>")


# ---------------------------------------------------------------------------------------------
# application.yaml
# ---------------------------------------------------------------------------------------------

def yaml_list(items, indent):
    if not items:
        return " []\n"
    pad = " " * indent
    return "\n" + "".join(f"{pad}- {x}\n" for x in items)


def app_yaml(name: str) -> str:
    s = SVC[name]
    topics = s["kafka_topics"]
    consumes = [t for t in topics["consumes"] if t != "notification.fraud-notice.sent.v1"]
    produces = [t for t in topics["produces"] if t != "notification.fraud-notice.sent.v1"]
    head = T("""
        # @@name@@ - Claims Hub service configuration (profile-independent defaults).
        # Secrets are injected at deploy time from the platform secret store; never commit values.
        spring:
          application:
            name: @@name@@
          datasource:
            url: jdbc:postgresql://${DB_HOST:localhost}:5432/@@db@@
            username: ${DB_USER}
            password: ${DB_PASSWORD}
          jpa:
            open-in-view: false
            hibernate:
              ddl-auto: validate
          kafka:
            bootstrap-servers: ${KAFKA_BOOTSTRAP_SERVERS}
            consumer:
              group-id: @@name@@
              auto-offset-reset: earliest

        server:
          port: 8080

        management:
          endpoints:
            web:
              exposure:
                include: health,info,prometheus

        chub:
          kafka:
            cluster: esp-prd
    """, name=name, db=database(name))
    body = "    consumes:" + yaml_list(consumes, 6) + "    produces:" + yaml_list(produces, 6)
    tables = "  postgres-tables:" + yaml_list(s["postgres_tables"], 4)
    extra = extra_yaml(name)
    return head + body + tables + ("\n" + extra if extra else "")


def extra_yaml(name: str) -> str:
    if name == "triage-svc":
        return T("""

            sentinel:
              base-url: https://sentinel.corvane.internal
              # ADR-013: synchronous REST scoring; on timeout fall back to batch scoring
              timeout-ms: 800

            triage:
              tier-rule: BR-TRI-003
        """)
    if name == NEW_RESERVE:
        return T("""

            reserve:
              # BR-RSV-007 v3 (effective 2026-07-01), CHUB-322
              tier3-review-days: 14
              large-loss-threshold-gbp: 250000
              # ADR-028 / DEC-005: revaluations are posted as RV reserve movements
              revaluation:
                movement-type: RV
                rate-source: GROUP_LEDGER_MONTH_END
        """)
    if name == "fraud-referral-svc":
        return T("""

            referral:
              # ADR-020: effective-dated thresholds for BR-FRD-031 (Sentinel score 0-100)
              threshold.default: 65
              threshold.tier3: 60
              threshold.tier3.effective-from: 2026-10-01
              siu:
                # BR-FRD-035 v2
                triage-business-days: 3

            notice:
              # BR-FRD-032 v2 (NISA Circular 2026/04): written notice within 10 business days of referral
              business-days: 10
              # BR-FRD-036: deferral where SIU certifies a tipping-off risk
              max-deferral-days: 60

            auto-decline:
              # BR-FRD-033: no decline on the score alone
              enabled: false
        """)
    if name == "notification-svc":
        return T("""

            notify:
              base-url: ${NOTIFY_BASE_URL}
              # ADR-014: fraud-referral notices use Notify templates
              templates:
                fraud-notice-letter: FRN01
                fraud-notice-sms: FRN02

            notice:
              business-days: 10
              holiday-calendars: [UK, NO, SE, DK]
        """)
    if name == "payment-orchestrator":
        return T("""

            cpg:
              base-url: ${CPG_BASE_URL}
              # CLX-IF-038: ISO 20022 pain.001 JSON mapping
              instruction-format: pain.001
              # ADR-021 (after INC-2026-0914): every instruction carries an idempotency key
              idempotency:
                header: Idempotency-Key
                key-source: payment_id
        """)
    if name == "document-svc":
        return T("""

            evidence-vault:
              # Evidence Vault (formerly DOCSTOR), ADR-009: binaries never stored in this database
              base-url: ${EVIDENCE_VAULT_BASE_URL}
              upload: multipart
        """)
    if name == "reporting-feed-svc":
        return T("""

            reporting:
              target: NISA Reporting Hub
              returns: [TP2, FR1, CT1]
        """)
    if name == "gl-posting-svc":
        return T("""

            group-ledger:
              base-url: ${GROUP_LEDGER_BASE_URL}
              # CLX-IF-050: journals posted hourly
              posting-schedule: hourly
        """)
    if name == "claim-core-svc":
        return T("""

            policy-api:
              # CLX-IF-054: PALM policy API
              base-url: ${PALM_POLICY_API_URL}
        """)
    return ""


def yaml_mods(repo, name, path, text):
    if name == NEW_RESERVE:
        repo.modify(path, "CM-04", f"  application:\n    name: {OLD_RESERVE}", f"  application:\n    name: {NEW_RESERVE}")
        repo.modify(path, "CM-04", f"      group-id: {OLD_RESERVE}", f"      group-id: {NEW_RESERVE}")
        repo.modify(path, "CM-04", "    produces:\n      - reserve.changed.v1\n", "    produces:\n      - reserve.changed.v2\n")
        repo.modify(path, "F-14", "    consumes:\n      - triage.completed.v1\n",
                    "    consumes:\n      - claims.reserve.movement.v1\n      - triage.completed.v1\n")
        repo.modify(path, "CM-06", "  # BR-RSV-007 v2\n  tier3-review-days: 21\n",
                    "  # BR-RSV-007 v3 (effective 2026-07-01), CHUB-322\n  tier3-review-days: 14\n")
        repo.modify(path, "F-17", "  large-loss-threshold-gbp: 250000\n",
                    "  large-loss-threshold-gbp: 250000\n"
                    "  # ADR-028 / DEC-005: revaluations are posted as RV reserve movements\n"
                    "  revaluation:\n    movement-type: RV\n    rate-source: GROUP_LEDGER_MONTH_END\n")
    if name in ("gl-posting-svc", "reporting-feed-svc"):
        repo.modify(path, "CM-04", "      - reserve.changed.v1\n", "      - reserve.changed.v2\n")
    if name == "triage-svc":
        repo.modify(path, "F-12", "  # synchronous REST scoring; on timeout fall back to batch scoring\n",
                    "  # ADR-013: synchronous REST scoring; on timeout fall back to batch scoring\n")
    if name == "fraud-referral-svc":
        repo.modify(path, "CM-08", "  threshold.default: 65\n  siu:",
                    "  threshold.default: 65\n  threshold.tier3: 60\n  threshold.tier3.effective-from: 2026-10-01\n  siu:")
        at16 = repo.text_at(path, "F-16")
        block = at16[at16.index("\nreferral:\n"):]
        repo.modify(path, "F-16", "      - fraud.referral.notice-due.v1\n" + tables_tail(name),
                    "      - fraud.referral.notice-due.v1\n" + tables_tail(name) + block)
    if name == "notification-svc":
        repo.modify(path, "F-18", "      - fnol.received.v1\n    produces:",
                    "      - fnol.received.v1\n      - fraud.referral.notice-due.v1\n    produces:")
        start = text.index("\nnotify:\n")
        repo.modify(path, "F-18", tables_tail(name), tables_tail(name) + text[start:])
    if name == "payment-orchestrator":
        idem = ("  # ADR-021 (after INC-2026-0914): every instruction carries an idempotency key\n"
                "  idempotency:\n    header: Idempotency-Key\n    key-source: payment_id\n")
        repo.modify(path, "CM-07", "  instruction-format: pain.001\n", "  instruction-format: pain.001\n" + idem)
    if name == "document-svc":
        repo.modify(path, "F-13b",
                    "docstor:\n  # DOCSTOR document store, ADR-009: binaries never stored in this database\n"
                    "  base-url: ${DOCSTOR_BASE_URL}\n",
                    "evidence-vault:\n  # Evidence Vault (formerly DOCSTOR), ADR-009: binaries never stored in this database\n"
                    "  base-url: ${EVIDENCE_VAULT_BASE_URL}\n")


def tables_tail(name):
    return "  postgres-tables:" + yaml_list(SVC[name]["postgres_tables"], 4)


# ---------------------------------------------------------------------------------------------
# README.md
# ---------------------------------------------------------------------------------------------

README_TYPOS = {  # service -> (typo, fixed) introduced at creation, fixed by F-13
    "assessment-svc": ("recieves", "receives"),
    "gl-posting-svc": ("seperate", "separate"),
    "settlement-svc": ("occured", "occurred"),
    "reporting-feed-svc": ("enviroment", "environment"),
}

INTRO = [
    "This module is part of the Claims Hub monorepo and is built and deployed independently.",
    "The service is a Spring Boot application packaged as a container image and deployed to OpenShift.",
    "Like every Claims Hub service it owns its own PostgreSQL database (ADR-003) and talks to other services through Kafka events (ADR-002).",
    "It follows the Claims Hub service template: REST for synchronous calls, Kafka for domain events, one database per service.",
]
LOCAL = [
    "Run `make build SERVICE={n}` from the repository root, or `mvn -pl services/{n} verify` if you prefer Maven directly.",
    "From the repository root, `make test SERVICE={n}` runs the unit tests; integration tests need a local PostgreSQL and Kafka.",
    "Build locally with `mvn -f services/{n}/pom.xml package`; the Makefile target `make build SERVICE={n}` does the same.",
]


def readme(name: str) -> str:
    s = SVC[name]
    r = rng(f"readme:{name}")
    lines = [f"# {name}", "", s["description"] + ".", "", r.choice(INTRO), ""]
    lines += ["## Status", "", f"- Status: {s['status']}", f"- Go-live: {s['go_live']}",
              f"- Kubernetes namespace: `{s['k8s_namespace']}`", f"- Replicas (prod): {s['replicas']}",
              f"- Image: `{s['image']}`", f"- Terraform module: `{s['terraform_module']}`", ""]
    lines += ["## API", "", "| Method | Path | Summary |", "|---|---|---|"]
    for a in s["apis"]:
        summ = a["summary"].replace("(CLM-UK-2025-118204 format)", "(CLM-<region>-<yyyy>-<6 digits>)")
        lines.append(f"| {a['method']} | `{a['path']}` | {summ} |")
    lines.append("")
    topics = s["kafka_topics"]
    cons = [t for t in topics["consumes"] if t != "notification.fraud-notice.sent.v1"]
    prod = [t for t in topics["produces"] if t != "notification.fraud-notice.sent.v1"]
    lines += ["## Events", ""]
    lines.append("Produces: " + (", ".join(f"`{t}`" for t in prod) if prod else "none") + ".")
    lines.append("")
    lines.append("Consumes: " + (", ".join(f"`{t}`" for t in cons) if cons else "none") + ".")
    lines += ["", "## Data", ""]
    lines.append(f"Database `{database(name)}` with tables " + ", ".join(f"`{t}`" for t in s["postgres_tables"]) + ".")
    lines += ["", "## CLARA programs replaced", ""]
    lines.append(", ".join(s["replaces_programs"]) + ".")
    lines += ["", "## Building", "", r.choice(LOCAL).format(n=name), ""]
    lines += ["## Ownership", "", "Code owners are defined in `/.github/CODEOWNERS`.", ""]
    text = "\n".join(lines)
    if name in README_TYPOS:
        typo, fixed = README_TYPOS[name]
        text = text.replace("## Building\n\n", f"## Building\n\nThe service {fixed} its configuration from the "
                                                f"deployment environment.\n", 1)
    return text


def readme_mods(repo, name, path, text):
    if name in README_TYPOS:
        typo, fixed = README_TYPOS[name]
        repo.modify(path, "F-13", f"The service {typo} its configuration", f"The service {fixed} its configuration")
    if name == NEW_RESERVE:
        repo.modify(path, "CM-04", f"# {OLD_RESERVE}\n", f"# {NEW_RESERVE}\n")
        for old, new in ((f"`{SVC[name]['terraform_module'].replace(NEW_RESERVE, OLD_RESERVE)}`", f"`{SVC[name]['terraform_module']}`"),
                         (f"`{SVC[name]['image'].replace(NEW_RESERVE, OLD_RESERVE)}`", f"`{SVC[name]['image']}`"),
                         ("Produces: `reserve.changed.v1`.", "Produces: `reserve.changed.v2`."),
                         (f"make build SERVICE={OLD_RESERVE}", f"make build SERVICE={NEW_RESERVE}"),
                         (f"services/{OLD_RESERVE}", f"services/{NEW_RESERVE}")):
            if new in text:
                repo.modify(path, "CM-04", old, new)
        repo.modify(path, "F-14", "Consumes: `triage.completed.v1`.",
                    "Consumes: `claims.reserve.movement.v1`, `triage.completed.v1`.")
    if name in ("gl-posting-svc", "reporting-feed-svc"):
        repo.modify(path, "CM-04", "`reserve.changed.v1`", "`reserve.changed.v2`")
    if name == "notification-svc":
        repo.modify(path, "F-18", "Consumes: `fnol.received.v1`.", "Consumes: `fnol.received.v1`, `fraud.referral.notice-due.v1`.")
    if name == "document-svc":
        repo.modify(path, "F-13b", "stores binaries in DOCSTOR.", "stores binaries in Evidence Vault (formerly DOCSTOR).")
    if name == NEW_RESERVE:
        row = "| POST | `/revaluation-runs` | Trigger a currency revaluation run (replaces CLRGL090) |\n"
        prev = "| GET | `/reserves/{claimId}/history` | Reserve movement history |\n"
        repo.modify(path, "F-17", prev, prev + row)


# ---------------------------------------------------------------------------------------------
# Java
# ---------------------------------------------------------------------------------------------

def application_java(name: str) -> str:
    return T("""
        package com.corvane.chub.@@pkg@@;

        import java.util.List;
        import org.springframework.boot.SpringApplication;
        import org.springframework.boot.autoconfigure.SpringBootApplication;
        import org.springframework.boot.context.properties.ConfigurationProperties;
        import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

        /**
         * Entry point for @@name@@.
         */
        @SpringBootApplication
        @ConfigurationPropertiesScan
        public class @@cls@@ {

            public static void main(String[] args) {
                SpringApplication.run(@@cls@@.class, args);
            }

            /** Topics this service consumes and produces, bound from {@code chub.kafka.*}. */
            @ConfigurationProperties(prefix = "chub.kafka")
            public record KafkaTopics(String cluster, List<String> consumes, List<String> produces) {
            }
        }
    """, pkg=PKG[name], name=name, cls=APP_CLASS[name])


TIER_CLASSIFIER = """
package com.corvane.chub.triage;

import java.math.BigDecimal;
import java.util.Map;
import org.springframework.stereotype.Component;

/**
 * Claim tier classification, BR-TRI-003 v3 (approved 2024-11-26, effective 2025-01-01).
 *
 * <p>Tier-3 if any trigger applies: estimated incurred at or above the currency threshold,
 * any bodily injury, solicitor or litigation involvement at notification, or a property
 * total loss. Tier-2 covers incurred from the GBP Tier-2 floor or any third-party
 * involvement. Everything else is Tier-1.
 *
 * <p>Tiering is owned by triage-svc (ADR-030); other services call the triage API rather
 * than re-implementing these constants.
 */
@Component
public class TierClassifier {

    // --- BR-TRI-003 v3 thresholds -------------------------------------------------------
    static final BigDecimal TIER3_MIN_GBP = new BigDecimal("50000");
    static final BigDecimal TIER3_MIN_NOK = new BigDecimal("650000");
    static final BigDecimal TIER3_MIN_SEK = new BigDecimal("680000");
    static final BigDecimal TIER3_MIN_DKK = new BigDecimal("430000");
    static final BigDecimal TIER2_MIN_GBP = new BigDecimal("5000");

    private static final Map<String, BigDecimal> TIER3_MIN = Map.of(
            "GBP", TIER3_MIN_GBP,
            "NOK", TIER3_MIN_NOK,
            "SEK", TIER3_MIN_SEK,
            "DKK", TIER3_MIN_DKK);

    public Tier classify(TriageInput in) {
        BigDecimal floor = TIER3_MIN.get(in.currency());
        if (floor == null) {
            throw new IllegalArgumentException("Unsupported claim currency " + in.currency());
        }
        if (in.estimatedIncurred().compareTo(floor) >= 0
                || in.bodilyInjury()
                || in.litigationAtNotification()
                || in.propertyTotalLoss()) {
            return Tier.TIER_3;
        }
        if (in.estimatedIncurredGbp().compareTo(TIER2_MIN_GBP) >= 0 || in.thirdPartyInvolved()) {
            return Tier.TIER_2;
        }
        return Tier.TIER_1;
    }

    public enum Tier { TIER_1, TIER_2, TIER_3 }

    public record TriageInput(String claimId,
                              String currency,
                              BigDecimal estimatedIncurred,
                              BigDecimal estimatedIncurredGbp,
                              boolean bodilyInjury,
                              boolean litigationAtNotification,
                              boolean propertyTotalLoss,
                              boolean thirdPartyInvolved) {
    }
}
"""

TIER_TEST = """
package com.corvane.chub.triage;

import static org.assertj.core.api.Assertions.assertThat;

import java.math.BigDecimal;
import org.junit.jupiter.api.Test;

class TierClassifierTest {

    private final TierClassifier classifier = new TierClassifier();

    private static TierClassifier.TriageInput input(String ccy, String amount, String gbp) {
        return new TierClassifier.TriageInput("CLM-TEST-0001", ccy, new BigDecimal(amount), new BigDecimal(gbp),
                false, false, false, false);
    }

    @Test
    void gbpClaimAtTheTier3FloorIsTier3() {
        assertThat(classifier.classify(input("GBP", "50000", "50000"))).isEqualTo(TierClassifier.Tier.TIER_3);
    }

    @Test
    void gbpClaimJustBelowTheFloorIsTier2() {
        assertThat(classifier.classify(input("GBP", "49999", "49999"))).isEqualTo(TierClassifier.Tier.TIER_2);
    }

    @Test
    void nordicThresholdsAreInLocalCurrency() {
        assertThat(classifier.classify(input("NOK", "650000", "48000"))).isEqualTo(TierClassifier.Tier.TIER_3);
        assertThat(classifier.classify(input("SEK", "679999", "49000"))).isEqualTo(TierClassifier.Tier.TIER_2);
        assertThat(classifier.classify(input("DKK", "430000", "49500"))).isEqualTo(TierClassifier.Tier.TIER_3);
    }

    @Test
    void smallClaimWithoutTriggersIsTier1() {
        assertThat(classifier.classify(input("GBP", "1200", "1200"))).isEqualTo(TierClassifier.Tier.TIER_1);
    }
}
"""

WRITE_OFF = """
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
"""

WRITE_OFF_TEST = """
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
"""

NOTICE_SCHEDULER = """
package com.corvane.chub.notification;

import java.time.DayOfWeek;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

/**
 * Schedules the customer notice that follows a fraud referral (BR-FRD-032 v2, NISA Circular
 * 2026/04 section 3.2).
 *
 * <p>fraud-referral-svc publishes {@code fraud.referral.notice-due.v1} when a referral is
 * created. This class works out the latest date the written notice may go out: the referral
 * date plus ten business days, skipping weekends and the public holidays of the claim's
 * region. A deferral approved under BR-FRD-036 arrives as a later event and moves the date.
 * Letters use Notify template FRN01 and SMS uses FRN02 (ADR-014).
 */
@Component
public class FraudReferralNoticeScheduler {

    /** BR-FRD-032 v2: notice within 10 business days of the referral. */
    static final int NOTICE_BUSINESS_DAYS = 10;

    /** Holiday calendars used for business-day arithmetic. */
    static final List<String> CALENDAR_REGIONS = List.of("UK", "NO", "SE", "DK");

    private final Map<String, HolidayCalendar> calendars;
    private final NoticeQueue queue;

    public FraudReferralNoticeScheduler(Map<String, HolidayCalendar> calendars, NoticeQueue queue) {
        for (String region : CALENDAR_REGIONS) {
            if (!calendars.containsKey(region)) {
                throw new IllegalStateException("No holiday calendar for region " + region);
            }
        }
        this.calendars = calendars;
        this.queue = queue;
    }

    @KafkaListener(topics = "fraud.referral.notice-due.v1", groupId = "notification-svc")
    public void onNoticeDue(NoticeDueEvent event) {
        LocalDate due = dueDate(event.referralDate(), event.region());
        queue.schedule(event.referralId(), event.claimId(), due, event.deferredUntil());
    }

    /** Referral date plus {@value #NOTICE_BUSINESS_DAYS} business days in the claim's region. */
    public LocalDate dueDate(LocalDate referralDate, String region) {
        HolidayCalendar calendar = calendars.get(region);
        if (calendar == null) {
            throw new IllegalArgumentException("Unknown region " + region);
        }
        LocalDate d = referralDate;
        int counted = 0;
        while (counted < NOTICE_BUSINESS_DAYS) {
            d = d.plusDays(1);
            if (d.getDayOfWeek() == DayOfWeek.SATURDAY || d.getDayOfWeek() == DayOfWeek.SUNDAY) {
                continue;
            }
            if (calendar.isHoliday(d)) {
                continue;
            }
            counted++;
        }
        return d;
    }

    public interface HolidayCalendar {
        boolean isHoliday(LocalDate date);
    }

    public interface NoticeQueue {
        void schedule(String referralId, String claimId, LocalDate dueDate, LocalDate deferredUntil);
    }

    public record NoticeDueEvent(String referralId, String claimId, String region,
                                 LocalDate referralDate, LocalDate deferredUntil) {
    }
}
"""

REVALUATION_JOB = """
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
"""

MOVEMENT_LISTENER = """
package com.corvane.chub.reserve;

import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

/**
 * Consumes CLARA reserve movements republished by the MQ-to-Kafka bridge CLX-IF-049
 * (ADR-012): RSVMOVE records from CLX-IF-042, converted to Avro (schema v3) and keyed by
 * claim_id. Used for the reserve parallel run and for Wave 2 synchronisation.
 */
@Component
public class ReserveMovementListener {

    private final ReserveMovementService movements;

    public ReserveMovementListener(ReserveMovementService movements) {
        this.movements = movements;
    }

    @KafkaListener(topics = "claims.reserve.movement.v1", groupId = "reserve-engine-sync")
    public void onClaraMovement(ClaraReserveMovement movement) {
        movements.applyFromClara(movement);
    }

    public record ClaraReserveMovement(String claimId, String movementType, long amountMinor,
                                       String currency, int recVersion) {
    }
}
"""

TIER3_REVIEW = """
package com.corvane.chub.reserve;

import java.time.Clock;
import java.time.LocalDate;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

/**
 * Keeps reserve.review_schedule up to date for Tier-3 claims (BR-RSV-007). The cadence comes
 * from {@code reserve.tier3-review-days}; CLARA's CLRRS110 reads the same value from
 * CLR.T_PARAM (RSV_T3_REVIEW_DAYS), so both must be changed together.
 */
@Component
public class Tier3ReviewScheduler {

    private final ReviewScheduleRepository schedule;
    private final Clock clock;
    private final int cadenceDays;

    public Tier3ReviewScheduler(ReviewScheduleRepository schedule, Clock clock,
                                @Value("${reserve.tier3-review-days}") int cadenceDays) {
        this.schedule = schedule;
        this.clock = clock;
        this.cadenceDays = cadenceDays;
    }

    @KafkaListener(topics = "triage.completed.v1", groupId = "reserve-engine-review")
    public void onTriage(TriageCompleted event) {
        if (event.tier() == 3) {
            LocalDate next = LocalDate.now(clock).plusDays(cadenceDays);
            schedule.upsert(event.claimId(), next, cadenceDays);
        }
    }

    public record TriageCompleted(String claimId, int tier) {
    }
}
"""

THRESHOLD_POLICY_FINAL = """
package com.corvane.chub.fraud;

import java.time.LocalDate;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * Sentinel score cut-offs for fraud referral (BR-FRD-031), held as effective-dated
 * configuration rather than code (ADR-020). A claim is referred to SIU when its Sentinel
 * score reaches the threshold that applies on the scoring date. The score alone never
 * declines a claim (BR-FRD-033).
 */
@Component
public class ReferralThresholdPolicy {

    private final int defaultThreshold;
    private final int tier3Threshold;
    private final LocalDate tier3EffectiveFrom;

    public ReferralThresholdPolicy(@Value("${referral.threshold.default}") int defaultThreshold,
                                   @Value("${referral.threshold.tier3}") int tier3Threshold,
                                   @Value("${referral.threshold.tier3.effective-from}") LocalDate tier3EffectiveFrom) {
        this.defaultThreshold = defaultThreshold;
        this.tier3Threshold = tier3Threshold;
        this.tier3EffectiveFrom = tier3EffectiveFrom;
    }

    /** Threshold for a claim of the given tier scored on the given date. */
    public int thresholdFor(int tier, LocalDate scoredOn) {
        if (tier == 3 && !scoredOn.isBefore(tier3EffectiveFrom)) {
            return tier3Threshold;
        }
        return defaultThreshold;
    }

    public boolean shouldRefer(int sentinelScore, int tier, LocalDate scoredOn) {
        return sentinelScore >= thresholdFor(tier, scoredOn);
    }
}
"""

THRESHOLD_TEST = """
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
"""

NOTICE_CONTROLLER = """
package com.corvane.chub.fraud;

import java.time.LocalDate;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

/**
 * Records or defers the customer notice for a referral. The deadline is the referral date
 * plus 10 business days (BR-FRD-032); a deferral needs SIU certification of a tipping-off
 * risk (BR-FRD-036).
 */
@RestController
public class CustomerNoticeController {

    private final CustomerNoticeService notices;

    public CustomerNoticeController(CustomerNoticeService notices) {
        this.notices = notices;
    }

    @PostMapping("/referrals/{referralId}/customer-notice")
    public ResponseEntity<CustomerNoticeService.Notice> recordOrDefer(@PathVariable String referralId,
                                                                      @RequestBody NoticeRequest request) {
        return ResponseEntity.ok(notices.recordOrDefer(referralId, request.action(), request.deferUntil(),
                request.certifiedBy()));
    }

    public record NoticeRequest(String action, LocalDate deferUntil, String certifiedBy) {
    }
}
"""

PAYMENT_SERVICE_FINAL = """
package com.corvane.chub.payment;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Builds payment instructions for the Corvane Payments Gateway (CLX-IF-038, ISO 20022
 * pain.001 mapping) once a settlement is agreed and the payment is authorised (BR-STL-002)
 * and screened.
 */
@Service
public class PaymentInstructionService {

    static final String IDEMPOTENCY_HEADER = "Idempotency-Key";

    private final PaymentInstructionRepository instructions;
    private final CpgClient cpg;

    public PaymentInstructionService(PaymentInstructionRepository instructions, CpgClient cpg) {
        this.instructions = instructions;
        this.cpg = cpg;
    }

    @Transactional
    public PaymentInstruction submit(PaymentInstruction instruction) {
        instruction.setIdempotencyKey(idempotencyKey(instruction));
        instructions.save(instruction);
        // ADR-021: a retry after a CPG timeout re-sends the same key, so CPG drops the duplicate
        cpg.send(instruction, IDEMPOTENCY_HEADER, instruction.getIdempotencyKey());
        instruction.markSubmitted();
        return instruction;
    }

    static String idempotencyKey(PaymentInstruction instruction) {
        return "PAY-" + instruction.getPaymentId();
    }
}
"""

JOURNAL_LISTENER = """
package com.corvane.chub.gl;

import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

/**
 * Turns reserve, payment and recovery events into Group Ledger journal lines
 * (gl.journal_line). Lines are batched and posted to Group Ledger by the hourly
 * CLX-IF-050 job.
 */
@Component
public class JournalPostingListener {

    private final JournalLineRepository lines;
    private final AccountMapping accounts;

    public JournalPostingListener(JournalLineRepository lines, AccountMapping accounts) {
        this.lines = lines;
        this.accounts = accounts;
    }

    @KafkaListener(topics = "#{kafkaTopics.consumes()}", groupId = "gl-posting-svc")
    public void onEvent(FinanceEvent event) {
        lines.save(JournalLine.from(event, accounts.accountFor(event.type()), event.periodOf()));
    }
}
"""

CLAIM_CONTROLLER = """
package com.corvane.chub.claimcore;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * Claim aggregate API. Claim references have the form CLM-&lt;region&gt;-&lt;yyyy&gt;-&lt;6 digits&gt;;
 * migrated claims keep their CLARA CLAIM_ID in claim_core.claim.legacy_claim_id.
 */
@RestController
@RequestMapping("/claims")
public class ClaimController {

    private final ClaimService claims;

    public ClaimController(ClaimService claims) {
        this.claims = claims;
    }

    @GetMapping("/{claimId}")
    public ResponseEntity<ClaimView> get(@PathVariable String claimId) {
        return claims.find(claimId).map(ResponseEntity::ok).orElse(ResponseEntity.notFound().build());
    }

    @PostMapping
    public ResponseEntity<ClaimView> create(@RequestBody CreateClaimFromFnol request) {
        return ResponseEntity.status(201).body(claims.createFromFnol(request));
    }

    @PatchMapping("/{claimId}")
    public ResponseEntity<ClaimView> update(@PathVariable String claimId, @RequestBody ClaimPatch patch) {
        return ResponseEntity.ok(claims.update(claimId, patch));
    }
}
"""

FNOL_CONTROLLER = """
package com.corvane.chub.fnol;

import java.util.UUID;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

/**
 * First Notice of Loss intake. Every accepted FNOL is stored in fnol.notification and
 * published as fnol.received.v1 for triage-svc, claim-core-svc and notification-svc.
 */
@RestController
public class FnolController {

    private final FnolService fnol;

    public FnolController(FnolService fnol) {
        this.fnol = fnol;
    }

    @PostMapping("/fnol")
    public ResponseEntity<FnolReceipt> submit(@RequestBody FnolRequest request) {
        return ResponseEntity.accepted().body(fnol.accept(request));
    }

    @GetMapping("/fnol/{fnolId}")
    public ResponseEntity<FnolStatus> status(@PathVariable UUID fnolId) {
        return fnol.status(fnolId).map(ResponseEntity::ok).orElse(ResponseEntity.notFound().build());
    }
}
"""


def _strip(s):
    return s.lstrip("\n")


JTYPE = {"UUID": ("UUID", "java.util.UUID"), "VARCHAR": ("String", None), "CHAR": ("String", None),
         "NUMERIC": ("BigDecimal", "java.math.BigDecimal"), "DATE": ("LocalDate", "java.time.LocalDate"),
         "TIMESTAMP": ("OffsetDateTime", "java.time.OffsetDateTime"), "SMALLINT": ("short", None),
         "BIGINT": ("long", None), "BOOLEAN": ("boolean", None), "JSONB": ("String", None)}


def camel(s, upper=False):
    parts = s.split("_")
    out = parts[0] + "".join(p.capitalize() for p in parts[1:])
    return out[0].upper() + out[1:] if upper else out


def entity_java(name: str, table: str, cls: str) -> str:
    t = W.tables[table]
    schema, tname = table.split(".")
    imports = {"jakarta.persistence.Column", "jakarta.persistence.Entity", "jakarta.persistence.Id",
               "jakarta.persistence.Table"}
    fields, accessors = [], []
    pk = set(t["primary_key"])
    for c in t["columns"]:
        jt, imp = JTYPE[c["type"]]
        if imp:
            imports.add(imp)
        attrs = [f'name = "{c["name"]}"']
        if not c["nullable"]:
            attrs.append("nullable = false")
        if c["type"] in ("VARCHAR", "CHAR") and c.get("length"):
            attrs.append(f"length = {c['length']}")
        if c["type"] == "NUMERIC":
            attrs.append(f"precision = {c.get('length') or 13}, scale = {c.get('scale') or 2}")
        if c["type"] == "JSONB":
            attrs.append('columnDefinition = "jsonb"')
        ann = ("    @Id\n" if c["name"] in pk else "") + f"    @Column({', '.join(attrs)})\n"
        fields.append(f"    /** {c['description']}. */\n{ann}    private {jt} {camel(c['name'])};\n")
        getter = ("is" if jt == "boolean" else "get") + camel(c["name"], True)
        accessors.append(f"    public {jt} {getter}() {{\n        return {camel(c['name'])};\n    }}\n")
    imp = "".join(f"import {i};\n" for i in sorted(imports))
    return (f"package com.corvane.chub.{PKG[name]};\n\n{imp}\n"
            f"/**\n * JPA mapping of {table} in database {t['database']} (owned by {name}, ADR-003).\n */\n"
            f"@Entity\n@Table(schema = \"{schema}\", name = \"{tname}\")\npublic class {cls} {{\n\n"
            + "\n".join(fields) + "\n    protected " + cls + "() {\n    }\n\n" + "\n".join(accessors) + "}\n")


RESERVE_PUBLISHER = """
package com.corvane.chub.reserve;

import java.util.UUID;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

/**
 * Publishes the reserve change event after every committed reserve movement. The topic is the
 * single entry of {@code chub.kafka.produces}; gl-posting-svc and reporting-feed-svc consume it.
 */
@Component
public class ReserveChangedPublisher {

    private final KafkaTemplate<String, ReserveChanged> kafka;
    private final String topic;

    public ReserveChangedPublisher(KafkaTemplate<String, ReserveChanged> kafka,
                                   ReserveApplication.KafkaTopics topics) {
        this.kafka = kafka;
        this.topic = topics.produces().get(0);
    }

    public void published(Reserve reserve, UUID movementId, String movementType, long amountMinor) {
        kafka.send(topic, reserve.getClaimId(), new ReserveChanged(reserve.getClaimId(), reserve.getReserveId(),
                movementId, movementType, amountMinor, reserve.getCurrency()));
    }

    /** Amounts in minor units (pence / ore), original currency (ADR-016). */
    public record ReserveChanged(String claimId, UUID reserveId, UUID movementId, String movementType,
                                 long amountMinor, String currency) {
    }
}
"""


def build(repo):
    for name in [s["name"] for s in sorted(SVC.values(), key=lambda s: s["id"])]:
        base = f"services/{name}"
        created = SKELETON_COMMIT[name]
        author = W.services[name]["owner_history"][0]["person"]
        # pom
        p = repo.add(f"{base}/pom.xml", pom(name), created, author=author)
        pom_mods(repo, name, p.path)
        # README
        text = readme(name)
        if name == "document-svc":
            pass
        p = repo.add(f"{base}/README.md", text, created, author=author)
        readme_mods(repo, name, p.path, text)
        # application.yaml
        text = app_yaml(name)
        p = repo.add(f"{base}/src/main/resources/application.yaml", text, created, author=author)
        yaml_mods(repo, name, p.path, text)
        # Application class
        repo.add(f"{jbase(name)}/{APP_CLASS[name]}.java", application_java(name), created, author=author)

    # key classes -----------------------------------------------------------------------------
    repo.add(f"{jbase('triage-svc')}/TierClassifier.java", _strip(TIER_CLASSIFIER), "F-03", author="P040")
    repo.add(f"{tbase('triage-svc')}/TierClassifierTest.java", _strip(TIER_TEST), "F-12", author="P040")
    repo.add(f"{jbase('recovery-svc')}/WriteOffPolicy.java", _strip(WRITE_OFF), "F-11", author="P043")
    repo.add(f"{tbase('recovery-svc')}/WriteOffPolicyTest.java", _strip(WRITE_OFF_TEST), "F-11", author="P043")
    repo.add(f"{jbase('notification-svc')}/FraudReferralNoticeScheduler.java", _strip(NOTICE_SCHEDULER), "F-18",
             author="P040")
    repo.add(f"{jbase(NEW_RESERVE)}/ReserveRevaluationJob.java", _strip(REVALUATION_JOB), "F-17", author="P041")
    p = repo.add(f"{jbase(NEW_RESERVE)}/ReserveMovementListener.java", _strip(MOVEMENT_LISTENER), "F-14", author="P041")
    repo.modify(p.path, "CM-04", 'groupId = "reserve-svc-sync"', 'groupId = "reserve-engine-sync"')
    p = repo.add(f"{jbase(NEW_RESERVE)}/Tier3ReviewScheduler.java", _strip(TIER3_REVIEW), "F-04", author="P041")
    repo.modify(p.path, "CM-04", 'groupId = "reserve-svc-review"', 'groupId = "reserve-engine-review"')
    p = repo.add(f"{jbase('fraud-referral-svc')}/ReferralThresholdPolicy.java", _strip(THRESHOLD_POLICY_FINAL), "F-16",
                 author="P042")
    threshold_mods(repo, p.path)
    repo.add(f"{tbase('fraud-referral-svc')}/ReferralThresholdPolicyTest.java", _strip(THRESHOLD_TEST), "F-21",
             author="P042")
    repo.add(f"{jbase('fraud-referral-svc')}/CustomerNoticeController.java", _strip(NOTICE_CONTROLLER), "F-16",
             author="P042")
    p = repo.add(f"{jbase('payment-orchestrator')}/PaymentInstructionService.java", _strip(PAYMENT_SERVICE_FINAL),
                 "F-05", author="P042")
    payment_mods(repo, p.path)
    repo.add(f"{jbase('gl-posting-svc')}/JournalPostingListener.java", _strip(JOURNAL_LISTENER), "F-04", author="P041")
    p = repo.add(f"{jbase('claim-core-svc')}/ClaimController.java", _strip(CLAIM_CONTROLLER), "F-03", author="P040")
    format_mods(repo, p.path)
    repo.add(f"{jbase('fnol-intake-svc')}/FnolController.java", _strip(FNOL_CONTROLLER), "F-03", author="P040")
    p = repo.add(f"{jbase(NEW_RESERVE)}/Reserve.java", entity_java(NEW_RESERVE, "reserve.reserve", "Reserve"), "F-04",
                 author="P041")
    repo.modify(p.path, "CM-04", f"(owned by {OLD_RESERVE}, ADR-003)", f"(owned by {NEW_RESERVE}, ADR-003)")
    repo.add(f"{jbase(NEW_RESERVE)}/ReserveChangedPublisher.java", _strip(RESERVE_PUBLISHER), "F-04", author="P041")
    repo.add(f"{jbase('fraud-referral-svc')}/Referral.java", entity_java("fraud-referral-svc", "fraud.referral", "Referral"),
             "F-05", author="P042")


def threshold_mods(repo, path):
    repo.modify(
        path, "CM-08",
        "    private final int defaultThreshold;\n\n"
        "    public ReferralThresholdPolicy(@Value(\"${referral.threshold.default}\") int defaultThreshold) {\n"
        "        this.defaultThreshold = defaultThreshold;\n    }\n",
        "    private final int defaultThreshold;\n"
        "    private final int tier3Threshold;\n"
        "    private final LocalDate tier3EffectiveFrom;\n\n"
        "    public ReferralThresholdPolicy(@Value(\"${referral.threshold.default}\") int defaultThreshold,\n"
        "                                   @Value(\"${referral.threshold.tier3}\") int tier3Threshold,\n"
        "                                   @Value(\"${referral.threshold.tier3.effective-from}\") LocalDate tier3EffectiveFrom) {\n"
        "        this.defaultThreshold = defaultThreshold;\n"
        "        this.tier3Threshold = tier3Threshold;\n"
        "        this.tier3EffectiveFrom = tier3EffectiveFrom;\n    }\n")
    repo.modify(
        path, "CM-08",
        "    public int thresholdFor(int tier, LocalDate scoredOn) {\n        return defaultThreshold;\n    }\n",
        "    public int thresholdFor(int tier, LocalDate scoredOn) {\n"
        "        if (tier == 3 && !scoredOn.isBefore(tier3EffectiveFrom)) {\n"
        "            return tier3Threshold;\n        }\n        return defaultThreshold;\n    }\n")


def payment_mods(repo, path):
    repo.modify(
        path, "CM-07",
        "    @Transactional\n    public PaymentInstruction submit(PaymentInstruction instruction) {\n"
        "        instructions.save(instruction);\n"
        "        cpg.send(instruction);\n",
        "    @Transactional\n    public PaymentInstruction submit(PaymentInstruction instruction) {\n"
        "        instruction.setIdempotencyKey(idempotencyKey(instruction));\n"
        "        instructions.save(instruction);\n"
        "        // ADR-021: a retry after a CPG timeout re-sends the same key, so CPG drops the duplicate\n"
        "        cpg.send(instruction, IDEMPOTENCY_HEADER, instruction.getIdempotencyKey());\n")
    repo.modify(
        path, "CM-07",
        "        return instruction;\n    }\n}\n",
        "        return instruction;\n    }\n\n"
        "    static String idempotencyKey(PaymentInstruction instruction) {\n"
        "        return \"PAY-\" + instruction.getPaymentId();\n    }\n}\n")
    repo.modify(
        path, "CM-07",
        "public class PaymentInstructionService {\n\n    private final",
        "public class PaymentInstructionService {\n\n    static final String IDEMPOTENCY_HEADER = \"Idempotency-Key\";\n\n    private final")


def format_mods(repo, path):
    # F-19 normalised indentation / brace placement in a couple of places
    repo.modify(path, "F-19",
                "    public ClaimController(ClaimService claims)\n    {\n        this.claims = claims;\n    }\n",
                "    public ClaimController(ClaimService claims) {\n        this.claims = claims;\n    }\n")
