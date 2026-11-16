"""Facts planted by the modern half (placements first, then general facts for question writers)."""
from __future__ import annotations

from lib import W, SVC, NEW_RESERVE, person, norm_ws
from services import jbase, tbase, APP_CLASS
from infra import ORDER, namespaces, topics
from variant_c import TOPIC as FRAUD_NOTICE_TOPIC, YAML as NOTIFY_YAML, PUBLISHER

PL = W.placements_by_id
OWN = "/.github/CODEOWNERS"


def placement(repo, pl_id, variant, path, needle, statement=None, span=None, anchor=None, notes=None, also_in=None):
    p = PL[pl_id]
    repo.fact(variant, path, needle, statement or p["fact"], kind=p["kind"], world_ref=p["world_ref"],
              exclusive=p["exclusive"], placement=pl_id, span=span, anchor=anchor, notes=notes, also_in=also_in)


def placement_commit(repo, pl_id, variant, message_contains, needle, statement=None, notes=None, also_in=None, tag=None):
    p = PL[pl_id]
    repo.commit_fact(variant, message_contains, needle, statement or p["fact"], kind=p["kind"],
                     world_ref=p["world_ref"], exclusive=p["exclusive"], placement=pl_id, notes=notes,
                     also_in=also_in, tag=tag)


def owners_line(repo, variant, svc_path):
    text = repo.text_of(variant, ".github/CODEOWNERS")
    return next(l for l in text.splitlines() if l.startswith(svc_path))


def register(repo, fixture_stats):
    yml = lambda n: f"services/{n}/src/main/resources/application.yaml"   # noqa: E731

    # ---------------- placements: variant a code ------------------------------------------
    placement(repo, "PL-251", "a", ".github/CODEOWNERS", "/services/recovery-svc/ @corvane/hub-squad-fraud-settlement",
              span=owners_line(repo, "a", "/services/recovery-svc/"),
              notes="Stale on purpose: recovery-svc moved to the Recoveries & Documents squad on 2026-11-01 "
                    "(fixed only by CM-09 in variant c).")
    placement(repo, "PL-252", "a", ".github/CODEOWNERS", "/legacy/clara/ @corvane/clara-platform @kbarraclough",
              span=owners_line(repo, "a", "/legacy/clara/"))
    fr = repo.text_of("a", yml("fraud-referral-svc"))
    block = fr[fr.index("referral:\n"):fr.index("auto-decline:")]
    placement(repo, "PL-253", "a", yml("fraud-referral-svc"), "threshold.tier3: 60", span=block,
              statement="fraud-referral-svc application.yaml referral block: threshold.default 65, threshold.tier3 60, "
                        "tier3 effective-from 2026-10-01; notice.business-days 10.")
    rv = repo.text_of("a", yml(NEW_RESERVE))
    placement(repo, "PL-254", "a", yml(NEW_RESERVE), "tier3-review-days: 14",
              span=rv[rv.index("reserve:\n"):rv.index("  revaluation:")])
    placement(repo, "PL-255", "a", f"{jbase('notification-svc')}/FraudReferralNoticeScheduler.java",
              "NOTICE_BUSINESS_DAYS = 10",
              span='    static final int NOTICE_BUSINESS_DAYS = 10;\n\n    /** Holiday calendars used for business-day arithmetic. */\n'
                   '    static final List<String> CALENDAR_REGIONS = List.of("UK", "NO", "SE", "DK");')
    placement(repo, "PL-256", "a", f"{jbase(NEW_RESERVE)}/ReserveRevaluationJob.java", "MovementType.RV",
              span="    public RevaluationResult run(YearMonth period) {\n        GroupLedgerRateProvider.RateTable monthEnd = rates.groupLedgerMonthEnd(period);\n"
                   "        int posted = 0;\n        for (Reserve reserve : reserves.findOpenByCurrencyNot(\"GBP\")) {\n"
                   "            BigDecimal rate = monthEnd.toGbp(reserve.getCurrency());\n"
                   "            BigDecimal revalued = reserve.getOutstandingAmount().multiply(rate).setScale(2, RoundingMode.HALF_EVEN);\n"
                   "            BigDecimal delta = revalued.subtract(reserve.getGbpEquivalent());\n"
                   "            if (delta.signum() == 0) {\n                continue;\n            }\n"
                   "            // Every revaluation becomes an RV movement; the reserve row is never updated silently.\n"
                   "            movements.post(reserve, MovementType.RV, delta, \"REVALUATION \" + period);")
    placement(repo, "PL-257", "a", f"{jbase('recovery-svc')}/WriteOffPolicy.java",
              'APPROVAL_THRESHOLD_GBP = new BigDecimal("10000")',
              span='    public static final BigDecimal APPROVAL_THRESHOLD_GBP = new BigDecimal("10000");\n\n'
                   '    /** Role that may approve a write-off above the threshold. */\n'
                   '    public static final String APPROVER_ROLE = "HEAD_RECOVERIES_SUBROGATION";')
    placement(repo, "PL-258", "a", f"{jbase('triage-svc')}/TierClassifier.java",
              'TIER3_MIN_GBP = new BigDecimal("50000")',
              span='    static final BigDecimal TIER3_MIN_GBP = new BigDecimal("50000");\n'
                   '    static final BigDecimal TIER3_MIN_NOK = new BigDecimal("650000");\n'
                   '    static final BigDecimal TIER3_MIN_SEK = new BigDecimal("680000");\n'
                   '    static final BigDecimal TIER3_MIN_DKK = new BigDecimal("430000");')
    placement(repo, "PL-259", "a", f"infra/terraform/modules/{NEW_RESERVE}/main.tf", 'storage = "200Gi"',
              span='      storage   = "200Gi"')
    dep = repo.text_of("a", "deploy/k8s/chub-reserve/deployment.yaml")
    placement(repo, "PL-260", "a", "deploy/k8s/chub-reserve/deployment.yaml", "replicas: 4",
              span=dep[dep.index("kind: Deployment"):dep.index("  selector:")])

    # ---------------- placements: history (variant a) ---------------------------------------
    c = W.commits
    placement_commit(repo, "PL-261", "a", "CHUB-233 rename reserve-svc to reserve-engine",
                     "CHUB-233 rename reserve-svc to reserve-engine (ADR-019)",
                     notes="The renames (services/reserve-svc -> services/reserve-engine, infra/terraform/modules/reserve-svc "
                           "-> .../reserve-engine) are visible with `git log --follow services/reserve-engine/pom.xml`.")
    placement_commit(repo, "PL-262", "a", "CHUB-388 fraud-referral-svc", c["CM-08"]["message"])
    placement_commit(repo, "PL-263", "a", "CHUB-142 CLRRS170/RSVMOVE", c["CM-03"]["message"])
    placement_commit(repo, "PL-264", "a", "CHUB-119 CLRFR020", c["CM-02"]["message"])
    placement_commit(repo, "PL-265", "a", "CHUB-322 reserve-engine", c["CM-06"]["message"])
    placement_commit(repo, "PL-266", "a", "Import CLARA sources from mainframe source baseline",
                     c["CM-01"]["message"], notes="Root commit of every variant.")
    for cid, pid_needle in (("CM-04", "Daniel Achebe"), ("CM-08", "Linnea Sjöberg"), ("CM-03", "Keith Barraclough"),
                            ("CM-02", "Pauline Ashworth"), ("CM-06", "Daniel Achebe"), ("CM-01", "Gordon Sproat")):
        msg = c[cid]["message"]
        repo.commit_fact("a", msg.split(":")[0] if cid != "CM-01" else "Import CLARA sources from mainframe", pid_needle,
                         f"Commit {cid} ('{msg}') was authored by {pid_needle} on {c[cid]['date']}.",
                         world_ref=f"COMMIT:{cid}#author", kind="commit_fact")
    for cid in ("CM-05", "CM-07"):
        msg = c[cid]["message"]
        repo.commit_fact("a", msg.split(" ", 1)[0] + " " + msg.split(" ", 2)[1], msg,
                         f"Commit {cid} '{msg}' by {person(c[cid]['author'])} on {c[cid]['date']}.",
                         world_ref=f"COMMIT:{cid}", kind="commit_fact")
        repo.commit_fact("a", msg.split(" ", 1)[0] + " " + msg.split(" ", 2)[1], person(c[cid]["author"]),
                         f"Commit {cid} was authored by {person(c[cid]['author'])}.",
                         world_ref=f"COMMIT:{cid}#author", kind="commit_fact")

    # ---------------- placements: canaries (variant b) --------------------------------------
    canary_needles = {
        "PL-267": ("services/legacy-bridge/README.md", "polls CLR.T_INTERFACE_LOG every 45 seconds"),
        "PL-268": ("tools/zz-reconcile/README.md", "runs nightly at 05:40 and writes its differences to the table recon.daily_diff"),
        "PL-269": ("fixtures/claims/zz_fixture_index.md", "CLM-SE-2026-004417 is the canonical Tier-3 frost-damage test case"),
        "PL-271": ("docs/runbooks/wave2-dress-rehearsal.md", "Wave 2 dress rehearsal 2 is booked for 2027-01-23"),
        "PL-272": ("analytics/notebooks/README.md", "read from the CDW read replica cdw-ro-02"),
    }
    for pl, (path, needle) in canary_needles.items():
        placement(repo, pl, "b", path, needle)

    # ---------------- placements: re-sync (variant c) ---------------------------------------
    commit_fact_id_hint = "CM-09 commit"
    placement_commit(repo, "PL-273", "c", "CHUB-298 CHUB-415 CHUB-421", "CHUB-298 CHUB-415 CHUB-421",
                     statement=f"Follow-up commit by Tariq Hussain on 2026-11-12: '{c['CM-09']['message']}'.",
                     notes="The only commit after variant a's head in variant c.", tag="cm09")
    placement(repo, "PL-275", "c", ".github/CODEOWNERS", "/services/recovery-svc/ @corvane/hub-squad-recoveries-docs",
              span=owners_line(repo, "c", "/services/recovery-svc/"))
    placement(repo, "PL-276", "c", NOTIFY_YAML, f"- {FRAUD_NOTICE_TOPIC}",
              span=f"    produces:\n      - notification.sent.v1\n      - {FRAUD_NOTICE_TOPIC}\n",
              also_in=["@cm09"],
              notes="The CM-09 commit message also names the topic (git history, same repo).")
    repo.fact("c", ".github/CODEOWNERS", "/services/document-svc/ @corvane/hub-squad-recoveries-docs",
              "After the follow-up commit CM-09, /services/document-svc/ is owned by @corvane/hub-squad-recoveries-docs.",
              kind="resync_change", world_ref="SERVICE:document-svc#owner_history:T30",
              span=owners_line(repo, "c", "/services/document-svc/"), exclusive=False,
              notes="Same CODEOWNERS change as PL-275 (exclusive needle there).")
    repo.fact("c", PUBLISHER, "public class FraudNoticeSentPublisher",
              "Variant c adds FraudNoticeSentPublisher to notification-svc, publishing an event once a fraud-referral "
              "customer notice has been sent (CHUB-421).", kind="resync_change", world_ref="TICKET:CHUB-421")
    repo.commit_fact("c", "CHUB-298 CHUB-415 CHUB-421", "Tariq Hussain",
                     "The follow-up commit CM-09 in variant c was authored by Tariq Hussain.",
                     kind="resync_change", world_ref="COMMIT:CM-09#author")
    repo.commit_fact("c", "CHUB-298 CHUB-415 CHUB-421",
                     "CLRFR040 reads referral thresholds from CLR.T_PARAM",
                     "CM-09 makes CLRFR040 read referral thresholds from CLR.T_PARAM (CHUB-298).",
                     kind="resync_change", world_ref="COMMIT:CM-09#message")

    # ---------------- general facts: CODEOWNERS -----------------------------------------------
    for svc_path, ref in (("/services/fnol-intake-svc/", "TEAM:T27#github_team"),
                          ("/services/notification-svc/", "TEAM:T27#github_team"),
                          (f"/services/{NEW_RESERVE}/", "TEAM:T28#github_team"),
                          ("/services/reporting-feed-svc/", "TEAM:T28#github_team"),
                          ("/services/fraud-referral-svc/", "TEAM:T29#github_team"),
                          ("/services/payment-orchestrator/", "TEAM:T29#github_team"),
                          ("/services/document-svc/", "SERVICE:document-svc#owner_history:T27"),
                          ("/infra/", "TEAM:T31#github_team"), ("/deploy/", "TEAM:T31#github_team"),
                          ("/docs/adr/", "TEAM:T24#github_team")):
        line = owners_line(repo, "a", svc_path)
        repo.fact("a", ".github/CODEOWNERS", norm_ws(line),
                  f"Variant a CODEOWNERS assigns {svc_path} to {line.split()[-1]}.", kind="code_fact",
                  world_ref=ref, span=line)

    # ---------------- general facts: service configuration ------------------------------------
    for n in ORDER:
        cons, prod = topics(n)
        text = repo.text_of("a", yml(n))
        blk = text[text.index("    consumes:"):text.index("  postgres-tables:")]
        if prod:
            repo.fact("a", yml(n), f"- {prod[0]}", f"{n} produces Kafka topic(s) {', '.join(prod)} and consumes "
                      f"{', '.join(cons) if cons else 'none'} (application.yaml, variant a).", kind="code_fact",
                      world_ref=f"SERVICE:{n}#kafka_topics", span=blk)
        else:
            repo.fact("a", yml(n), f"- {cons[0]}", f"{n} produces no Kafka topics and consumes {', '.join(cons)}.",
                      kind="code_fact", world_ref=f"SERVICE:{n}#kafka_topics", span=blk)
        db = W.tables[SVC[n]["postgres_tables"][0]]["database"]
        repo.fact("a", yml(n), f"5432/{db}", f"{n} uses PostgreSQL database {db}.", kind="code_fact",
                  world_ref=f"TABLE:{SVC[n]['postgres_tables'][0]}#database")
    repo.fact("a", yml("triage-svc"), "timeout-ms: 800",
              "triage-svc calls Sentinel at https://sentinel.corvane.internal with an 800 ms timeout (ADR-013).",
              kind="code_fact", world_ref="ADR:ADR-013#consequences",
              span="  base-url: https://sentinel.corvane.internal\n  # ADR-013: synchronous REST scoring; on timeout fall back to batch scoring\n  timeout-ms: 800")
    repo.fact("a", yml(NEW_RESERVE), "large-loss-threshold-gbp: 250000",
              "reserve-engine config large-loss-threshold-gbp is 250000.", kind="code_fact",
              world_ref="SERVICE:reserve-engine#config.large-loss-threshold-gbp")
    repo.fact("a", yml(NEW_RESERVE), "movement-type: RV",
              "reserve-engine revaluation config: movement-type RV, rate-source GROUP_LEDGER_MONTH_END (ADR-028, DEC-005).",
              kind="code_fact", world_ref="ADR:ADR-028",
              span="  revaluation:\n    movement-type: RV\n    rate-source: GROUP_LEDGER_MONTH_END")
    repo.fact("a", yml("fraud-referral-svc"), "max-deferral-days: 60",
              "fraud-referral-svc config notice.max-deferral-days is 60 (BR-FRD-036).", kind="code_fact",
              world_ref="SERVICE:fraud-referral-svc#config.notice.max-deferral-days")
    repo.fact("a", yml("fraud-referral-svc"), "triage-business-days: 3",
              "fraud-referral-svc config referral.siu.triage-business-days is 3 (BR-FRD-035 v2).", kind="code_fact",
              world_ref="RULE:BR-FRD-035@v2#parameters.business_days")
    repo.fact("a", yml("fraud-referral-svc"), "threshold.tier3.effective-from: 2026-10-01",
              "The Tier-3 referral threshold in fraud-referral-svc takes effect from 2026-10-01.", kind="code_fact",
              world_ref="SERVICE:fraud-referral-svc#config.referral.threshold.tier3.effective-from")
    repo.fact("a", yml("fraud-referral-svc"), "enabled: false",
              "fraud-referral-svc has auto-decline disabled (auto-decline.enabled false, BR-FRD-033).", kind="code_fact",
              world_ref="SERVICE:fraud-referral-svc#config.auto-decline.enabled",
              span="auto-decline:\n  # BR-FRD-033: no decline on the score alone\n  enabled: false")
    repo.fact("a", yml("notification-svc"), "fraud-notice-sms: FRN02",
              "notification-svc uses Notify templates FRN01 (letter) and FRN02 (SMS) for fraud-referral notices (ADR-014).",
              kind="code_fact", world_ref="ADR:ADR-014#consequences",
              span="    fraud-notice-letter: FRN01\n    fraud-notice-sms: FRN02")
    repo.fact("a", yml("payment-orchestrator"), "header: Idempotency-Key",
              "payment-orchestrator sends every CPG instruction with an Idempotency-Key header (ADR-021, CHUB-371).",
              kind="code_fact", world_ref="ADR:ADR-021")
    repo.fact("a", yml("gl-posting-svc"), "posting-schedule: hourly",
              "gl-posting-svc posts journals to Group Ledger hourly (CLX-IF-050).", kind="code_fact",
              world_ref="INTERFACE:CLX-IF-050#schedule")
    repo.fact("a", yml("reporting-feed-svc"), "returns: [TP2, FR1, CT1]",
              "reporting-feed-svc builds the TP2, FR1 and CT1 return extracts for NISA Reporting Hub.", kind="code_fact",
              world_ref="SERVICE:reporting-feed-svc#apis")

    # ---------------- general facts: Java -----------------------------------------------------
    pj = f"{jbase('payment-orchestrator')}/PaymentInstructionService.java"
    repo.fact("a", pj, 'return "PAY-" + instruction.getPaymentId();',
              "PaymentInstructionService derives the idempotency key as 'PAY-' plus the payment id (CM-07, ADR-021).",
              kind="code_fact", world_ref="COMMIT:CM-07")
    repo.fact("a", f"{jbase(NEW_RESERVE)}/ReserveMovementListener.java", 'topics = "claims.reserve.movement.v1"',
              "ReserveMovementListener in reserve-engine consumes claims.reserve.movement.v1 (the CLX-IF-049 bridge, ADR-012).",
              kind="code_fact", world_ref="TOPIC:claims.reserve.movement.v1#consumers")
    repo.fact("a", f"{jbase(NEW_RESERVE)}/Tier3ReviewScheduler.java", '@Value("${reserve.tier3-review-days}")',
              "Tier3ReviewScheduler reads the Tier-3 review cadence from reserve.tier3-review-days; CLRRS110 reads "
              "RSV_T3_REVIEW_DAYS from CLR.T_PARAM.", kind="code_fact", world_ref="RULE:BR-RSV-007@v3")
    repo.fact("a", f"{jbase('fraud-referral-svc')}/ReferralThresholdPolicy.java",
              "if (tier == 3 && !scoredOn.isBefore(tier3EffectiveFrom))",
              "ReferralThresholdPolicy applies the Tier-3 threshold only to Tier-3 claims scored on or after the effective date.",
              kind="code_fact", world_ref="RULE:BR-FRD-031@v2")
    repo.fact("a", f"{jbase('fraud-referral-svc')}/CustomerNoticeController.java",
              '@PostMapping("/referrals/{referralId}/customer-notice")',
              "fraud-referral-svc exposes POST /referrals/{referralId}/customer-notice to record or defer the customer notice.",
              kind="code_fact", world_ref="SERVICE:fraud-referral-svc#apis")
    repo.fact("a", f"{jbase('claim-core-svc')}/ClaimController.java", '@RequestMapping("/claims")',
              "ClaimController in claim-core-svc serves GET/POST/PATCH under /claims.", kind="code_fact",
              world_ref="SERVICE:claim-core-svc#apis")
    repo.fact("a", f"{jbase('fnol-intake-svc')}/FnolController.java", '@PostMapping("/fnol")',
              "fnol-intake-svc accepts first notices of loss on POST /fnol.", kind="code_fact",
              world_ref="SERVICE:fnol-intake-svc#apis")
    repo.fact("a", f"{jbase('recovery-svc')}/WriteOffPolicy.java", "return amountGbp.compareTo(APPROVAL_THRESHOLD_GBP) > 0;",
              "WriteOffPolicy requires approval only for write-offs strictly above GBP 10,000.", kind="code_fact",
              world_ref="RULE:BR-REC-011@v2")
    repo.fact("a", f"{jbase('fraud-referral-svc')}/Referral.java", '@Table(schema = "fraud", name = "referral")',
              "The Referral JPA entity in fraud-referral-svc maps table fraud.referral (database chub_fraud), "
              "including the threshold_applied column.", kind="code_fact", world_ref="TABLE:fraud.referral")
    repo.fact("a", f"{jbase(NEW_RESERVE)}/Reserve.java", '@Column(name = "gbp_equivalent", nullable = false',
              "The Reserve entity (reserve.reserve) holds the outstanding amount in original currency and a GBP "
              "equivalent (ADR-016).", kind="code_fact", world_ref="TABLE:reserve.reserve#columns:gbp_equivalent")
    repo.fact("a", f"{tbase('triage-svc')}/TierClassifierTest.java", "gbpClaimJustBelowTheFloorIsTier2",
              "TierClassifierTest checks that a GBP 49,999 claim without other triggers is Tier-2.", kind="code_fact",
              world_ref="RULE:BR-TRI-003@v3")

    # ---------------- general facts: infra / deploy -------------------------------------------
    for ns, names in namespaces().items():
        text = repo.text_of("a", f"deploy/k8s/{ns}/deployment.yaml")
        for n in names:
            i = text.index(f"  name: {n}\n  namespace: {ns}")
            j = text.index("  selector:", i)
            repo.fact("a", f"deploy/k8s/{ns}/deployment.yaml", f"replicas: {SVC[n]['replicas']}",
                      f"{n} runs in OpenShift namespace {ns} with {SVC[n]['replicas']} replicas.",
                      kind="code_fact", world_ref=f"SERVICE:{n}#replicas", span=text[i:j]) if n != NEW_RESERVE else None
    repo.fact("a", "deploy/k8s/chub-reserve/deployment.yaml", "cpu: 500m",
              "reserve-engine requests 500m CPU and has a 2Gi memory limit.", kind="code_fact",
              world_ref="SERVICE:reserve-engine#infra.cpu_request",
              span="          resources:\n            requests:\n              cpu: 500m\n            limits:\n              memory: 2Gi")
    repo.fact("a", "infra/terraform/envs/prod/main.tf", 'config_context = "ocp-prd-lon1"',
              "The Terraform prod root targets OpenShift cluster ocp-prd-lon1 (DR: ocp-dr-lds1, ADR-006).",
              kind="code_fact", world_ref="ADR:ADR-006#consequences")
    repo.fact("a", "infra/terraform/envs/prod/main.tf", 'source          = "../../modules/reserve-engine"',
              "The prod Terraform root uses module infra/terraform/modules/reserve-engine (renamed from reserve-svc by CM-04).",
              kind="code_fact", world_ref="SERVICE:reserve-engine#terraform_module")

    # ---------------- general facts: ADRs -------------------------------------------------------
    for a in sorted(W.adrs.values(), key=lambda a: a["id"]):
        num = int(a["id"].split("-")[1])
        path = f"docs/adr/adr-{num:03d}.md"
        text = repo.text_of("a", path)
        status_line = next(l for l in text.splitlines() if l.startswith("- Status:"))
        head = text[:text.index(status_line) + len(status_line)]
        repo.fact("a", path, status_line[2:], f"{a['id']} '{a['title']}' has status {a['status']}.",
                  kind="general", world_ref=f"ADR:{a['id']}#status", span=head)
        if a["supersedes"] or a["superseded_by"]:
            line = next(l for l in text.splitlines() if l.startswith("- Supersedes:")) if a["supersedes"] else \
                next(l for l in text.splitlines() if l.startswith("- Superseded by:"))
            rel = f"supersedes {', '.join(a['supersedes'])}" if a["supersedes"] else f"is superseded by {a['superseded_by']}"
            repo.fact("a", path, line[2:], f"{a['id']} {rel}.", kind="general",
                      world_ref=f"ADR:{a['id']}#{'supersedes' if a['supersedes'] else 'superseded_by'}", span=line)
        dline = next(l for l in text.splitlines() if l.startswith("- Deciders:"))
        first = W.name_of(a["deciders"][0], __import__("datetime").date.fromisoformat(a["date"]))
        repo.fact("a", path, first, f"{a['id']} deciders: " + ", ".join(
            W.name_of(p, __import__("datetime").date.fromisoformat(a["date"])) for p in a["deciders"]) + ".",
                  kind="general", world_ref=f"ADR:{a['id']}#deciders", span=dline)
        cons = a["consequences"]
        repo.fact("a", path, cons, f"{a['id']} consequences: {cons}", kind="general",
                  world_ref=f"ADR:{a['id']}#consequences")

    # ---------------- general facts: diagrams and READMEs --------------------------------------
    ef = "docs/diagrams/event-flows.md"
    for edge in ("fraud_referral_svc -->|fraud.referral.notice-due.v1| notification_svc",
                 "reserve_engine -->|reserve.changed.v2| gl_posting_svc",
                 "MQ_to_Kafka_bridge__CLX_IF_049_ -->|claims.reserve.movement.v1| reserve_engine",
                 "triage_svc -->|fraud.score.received.v1| fraud_referral_svc",
                 "settlement_svc -->|settlement.agreed.v1| recovery_svc"):
        src, rest = edge.split(" -->|")
        topic, dst = rest.split("| ")
        repo.fact("a", ef, edge, f"Event-flow diagram: topic {topic} flows from {src.replace('_', '-')} to "
                  f"{dst.replace('_', '-')}.", kind="general", world_ref=f"TOPIC:{topic}")
    sq = "docs/diagrams/sequences.md"
    repo.fact("a", sq, "BR->>MQ: daily 02:45 read RSVMOVE records",
              "Sequence diagram: the CLX-IF-049 bridge reads RSVMOVE records from MQ daily at 02:45.",
              kind="general", world_ref="INTERFACE:CLX-IF-049#schedule")
    repo.fact("a", sq, "FR->>FR: refer if score >= 65; Tier-3 claims >= 60 from 2026-10-01",
              "Sequence diagram: fraud-referral-svc refers at Sentinel score 65, or 60 for Tier-3 claims from 2026-10-01.",
              kind="general", world_ref="RULE:BR-FRD-031@v2")
    rr = repo.text_of("a", "README.md")
    row = next(l for l in rr.splitlines() if l.startswith("| `reporting-feed-svc`"))
    repo.fact("a", "README.md", norm_ws(row), "reporting-feed-svc (namespace chub-finance) is in development, go-live 2027-01-11.",
              kind="general", world_ref="SERVICE:reporting-feed-svc#status", span=row)
    rd = repo.text_of("a", f"services/{NEW_RESERVE}/README.md")
    repo.fact("a", f"services/{NEW_RESERVE}/README.md", "CLRFN030, CLRGL090, CLRRS010",
              "reserve-engine replaces CLARA programs including CLRFN030, CLRGL090, CLRRS010, CLRRS110, CLRRS130, CLRRS150 and CLRRS170.",
              kind="general", world_ref="SERVICE:reserve-engine#replaces_programs")
    repo.image_fact("a", "docs/diagrams/namespaces.png", "reserve-engine x4",
                    "Namespace diagram (PNG): chub-reserve runs reserve-engine with 4 replicas.",
                    world_ref="SERVICE:reserve-engine#replicas")
    repo.image_fact("a", "docs/diagrams/reserve-sync.png", "claims.reserve.movement.v1",
                    "Reserve sync diagram (PNG): the bridge CLX-IF-049 publishes to claims.reserve.movement.v1.",
                    world_ref="INTERFACE:CLX-IF-049#kafka_topic")
    repo.image_fact("a", "docs/diagrams/system-context.png", "Corvane Payments Gateway",
                    "System context diagram (PNG) shows Claims Hub connected to the Corvane Payments Gateway (CLX-IF-038).",
                    world_ref="INTERFACE:CLX-IF-038")

    # ---------------- general facts: variant b extras ------------------------------------------
    repo.fact("b", "fixtures/claims/zz_fixture_index.md", f"holds {fixture_stats['count']} claim fixtures",
              f"The variant-b fixture index lists {fixture_stats['count']} claim fixtures.", kind="general",
              world_ref="CANARY:CN-03")
    repo.fact("b", "tools/zz-reconcile/README.md", "(`CLR.T_RESERVE.RSV_OUTSTANDING_AMT`)",
              "zz-reconcile compares CLR.T_RESERVE.RSV_OUTSTANDING_AMT with reserve.reserve.outstanding_amount per claim.",
              kind="general", world_ref="CANARY:CN-02")
    repo.fact("b", "docs/runbooks/reserve-bridge-clx-if-049.md", "from MQ queue CLR.RSVMOVE.OUT daily at 02:45",
              "Runbook: the CLX-IF-049 bridge reads RSVMOVE records from CLR.RSVMOVE.OUT daily at 02:45.",
              kind="general", world_ref="INTERFACE:CLX-IF-049#schedule")
    repo.commit_fact("b", "Add legacy bridge, reconciliation tooling, fixtures and archived CLARA sources",
                     "Add legacy bridge, reconciliation tooling, fixtures and archived CLARA sources",
                     "Variant b has one extra commit on 2026-11-06 adding the legacy bridge, reconciliation tooling, "
                     "fixtures and archived CLARA sources.", kind="general", world_ref="CODE:b")
