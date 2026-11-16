#!/usr/bin/env python
"""End-to-end test of the baseline pipeline on a dummy corpus (no real corpus or questions needed).

Builds build/test_baseline/ from scratch:
    corpus/upload/...            3 small upload files (DOCX, CSV, MD), plus a dotfile and a .png to be skipped
    build/code_repo/variant_a/   a 2-commit git repo, plus an orphan branch whose content must NOT reach
                                 the sandbox
    questions/questions.yaml     3 questions (needle, code history, unanswerable)
then runs:
    questions_for_agent before the questions exist   -> clear error, exit 2
    prepare_sandbox with planted leaks (3 kinds)     -> exit 1 each
    prepare_sandbox                                  -> structure, git isolation, read-only corpus
    prepare_sandbox --check (cold/prepared)          -> passes clean; fails on modified/stray files
    questions_for_agent --batch-size 2 --label test  -> question files, plan, prompts, timings template
    hand-written batch answers + a synthetic transcript (batch 1) + batch totals (batch 2)
    timings_from_transcript, collect_results         -> sheet, score, efficiency; exact numbers checked
    override survives a re-collect; a fake product run; score.py compare

    .venv/bin/python -I baseline/test_pipeline.py          # exit 0 = all checks passed
"""
from __future__ import annotations

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import csv
import json
import os
import shutil
import subprocess

import yaml

Path = pathlib.Path
T = ROOT / "build" / "test_baseline"
SANDBOX = T / "build" / "baseline_sandbox"
RUN = T / "build" / "baseline_runs" / "test"
QFILE = T / "questions" / "questions.yaml"
RESULTS = T / "results"
PY = sys.executable

FAILS: list[str] = []


def check(cond: bool, msg: str) -> None:
    print(("  ok    " if cond else "  FAIL  ") + msg)
    if not cond:
        FAILS.append(msg)


def run(*args: str, expect: int = 0, quiet: bool = False) -> subprocess.CompletedProcess:
    cmd = [PY, "-I", *args] if args[0].endswith(".py") else list(args)
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    shown = " ".join(a.replace(str(ROOT) + "/", "") for a in cmd[2:] if a)
    if not quiet or r.returncode != expect:
        print(f"$ {shown}\n" + "\n".join("    " + ln for ln in (r.stdout + r.stderr).strip().splitlines()))
    check(r.returncode == expect, f"exit {r.returncode} (expected {expect}): {shown[:90]}")
    return r


def git(repo: Path, *args: str, date: str | None = None) -> str:
    env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1")
    if date:
        env.update(GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
    r = subprocess.run(["git", "-c", "user.name=Test Author", "-c", "user.email=author@corvane-mutual.example",
                        "-c", "commit.gpgsign=false", "-c", "init.defaultBranch=main", *args],
                       cwd=repo, capture_output=True, text=True, env=env, check=True)
    return r.stdout


def rm(path: Path) -> None:
    if path.exists():
        for dp, _, _ in os.walk(path):
            os.chmod(dp, 0o755)
        shutil.rmtree(path)


# ---------------------------------------------------------------------------------------------

def build_fixture() -> None:
    import docx  # noqa: PLC0415
    rm(T)
    up = T / "corpus" / "upload"
    for fam in ("long_docs", "structured", "text"):
        (up / fam).mkdir(parents=True)
    d = docx.Document()
    d.add_heading("Test reserve policy", 1)
    d.add_paragraph("1. Scope. This policy covers open claims.")
    d.add_paragraph("2. Reviews. Reserve reviews for Tier-3 claims take place every 14 days.")
    d.save(up / "long_docs" / "LD901_test_reserve_policy.docx")
    (up / "structured" / "ST901_test_vendor_register.csv").write_text(
        "vendor,city,rating\nNordlys Adjusting,Oslo,A\nKestrel Loss Partners,Leeds,B\n", encoding="utf-8")
    (up / "text" / "TX901_test_meeting_note.md").write_text(
        "# Steering note\n\nDecision: the Oslo pilot starts on 3 March 2026.\n", encoding="utf-8")
    (up / "text" / ".DS_Store").write_bytes(b"\x00\x01")
    (up / "text" / "TX902_diagram.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    repo = T / "build" / "code_repo" / "variant_a"
    repo.mkdir(parents=True)
    git(repo, "init", "-q")
    (repo / "README.md").write_text("# claims-api\n\nA test service.\n")
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("RATE_LIMIT = 100\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "Initial import", date="2026-01-05T10:00:00+00:00")
    (repo / "src" / "app.py").write_text("RATE_LIMIT = 50\n")
    git(repo, "commit", "-q", "-am", "CHUB-001: lower the rate limit to 50 requests", date="2026-02-10T10:00:00+00:00")
    git(repo, "checkout", "-q", "--orphan", "other")
    git(repo, "rm", "-rq", "--cached", ".")
    for p in ("README.md", "src/app.py"):
        (repo / p).unlink()
    (repo / "only_in_other.txt").write_text("ORPHAN-MARKER: this must never reach the sandbox\n")
    git(repo, "add", "only_in_other.txt")
    git(repo, "commit", "-q", "-m", "orphan branch content", date="2026-03-01T10:00:00+00:00")
    git(repo, "checkout", "-q", "-f", "main")
    (repo / "only_in_other.txt").unlink(missing_ok=True)


QUESTIONS = """\
# Fake question key for baseline/test_pipeline.py (docs/CONVENTIONS.md section 7 format). Not the real key.
- id: T001
  category: needle_long_range
  dimensions: [docx, needle]
  question: "How often are reserves for Tier-3 claims reviewed?"
  expected_answer: "Every 14 days."
  acceptable_variants: ["fortnightly"]
  must_include: [["14 days", "fortnight", "two weeks"]]
  must_not_include: ["30 days"]
  hops: 1
  ask_mode: chat
  difficulty: easy
- id: T002
  category: code_history
  dimensions: [code]
  question: "Which ticket does the commit that lowered the rate limit cite?"
  expected_answer: "CHUB-001"
  must_include: [["CHUB-001"]]
  hops: 1
  ask_mode: chat
  difficulty: medium
- id: T003
  category: unanswerable
  dimensions: [negation]
  question: "What is the name of the claims director's dog?"
  expected_answer: "Not found in the corpus."
  hops: 1
  ask_mode: chat
  difficulty: easy
"""

ANSWERS = {
    "T001": ("Every 14 days.\nEvidence: documents/LD901_test_reserve_policy.docx, section 2 (paragraph 3).",
             ["documents/LD901_test_reserve_policy.docx :: section 2, paragraph 3"], None),
    "T002": ("CHUB-001.\nEvidence: code_repo git history, second commit: 'CHUB-001: lower the rate limit to 50 requests'.",
             ["code_repo :: git log, commit 'CHUB-001: lower the rate limit to 50 requests'"], None),
    "T003": ("Not found in the corpus.", [], "Checked all three documents and the code repository."),
}


def entry_yaml(qid: str) -> str:
    ans, cites, notes = ANSWERS[qid]
    lines = [f"- id: {qid}", "  answer: |"] + [f"    {ln}" for ln in ans.splitlines()]
    lines += ["  cited_sources:" + ("" if cites else " []")] + [f'    - "{c}"' for c in cites]
    lines += [f"  notes: {json.dumps(notes) if notes else ''}".rstrip()]
    return "\n".join(lines)


def transcript(ids: list[str]) -> str:
    """A Claude Code-style JSONL transcript: setup call, then question a (2 calls), b (1 call), final answer."""
    a, b = ids

    def asst(ts, mid, block, usage):
        return {"type": "assistant", "timestamp": f"2026-11-15T10:00:{ts:02d}.000Z",
                "message": {"id": mid, "role": "assistant", "content": [block], "usage": usage}}

    def result(ts):
        return {"type": "user", "timestamp": f"2026-11-15T10:00:{ts:02d}.000Z",
                "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "x", "content": "..."}]}}

    def u(i, o):
        return {"input_tokens": 2, "cache_creation_input_tokens": i - 2, "cache_read_input_tokens": 0, "output_tokens": o}

    def tool(name):
        return {"type": "tool_use", "id": "x", "name": name, "input": {}}

    final = ">>> END\n" + "\n\n".join(entry_yaml(q) for q in ids)
    lines = [
        {"type": "user", "timestamp": "2026-11-15T10:00:00.000Z", "message": {"role": "user", "content": "prompt"}},
        {"type": "attachment", "timestamp": "2026-11-15T10:00:00.500Z"},
        asst(2, "m0", tool("Glob"), u(100, 10)), result(3),
        asst(5, "m1", {"type": "text", "text": f">>> {a}"}, u(200, 20)), asst(6, "m1", tool("Grep"), u(200, 20)),
        result(9),
        asst(12, "m2", tool("Bash"), u(300, 30)), result(20),
        asst(25, "m3", {"type": "text", "text": f"Done with that one.\n>>> {b}"}, u(400, 40)),
        asst(26, "m3", tool("Bash"), u(400, 40)), result(40),
        asst(50, "m4", {"type": "text", "text": final}, u(500, 50)),
    ]
    return "\n".join(json.dumps(x) for x in lines) + "\n"


# ---------------------------------------------------------------------------------------------

def main() -> int:
    print("== fixture")
    build_fixture()
    check((T / "build" / "code_repo" / "variant_a" / ".git").is_dir(), "fixture git repo built")

    print("== questions_for_agent before questions.yaml exists")
    r = run("baseline/questions_for_agent.py", "--root", str(T), expect=2)
    check("does not exist yet" in r.stderr, "clear 'does not exist yet' message")
    check(not SANDBOX.exists(), "nothing written")

    print("== leak checks (each must fail)")
    up = T / "corpus" / "upload" / "text"
    import docx  # noqa: PLC0415
    leak_docx = docx.Document()
    leak_docx.add_paragraph("expected_answer: Every 14 days")
    plants = [
        ("TX903_leak.yaml", lambda p: p.write_text("- fact_id: LD001-F001\n  statement: x\n")),
        ("TX904_leak.docx", lambda p: leak_docx.save(p)),
        ("long_docs.facts.yaml", lambda p: p.write_text("hello\n")),
    ]
    for name, make in plants:
        make(up / name)
        r = run("baseline/prepare_sandbox.py", "--root", str(T), expect=1, quiet=True)
        check("LEAK CHECK FAILED" in r.stderr and name in r.stderr, f"leak in {name} reported")
        (up / name).unlink()

    print("== prepare_sandbox")
    r = run("baseline/prepare_sandbox.py", "--root", str(T))
    check("documents/  3 files" in r.stdout, "3 documents copied (dotfile and .png skipped)")
    check("leak check passed" in r.stdout, "leak check passed")
    docs = sorted(p.name for p in (SANDBOX / "documents").iterdir())
    check(docs == ["LD901_test_reserve_policy.docx", "ST901_test_vendor_register.csv", "TX901_test_meeting_note.md"],
          f"documents flattened: {docs}")
    tops = sorted(p.name for p in SANDBOX.iterdir())
    check(tops == ["code_repo", "documents"], f"sandbox top level is only {tops}")
    repo = SANDBOX / "code_repo"
    check(git(repo, "branch", "--format=%(refname:short)").split() == ["main"], "only branch main in the sandbox repo")
    check(git(repo, "remote").strip() == "", "no git remote")
    check(git(repo, "rev-list", "--count", "--all").strip() == "2", "2 commits reachable")
    objs = git(repo, "cat-file", "--batch-all-objects", "--batch-check").splitlines()
    reach = git(repo, "rev-list", "--all", "--objects").splitlines()
    check(len(objs) == len(reach), f"no unreachable objects ({len(objs)} stored, {len(reach)} reachable)")
    check("ORPHAN-MARKER" not in git(repo, "log", "--all", "-p"), "orphan-branch content absent from history")
    check(not (repo / ".git" / "logs").exists(), "reflogs removed")
    check(not os.access(SANDBOX / "documents" / docs[0], os.W_OK), "corpus files are read-only")
    man = json.loads((SANDBOX.parent / "baseline_sandbox.manifest.json").read_text())
    check(man["status"] == "ok" and man["git"]["commits"] == 2 and len(man["files"]) == 5,
          f"manifest: status {man['status']}, {len(man['files'])} files, digest {man['digest'][:12]}")

    print("== prepare_sandbox --check")
    run("baseline/prepare_sandbox.py", "--root", str(T), "--check", "--mode", "cold")
    victim = SANDBOX / "documents" / "TX901_test_meeting_note.md"
    os.chmod(victim, 0o644)
    victim.write_text(victim.read_text() + "tampered\n")
    r = run("baseline/prepare_sandbox.py", "--root", str(T), "--check", expect=1, quiet=True)
    check("TX901_test_meeting_note.md: modified" in r.stderr, "modified corpus file detected")
    run("baseline/prepare_sandbox.py", "--root", str(T), quiet=True)            # rebuild
    (SANDBOX / "stray.txt").write_text("x")
    r = run("baseline/prepare_sandbox.py", "--root", str(T), "--check", expect=1, quiet=True)
    check("stray.txt: not allowed" in r.stderr, "stray top-level file detected")
    (SANDBOX / "stray.txt").unlink()
    (SANDBOX / "_notes").mkdir()
    (SANDBOX / "_notes" / "README.md").write_text("index of the corpus\n")
    r = run("baseline/prepare_sandbox.py", "--root", str(T), "--check", "--mode", "cold", expect=1, quiet=True)
    check("_notes/: not allowed" in r.stderr, "_notes/ refused in cold mode")
    run("baseline/prepare_sandbox.py", "--root", str(T), "--check", "--mode", "prep", quiet=True)
    run("baseline/prepare_sandbox.py", "--root", str(T), "--check", "--mode", "prepared", quiet=True)
    shutil.rmtree(SANDBOX / "_notes")

    print("== questions")
    QFILE.parent.mkdir(parents=True, exist_ok=True)
    QFILE.write_text(QUESTIONS, encoding="utf-8")
    run("harness/score.py", "keycheck", "--questions", str(QFILE))
    run("baseline/questions_for_agent.py", "--root", str(T), "--batch-size", "2", "--label", "test")
    qonly = (SANDBOX / "QUESTIONS_ONLY.md").read_text()
    batch_files = sorted(p.name for p in SANDBOX.glob("QUESTIONS_ONLY_batch_*.md"))
    check(batch_files == ["QUESTIONS_ONLY_batch_01.md", "QUESTIONS_ONLY_batch_02.md"], f"batch files {batch_files}")
    all_q = qonly + "".join((SANDBOX / f).read_text() for f in batch_files)
    for bad in ("expected_answer", "must_include", "category", "14 days", "CHUB-001", "Not found", "unanswerable"):
        check(bad not in all_q, f"question files do not contain {bad!r}")
    for qid in ("T001", "T002", "T003"):
        check(qonly.count(f"### {qid}\n") == 1, f"{qid} listed once")
    plan = list(csv.DictReader(open(RUN / "batch_plan.csv")))
    b1 = [r["id"] for r in plan if r["batch"] == "01"]
    b2 = [r["id"] for r in plan if r["batch"] == "02"]
    check(len(b1) == 2 and len(b2) == 1, f"batch plan: 01 = {b1}, 02 = {b2}")
    prompts = sorted(p.name for p in (RUN / "prompts").iterdir())
    check(prompts == ["batch_01.md", "batch_02.md", "system.md"], f"prompts {prompts}")
    p1 = (RUN / "prompts" / "batch_01.md").read_text()
    check("{{" not in p1 and all(f"### {q}" in p1 for q in b1) and str(SANDBOX) in p1,
          "batch prompt filled (no placeholders, has its questions and the sandbox path)")
    check(str(SANDBOX / "_scratch" / "batch_01") in p1, "batch prompt names its scratch folder")
    run("baseline/prepare_sandbox.py", "--root", str(T), "--check", "--mode", "cold")
    r = run("baseline/prepare_sandbox.py", "--root", str(T), "--check", "--mode", "prep", expect=1, quiet=True)
    check("QUESTIONS_ONLY.md: not allowed" in r.stderr, "question files refused in prep mode (question-blind prep)")

    print("== prepared mode: prep-only prompts, then questions fill run.yaml")
    run("baseline/questions_for_agent.py", "--root", str(T), "--label", "prep_test", "--baseline-mode", "prepared",
        "--prep-only", "--batch-size", "2")
    prun = T / "build" / "baseline_runs" / "prep_test"
    check(sorted(p.name for p in (prun / "prompts").iterdir()) == ["prep.md", "system.md"], "prep-only: no batch prompts")
    check(yaml.safe_load((prun / "run.yaml").read_text())["questions_sha1"] is None, "prep-only: no question key yet")
    check("_notes" in (prun / "prompts" / "prep.md").read_text(), "prep prompt names _notes/")
    r = run("baseline/questions_for_agent.py", "--root", str(T), "--label", "prep_test", "--baseline-mode", "prepared",
            "--batch-size", "2")
    check("filled" in r.stdout and yaml.safe_load((prun / "run.yaml").read_text())["questions_sha1"],
          "second call fills the question key into run.yaml")
    check("_notes/" in (prun / "prompts" / "batch_01.md").read_text(), "prepared batch prompt has the notes addendum")
    shutil.rmtree(prun)

    print("== fake agent output and timings")
    (RUN / "batch_01.yaml").write_text(
        ">>> END\nHere are the answers.\n```yaml\n" + "\n\n".join(entry_yaml(q) for q in b1) + "\n```\n",
        encoding="utf-8")
    (RUN / "batch_02.yaml").write_text("\n\n".join(entry_yaml(q) for q in b2) + "\n", encoding="utf-8")
    (RUN / "transcript_batch_01.jsonl").write_text(transcript(b1), encoding="utf-8")
    run("baseline/timings_from_transcript.py", str(RUN / "transcript_batch_01.jsonl"), "--batch", "01",
        "--timings", str(RUN / "timings.csv"))
    rows = {(r["batch"], r["question_id"]): r for r in csv.DictReader(open(RUN / "timings.csv"))}
    got = {k[1]: (float(v["seconds"]), int(v["tool_calls"]), int(v["tokens_in"]), int(v["tokens_out"]))
           for k, v in rows.items() if k[0] == "01"}
    want = {"_setup": (5.0, 1, 100, 10), b1[0]: (20.0, 2, 500, 50), b1[1]: (15.0, 1, 400, 40),
            "_output": (10.0, 0, 500, 50)}
    check(got == want, f"transcript split: {got}")
    check(rows.get(("02", b2[0]), {}).get("seconds") == "", "batch 02 template row still blank")
    with open(RUN / "timings.csv", "a", newline="") as f:
        csv.writer(f, lineterminator="\n").writerow(["02", "*", "30", "6", "", "", "9000", "agent usage report"])
    r = run("baseline/timings_from_transcript.py", str(RUN / "transcript_batch_01.jsonl"), "--prep", "--dry-run")
    check("prep,_prep,50.0,4,1500,150,1650" in r.stdout, "prep mode: one '_prep' row with session totals")
    meta = yaml.safe_load((RUN / "run.yaml").read_text())
    meta.update(model="test-model-1", temperature="runner default (not settable)", runner="test harness",
                operator="test", date="2026-11-15", timing_method="transcript (batch 1), batch_totals (batch 2)")
    (RUN / "run.yaml").write_text(yaml.safe_dump(meta, sort_keys=False))

    print("== collect_results")
    sheet = RESULTS / "runs" / "baseline_test.yaml"
    run("baseline/collect_results.py", "--label", "test", "--root", str(T), "--questions", str(QFILE))
    rep = json.loads((RESULTS / "baseline_test_score.json").read_text())
    t = rep["totals"]
    check((t["n"], t["correct"], t["answered"]) == (3, 3, 3), f"score: {t['correct']}/{t['n']} correct")
    check(rep["run"]["context"] == "baseline" and rep["run"]["label"] == "baseline_test", "run label/context")
    lat = {q["id"]: q["latency_s"] for q in rep["questions"]}
    check(lat == {b1[0]: 20.0, b1[1]: 15.0, b2[0]: 30.0}, f"latency per question {lat}")
    s = yaml.safe_load(sheet.read_text())
    by = {e["id"]: e for e in s["answers"]}
    check({q: by[q]["timing"] for q in by} == {b1[0]: "exact", b1[1]: "exact", b2[0]: "apportioned"}, "timing methods")
    check(by[b2[0]]["tool_calls"] == 6 and by[b1[0]]["tool_calls"] == 2, "tool calls per question")
    check(by["T001"]["cited_sources"] == ANSWERS["T001"][1], "cited sources carried over")
    eff = json.loads((RESULTS / "baseline_test_efficiency.json").read_text())
    check(eff["wall_seconds"] == 80.0 and eff["tool_calls"] == 10, f"efficiency: {eff['wall_seconds']} s, "
          f"{eff['tool_calls']} tool calls (expected 80 s, 10)")
    check("80.0 s" in (RESULTS / "baseline_test_score.md").read_text(), "summary line in the score report")

    print("== override survives re-collect")
    data = yaml.safe_load(sheet.read_text())
    for e in data["answers"]:
        if e["id"] == "T001":
            e["override"] = "partial"
    sheet.write_text(yaml.safe_dump(data, sort_keys=False))
    r = run("baseline/collect_results.py", "--label", "test", "--root", str(T), "--questions", str(QFILE))
    check("kept 1 override" in r.stdout, "override kept")
    rep = json.loads((RESULTS / "baseline_test_score.json").read_text())
    check(rep["totals"]["partial"] == 1, "override applied by the scorer")
    sheet.unlink()
    run("baseline/collect_results.py", "--label", "test", "--root", str(T), "--questions", str(QFILE), quiet=True)

    print("== fake product run and compare")
    run("harness/score.py", "template", "--label", "product_test", "--context", "A", "--questions", str(QFILE),
        "--out-dir", str(RESULTS / "runs"), "--force")
    ps = RESULTS / "runs" / "product_test.yaml"
    data = yaml.safe_load(ps.read_text())
    fake = {"T001": ("Reserves are reviewed every 30 days.", 18), "T002": ("Not found in the context.", 15),
            "T003": ("Not found.", 12)}
    for e in data["answers"]:
        e["answer"], e["latency_s"] = fake[e["id"]]
    ps.write_text(yaml.safe_dump(data, sort_keys=False))
    run("harness/score.py", "score", str(ps), "--questions", str(QFILE), "--out", str(RESULTS / "product_test_score.md"))
    out = RESULTS / "compare_product_vs_baseline.md"
    run("harness/score.py", "compare", str(RESULTS / "product_test_score.json"), str(RESULTS / "baseline_test_score.json"),
        "--out", str(out))
    cmp_md = out.read_text()
    check("product_test" in cmp_md and "baseline_test" in cmp_md and "T001" in cmp_md, "comparison written")

    print()
    if FAILS:
        print(f"FAILED: {len(FAILS)} check(s)")
        for f in FAILS:
            print(f"  - {f}")
        return 1
    print(f"ALL CHECKS PASSED. Outputs in {T.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
