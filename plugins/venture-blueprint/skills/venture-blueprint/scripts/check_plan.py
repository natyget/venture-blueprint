#!/usr/bin/env python3
"""Check a venture-blueprint plan against the bar, for the stage it is in.

Enforces the mechanical rules that are invisible on a read-through and
expensive in week three: unanswered traps, unsourced assumptions, financials
that no longer match their inputs, steps with no runnable test, compliance
rows that point at nothing, decisions with no rejected alternatives,
concurrent workstreams fighting over a file, and leftover placeholders.

It checks only what the current stage should have produced, so a brainstorm
is not failed for having no roadmap yet.

Usage:  python3 -I scripts/check_plan.py <plan-dir> [--stage explore|plan|build] [--quiet]
With no --stage, the stage is detected from what exists in the folder.
Exit 1 if there are errors. Warnings do not fail the run.
"""

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent

DOCS = {
    "00-brief.md": [],
    "paths.md": ["preference", "recommend"],
    "01-wedge.md": ["what the re-read changed", "wedge"],
    "02-economics.md": ["bottom-up", "unit economics", "bootstrap"],
    "03-compliance.md": ["register", "not legal advice"],
    "04-architecture.md": ["budget", "scale"],
    "05-design-language.md": ["token", "asset"],
    "06-growth.md": ["event", "funnel"],
    "07-monetization.md": ["rail", "price"],
    "08-ecosystem.md": ["value chain", "console"],
    "09-roadmap.md": ["cut line", "gate", "rollback"],
    "10-red-team.md": ["did not verify", "kill"],
    "business-plan.md": ["executive summary", "vision", "mission", "principles",
                         "persona", "anti-persona", "market", "competitor matrix",
                         "financial", "statement of work", "milestones",
                         "unverified"],
}
# Once the founder has chosen, paths.md must record the choice and its reasons.
CHOSEN_EXTRA = {"paths.md": ["choice", "constraint", "rejected"]}

PLAN_DOCS = ["00-brief.md", "paths.md", "01-wedge.md", "02-economics.md",
             "03-compliance.md", "04-architecture.md", "05-design-language.md",
             "06-growth.md", "07-monetization.md", "08-ecosystem.md",
             "10-red-team.md", "business-plan.md"]
STAGE_DOCS = {
    "explore": ["00-brief.md", "paths.md"],
    "plan": PLAN_DOCS,
    "build": PLAN_DOCS + ["09-roadmap.md"],
}

STEP_FIELDS = ["id", "workstream", "anchor", "change", "why", "risk",
               "test", "pass", "revert", "effort_hours", "files", "tier"]

VAGUE_TEST = re.compile(
    r"\b(verify|check|confirm|ensure|make sure)\b[^.]{0,20}\b(it|that|this|everything)?\s*"
    r"\b(works?|is\s+fine|is\s+ok|looks?\s+(good|right|fine)|correct(ly)?)\b"
    r"|^\s*(manual(ly)?|by hand|eyeball|smoke test|test it|qa)\s*\.?\s*$"
    r"|^\s*(tbd|n/?a|none)\s*\.?\s*$",
    re.I)

PLACEHOLDER = re.compile(r"\bTODO:|\bTBD\b|<FILL[^>]*>|\bXXX\b|\bLOREM\b", re.I)
MONEY = re.compile(r"(?<![\w.])\$\s?\d[\d,]*(\.\d+)?(?![\w])|(?<![\w.])\d+(\.\d+)?\s?%")
SOURCED = re.compile(r"https?://|\[source|\bsource:|\bverified\b|UNVERIFIED|"
                     r"\b[a-zA-Z0-9_./-]+\.(ts|tsx|js|jsx|py|swift|kt|md|json):\d+|"
                     r"\b(19|20)\d{2}-\d{2}-\d{2}\b|founder|this conversation|"
                     r"financials\.md|model\.py", re.I)
BANNED = re.compile(
    r"\b(elevate[sd]?|seamless(ly)?|unlock(s|ed|ing)?|game[- ]chang(er|ing)|"
    r"revolutioni[sz](e|es|ed|ing)|effortless(ly)?|empower(s|ed|ing)?|"
    r"next[- ]generation|cutting[- ]edge|world[- ]class|best[- ]in[- ]class|"
    r"synerg(y|ies)|paradigm)\b|\bnot just\b[^.\n]{0,60}\bit'?s\b", re.I)
POSTURE = re.compile(r"^(in force|enjoined|proposed|effective\s+\S+)$", re.I)
APPROACH = {"implement", "design away", "avoid feature"}
COUNSEL = {"required", "no"}
TIERS = {"must", "should", "can-follow"}
STALE_DAYS = 90


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, where, msg):
        self.errors.append((where, msg))

    def warn(self, where, msg):
        self.warnings.append((where, msg))


def load_json(path, rep, required=True):
    if not path.exists():
        if required:
            rep.error(path.name, "missing — run new_plan.py or create it")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        rep.error(path.name, f"invalid JSON: {exc}")
        return None


def has_steps(plan):
    try:
        data = json.loads((plan / "roadmap.json").read_text(encoding="utf-8"))
        return bool(data.get("steps"))
    except (OSError, json.JSONDecodeError):
        return False


def detect_stage(plan):
    if has_steps(plan):
        return "build"
    bp = plan / "business-plan.md"
    if bp.exists() and not PLACEHOLDER.search(bp.read_text(encoding="utf-8")):
        return "plan"
    for name in ("01-wedge.md", "assumptions.json"):
        p = plan / name
        if p.exists() and not PLACEHOLDER.search(p.read_text(encoding="utf-8")):
            return "plan"
    return "explore"


def check_docs(plan, stage, rep):
    for name in STAGE_DOCS[stage]:
        required = list(DOCS[name])
        if stage != "explore":
            required += CHOSEN_EXTRA.get(name, [])
        path = plan / name
        if not path.exists():
            rep.error(name, "missing document")
            continue
        text = path.read_text(encoding="utf-8")
        # Scaffold hints live in comments; they must not satisfy a required section.
        low = re.sub(r"<!--.*?-->", "", text, flags=re.S).lower()
        if len(text.strip()) < 200:
            rep.error(name, "looks empty — under 200 characters of content")
        for phrase in required:
            if phrase.lower() not in low:
                rep.error(name, f'required section missing: no mention of "{phrase}"')
        lines = text.splitlines()
        for i, line in enumerate(lines, 1):
            if PLACEHOLDER.search(line):
                rep.error(f"{name}:{i}", f"placeholder left in: {line.strip()[:70]}")
        unver = low.count("unverified")
        if unver and name != "business-plan.md":
            rep.warn(name, f"{unver} UNVERIFIED claim(s) — confirm the founder knows")
        for i, line in enumerate(lines):
            if line.lstrip().startswith(("|", ">", "```", "<!--")):
                continue
            if MONEY.search(line):
                window = " ".join(lines[max(0, i - 1):i + 3])
                if not SOURCED.search(window):
                    rep.warn(f"{name}:{i + 1}",
                             f"figure with no nearby source: {line.strip()[:70]}")
        if name in ("business-plan.md", "paths.md"):
            in_code = False
            for i, line in enumerate(lines, 1):
                if line.lstrip().startswith("```"):
                    in_code = not in_code
                if in_code:
                    continue
                found = [m.group(0) for m in BANNED.finditer(line)]
                if found:
                    words = ", ".join(f'"{w}"' for w in dict.fromkeys(found))
                    rep.warn(f"{name}:{i}", f"slogan wording {words} — "
                                            "say the concrete thing instead")


def source_state(block):
    src = str((block or {}).get("source") or "").strip()
    if not src or src.upper().startswith("TODO"):
        return "missing"
    if "UNVERIFIED" in src.upper():
        return "unverified"
    return "ok"


def check_model(plan, rep):
    ap = plan / "assumptions.json"
    if not ap.exists():
        rep.error("assumptions.json", "missing — the financials must come from "
                                      "model.py, not from mental arithmetic")
        return
    raw = ap.read_bytes()
    try:
        a = json.loads(raw)
    except json.JSONDecodeError as exc:
        rep.error("assumptions.json", f"invalid JSON: {exc}")
        return
    if not isinstance(a.get("customers"), dict) or not a.get("revenue_lines"):
        rep.error("assumptions.json", "needs a customers block and at least one "
                                      "revenue line")
        return
    blocks = ([("customers", a["customers"])]
              + [(f"revenue line {l.get('name', '?')!r}", l) for l in a["revenue_lines"]]
              + [(f"variable cost {v.get('name', '?')!r}", v)
                 for v in a.get("variable_costs") or []]
              + [(f"fixed cost {f.get('name', '?')!r}", f)
                 for f in a.get("fixed_costs") or []])
    unverified = 0
    for label, blk in blocks:
        state = source_state(blk)
        if state == "missing":
            rep.error("assumptions.json", f"{label} has no source — give one, or "
                                          "say UNVERIFIED and why")
        elif state == "unverified":
            unverified += 1
    if unverified:
        rep.warn("assumptions.json", f"{unverified} of {len(blocks)} assumption "
                                     "block(s) are UNVERIFIED — the plan's numbers "
                                     "are only as good as these")
    if not a.get("fixed_costs"):
        rep.warn("assumptions.json", "no fixed costs at all — is nobody being paid, "
                                     "and is nothing being bought?")

    fm = plan / "financials.md"
    if not fm.exists():
        rep.error("financials.md", "missing — run scripts/model.py")
        return
    m = re.search(r"assumptions-sha256:\s*([0-9a-f]+)", fm.read_text(encoding="utf-8"))
    if not m or m.group(1) != hashlib.sha256(raw).hexdigest()[:16]:
        rep.error("financials.md", "stale — assumptions.json changed after "
                                   "model.py last ran. Rerun it so every figure "
                                   "in the plan agrees")


def reachable(steps_by_id):
    """Transitive closure of the depends graph: id -> set of ids it depends on."""
    memo = {}

    def walk(sid, seen):
        if sid in memo:
            return memo[sid]
        if sid in seen:
            return set()
        seen = seen | {sid}
        out = set()
        for dep in steps_by_id.get(sid, {}).get("depends", []) or []:
            out.add(dep)
            out |= walk(dep, seen)
        memo[sid] = out
        return out

    return {sid: walk(sid, set()) for sid in steps_by_id}


def find_cycle(steps_by_id):
    state = {}

    def visit(sid, stack):
        if state.get(sid) == 2:
            return None
        if state.get(sid) == 1:
            return stack[stack.index(sid):] + [sid]
        state[sid] = 1
        for dep in steps_by_id.get(sid, {}).get("depends", []) or []:
            if dep in steps_by_id:
                cyc = visit(dep, stack + [sid])
                if cyc:
                    return cyc
        state[sid] = 2
        return None

    for sid in steps_by_id:
        cyc = visit(sid, [])
        if cyc:
            return cyc
    return None


def check_roadmap(data, rep):
    steps = data.get("steps") or []
    if not steps:
        rep.error("roadmap.json", "no steps")
        return {}
    workstreams = {w.get("id"): w for w in data.get("workstreams") or []}
    if not workstreams:
        rep.error("roadmap.json", "no workstreams declared")

    by_id = {}
    for idx, step in enumerate(steps):
        sid = step.get("id") or f"#{idx}"
        if sid in by_id:
            rep.error(f"roadmap.json/{sid}", "duplicate step id")
        by_id[sid] = step
        where = f"roadmap.json/{sid}"

        for field in STEP_FIELDS:
            val = step.get(field)
            if val is None or (isinstance(val, str) and not val.strip()):
                if field == "files" and step.get("human"):
                    continue
                rep.error(where, f"missing {field}")

        test = (step.get("test") or "").strip()
        if test and VAGUE_TEST.search(test):
            rep.error(where, f'test is not runnable: "{test[:60]}" — '
                             "give a command or query")
        elif test and len(test) < 10:
            rep.error(where, f'test too vague to run: "{test}"')

        tier = step.get("tier")
        if tier and tier not in TIERS:
            rep.error(where, f"tier must be one of {sorted(TIERS)}, got {tier!r}")

        ws = step.get("workstream")
        if ws and workstreams and ws not in workstreams:
            rep.error(where, f"workstream {ws!r} is not declared")

        if step.get("user_facing") and not (step.get("event") or "").strip():
            rep.error(where, "user_facing but no event — every feature ships "
                             "with its measurement")

        if step.get("human") and not step.get("lead_time_days"):
            rep.warn(where, "human step with no lead_time_days — it cannot be "
                            "scheduled first in wall-clock time")

        try:
            hours = float(step.get("effort_hours") or 0)
            if hours > 4:
                rep.warn(where, f"{hours}h is a workstream, not a step — split it")
        except (TypeError, ValueError):
            rep.error(where, f"effort_hours is not a number: "
                             f"{step.get('effort_hours')!r}")

    for sid, step in by_id.items():
        for dep in step.get("depends") or []:
            if dep not in by_id:
                rep.error(f"roadmap.json/{sid}", f"depends on unknown step {dep!r}")

    cyc = find_cycle(by_id)
    if cyc:
        rep.error("roadmap.json", "dependency cycle: " + " -> ".join(cyc))

    if len(workstreams) > 1:
        blocking = [w for w in workstreams.values() if w.get("blocking")]
        if not blocking:
            rep.error("roadmap.json", "no blocking workstream — contracts must "
                                      "land before parallel work starts")
        contract_paths = []
        for w in blocking:
            contract_paths += list(w.get("paths") or [])
        for sid, step in by_id.items():
            if workstreams.get(step.get("workstream"), {}).get("blocking"):
                continue
            for f in step.get("files") or []:
                for cp in contract_paths:
                    if f.startswith(cp):
                        rep.error(f"roadmap.json/{sid}",
                                  f"touches contract path {f!r} from a "
                                  "non-blocking workstream")

    gates = data.get("gates") or []
    if not gates:
        rep.error("roadmap.json", "no gates — ship criteria must be written "
                                  "before the build")
    for i, gate in enumerate(gates):
        if not (gate.get("check") or "").strip():
            rep.error(f"roadmap.json/gate[{i}]", "missing check")
        if not (gate.get("pass") or "").strip():
            rep.error(f"roadmap.json/gate[{i}]", "missing pass criterion")

    if not data.get("cannot_undo"):
        rep.warn("roadmap.json", "cannot_undo is empty — is nothing permanent?")

    if not any(s.get("tier") == "must" for s in steps):
        rep.error("roadmap.json", "no step is tier 'must' — the cut line is unset")

    deps = reachable(by_id)
    owners = {}
    for sid, step in by_id.items():
        for f in step.get("files") or []:
            owners.setdefault(f, []).append(sid)
    for f, sids in sorted(owners.items()):
        if len(sids) < 2:
            continue
        for i in range(len(sids)):
            for j in range(i + 1, len(sids)):
                a, b = sids[i], sids[j]
                ws_a = by_id[a].get("workstream")
                ws_b = by_id[b].get("workstream")
                if ws_a == ws_b:
                    continue
                if b in deps.get(a, set()) or a in deps.get(b, set()):
                    continue
                rep.error("roadmap.json",
                          f"{f!r} is claimed by {a} ({ws_a}) and {b} ({ws_b}) "
                          "with no dependency between them — concurrent "
                          "sessions would collide")
    return by_id


def check_step_refs(where, label, raw, step_ids, building, rep):
    """In the build stage every referenced step must exist; earlier, refs are notes."""
    for sid in re.split(r"[,\s]+", (raw or "").strip()):
        if not sid:
            continue
        if building and sid not in step_ids:
            rep.error(where, f"[{label}] step {sid!r} is not in roadmap.json")


def check_compliance(path, step_ids, building, rep):
    if not path.exists():
        rep.error("compliance.csv", "missing")
        return
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    if not rows:
        rep.error("compliance.csv", "no rows — every product triggers something")
        return
    today = dt.date.today()
    needed = {"feature", "regime", "requirement", "posture", "approach",
              "step", "evidence", "source", "verified", "counsel"}
    missing_cols = needed - set(rows[0].keys())
    if missing_cols:
        rep.error("compliance.csv", f"missing columns: {sorted(missing_cols)}")
        return
    counsel_rows, unstepped = [], 0
    for i, row in enumerate(rows, 2):
        where = f"compliance.csv:{i}"
        label = (row.get("regime") or "?").strip()[:40]
        approach = (row.get("approach") or "").strip().lower()
        if approach not in APPROACH:
            rep.error(where, f"[{label}] approach must be one of "
                             f"{sorted(APPROACH)}, got {approach!r}")
        if not POSTURE.match((row.get("posture") or "").strip()):
            rep.error(where, f"[{label}] posture must be 'in force', 'enjoined', "
                             "'proposed' or 'effective <date>'")
        counsel = (row.get("counsel") or "").strip().lower()
        if counsel not in COUNSEL:
            rep.error(where, f"[{label}] counsel must be 'required' or 'no'")
        elif counsel == "required":
            counsel_rows.append(label)
        step = (row.get("step") or "").strip()
        if approach != "avoid feature" and not step:
            if building:
                rep.error(where, f"[{label}] no implementing step — an obligation "
                                 "with no step is one nobody will do")
            else:
                unstepped += 1
        check_step_refs(where, label, step, step_ids, building, rep)
        if not (row.get("source") or "").strip():
            rep.error(where, f"[{label}] no source")
        if not (row.get("evidence") or "").strip():
            rep.error(where, f"[{label}] no evidence artifact")
        verified = (row.get("verified") or "").strip()
        if not verified:
            rep.error(where, f"[{label}] no verified date")
        else:
            try:
                age = (today - dt.date.fromisoformat(verified)).days
                if age > STALE_DAYS:
                    rep.warn(where, f"[{label}] verified {age} days ago — "
                                    "re-check before building on it")
                elif age < 0:
                    rep.error(where, f"[{label}] verified date is in the future")
            except ValueError:
                rep.error(where, f"[{label}] verified is not YYYY-MM-DD: {verified!r}")
    if unstepped:
        rep.warn("compliance.csv", f"{unstepped} obligation(s) have no implementing "
                                   "step yet — each needs one in the build stage")
    if counsel_rows:
        rep.warn("compliance.csv", f"{len(counsel_rows)} row(s) need a lawyer: "
                                   f"{', '.join(sorted(set(counsel_rows))[:6])}")


def canonical_traps():
    """The fixed trap list, so the CSV and the checker cannot drift apart."""
    try:
        path = SKILL / "templates" / "traps.json"
        return json.loads(path.read_text(encoding="utf-8")).get("traps", [])
    except (OSError, json.JSONDecodeError):
        return []


def check_traps(path, step_ids, building, rep):
    canon = canonical_traps()
    if not path.exists():
        rep.error("traps.csv", "missing — run new_plan.py to seed the trap sweep")
        return
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    if not rows:
        rep.error("traps.csv", "no rows — the sweep is not optional")
        return
    needed = {"id", "category", "question", "status", "answer",
              "source", "verified", "step"}
    missing_cols = needed - set(rows[0].keys())
    if missing_cols:
        rep.error("traps.csv", f"missing columns: {sorted(missing_cols)}")
        return

    today = dt.date.today()
    seen = set()
    for i, row in enumerate(rows, 2):
        tid = (row.get("id") or "").strip()
        where = f"traps.csv:{i}"
        if not tid:
            rep.error(where, "row has no id")
            continue
        if tid in seen:
            rep.error(where, f"duplicate trap id {tid}")
        seen.add(tid)

        status = (row.get("status") or "").strip().lower()
        answer = (row.get("answer") or "").strip()
        if status not in {"answered", "n/a"}:
            rep.error(where, f"[{tid}] status must be 'answered' or 'n/a', got "
                             f"{status or 'empty'!r} — an unanswered trap is one "
                             "nobody looked at")
            continue
        if not answer:
            extra = (" — 'n/a' still needs the reason it does not apply"
                     if status == "n/a" else "")
            rep.error(where, f"[{tid}] no answer{extra}")

        if status != "answered":
            continue
        if not (row.get("source") or "").strip():
            rep.error(where, f"[{tid}] answered with no source")
        verified = (row.get("verified") or "").strip()
        if not verified:
            rep.error(where, f"[{tid}] answered with no verified date")
        else:
            try:
                age = (today - dt.date.fromisoformat(verified)).days
                if age > STALE_DAYS:
                    rep.warn(where, f"[{tid}] verified {age} days ago — platform "
                                    "rules and statutes move; re-check")
                elif age < 0:
                    rep.error(where, f"[{tid}] verified date is in the future")
            except ValueError:
                rep.error(where, f"[{tid}] verified is not YYYY-MM-DD: {verified!r}")
        check_step_refs(where, tid, row.get("step"), step_ids, building, rep)

    for trap in canon:
        if trap.get("id") not in seen:
            rep.error("traps.csv", f"canonical trap {trap.get('id')} "
                                   f"({trap.get('category')}) is missing: "
                                   f"{trap.get('question', '')[:70]}")


def check_decisions(data, rep):
    decisions = data.get("decisions") or []
    if not decisions:
        rep.error("decisions.json", "no decisions recorded")
        return
    for i, d in enumerate(decisions):
        did = d.get("id") or f"#{i}"
        where = f"decisions.json/{did}"
        if not (d.get("chosen") or "").strip():
            rep.error(where, "no chosen option")
        if not (d.get("because") or "").strip():
            rep.error(where, "no reason given")
        rejected = d.get("rejected") or []
        if not rejected:
            rep.error(where, "no rejected alternatives — a choice with no "
                             "alternatives is not a decision")
        for r in rejected:
            if not (r.get("why") or "").strip():
                rep.error(where, f"rejected {r.get('option')!r} with no reason")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan_dir")
    ap.add_argument("--stage", choices=["explore", "plan", "build"],
                    help="what to check; detected from the folder if omitted")
    ap.add_argument("--quiet", action="store_true",
                    help="only print errors and the summary")
    args = ap.parse_args()

    plan = Path(args.plan_dir)
    if not plan.is_dir():
        print(f"error: {plan} is not a directory", file=sys.stderr)
        return 2

    stage = args.stage or detect_stage(plan)
    building = stage == "build"
    print(f"Checking stage: {stage}"
          + ("" if args.stage else " (detected — pass --stage to choose)"))

    rep = Report()
    check_docs(plan, stage, rep)

    steps_by_id = {}
    if building:
        roadmap = load_json(plan / "roadmap.json", rep)
        if roadmap:
            steps_by_id = check_roadmap(roadmap, rep)

    if stage in ("plan", "build"):
        check_model(plan, rep)
        check_compliance(plan / "compliance.csv", set(steps_by_id), building, rep)
        check_traps(plan / "traps.csv", set(steps_by_id), building, rep)
        decisions = load_json(plan / "decisions.json", rep)
        if decisions:
            check_decisions(decisions, rep)
    else:
        decisions = load_json(plan / "decisions.json", rep, required=False)
        if decisions and decisions.get("decisions"):
            check_decisions(decisions, rep)

    if rep.errors:
        print(f"\n{len(rep.errors)} error(s) — fix these before handing over:\n")
        for where, msg in rep.errors:
            print(f"  ERROR  {where}: {msg}")
    if rep.warnings and not args.quiet:
        print(f"\n{len(rep.warnings)} warning(s) — judgement calls:\n")
        for where, msg in rep.warnings:
            print(f"  warn   {where}: {msg}")

    print(f"\n{'FAIL' if rep.errors else 'PASS'} ({stage}): "
          f"{len(rep.errors)} error(s), {len(rep.warnings)} warning(s)")
    if not rep.errors:
        nxt = {"explore": "Show the paths and ask which one, then stop.",
               "plan": "Hand over the business plan and ask whether to build, "
                       "then stop.",
               "build": "The plan meets the mechanical bar. The judgement is "
                        "still yours."}[stage]
        print(nxt)
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
