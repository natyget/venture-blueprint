#!/usr/bin/env python3
"""Check a venture-blueprint plan against the bar.

Enforces the mechanical rules that are invisible on a read-through and
expensive in week three: steps with no runnable test, compliance rows that
point at nothing, decisions with no rejected alternatives, concurrent
workstreams fighting over the same file, and leftover placeholders.

Usage:  python3 -I scripts/check_plan.py <plan-dir> [--quiet]
Exit 1 if there are errors. Warnings do not fail the run.
"""

import argparse
import csv
import datetime as dt
import json
import re
import sys
from pathlib import Path

DOCS = {
    "00-brief.md": [],
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
                     r"\b(19|20)\d{2}-\d{2}-\d{2}\b|founder|this conversation", re.I)
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


def load_json(path, rep):
    if not path.exists():
        rep.error(path.name, "missing — run new_plan.py or create it")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        rep.error(path.name, f"invalid JSON: {exc}")
        return None


def check_docs(plan, rep):
    for name, required in DOCS.items():
        path = plan / name
        if not path.exists():
            rep.error(name, "missing document")
            continue
        text = path.read_text(encoding="utf-8")
        low = text.lower()
        if len(text.strip()) < 200:
            rep.error(name, "looks empty — under 200 characters of content")
        for phrase in required:
            if phrase.lower() not in low:
                rep.error(name, f'required section missing: no mention of "{phrase}"')
        for i, line in enumerate(text.splitlines(), 1):
            if PLACEHOLDER.search(line):
                rep.error(f"{name}:{i}", f"placeholder left in: {line.strip()[:70]}")
        unver = low.count("unverified")
        if unver:
            rep.warn(name, f"{unver} UNVERIFIED claim(s) — confirm the founder knows")
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if line.lstrip().startswith(("|", ">", "```")):
                continue
            if MONEY.search(line):
                window = " ".join(lines[max(0, i - 1):i + 3])
                if not SOURCED.search(window):
                    rep.warn(f"{name}:{i + 1}",
                             f"figure with no nearby source: {line.strip()[:70]}")


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
        return {}, {}
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
    return by_id, workstreams


def check_compliance(path, step_ids, rep):
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
    counsel_rows = []
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
        if approach == "avoid feature":
            pass
        elif not step:
            rep.error(where, f"[{label}] no implementing step — an obligation "
                             "with no step is one nobody will do")
        else:
            for sid in re.split(r"[,\s]+", step):
                if sid and sid not in step_ids:
                    rep.error(where, f"[{label}] step {sid!r} is not in roadmap.json")
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
    if counsel_rows:
        rep.warn("compliance.csv", f"{len(counsel_rows)} row(s) need a lawyer: "
                                   f"{', '.join(sorted(set(counsel_rows))[:6])}")


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
    ap.add_argument("--quiet", action="store_true",
                    help="only print errors and the summary")
    args = ap.parse_args()

    plan = Path(args.plan_dir)
    if not plan.is_dir():
        print(f"error: {plan} is not a directory", file=sys.stderr)
        return 2

    rep = Report()
    check_docs(plan, rep)
    roadmap = load_json(plan / "roadmap.json", rep)
    steps_by_id, _ = check_roadmap(roadmap, rep) if roadmap else ({}, {})
    check_compliance(plan / "compliance.csv", set(steps_by_id), rep)
    decisions = load_json(plan / "decisions.json", rep)
    if decisions:
        check_decisions(decisions, rep)

    if rep.errors:
        print(f"\n{len(rep.errors)} error(s) — fix these before handing over:\n")
        for where, msg in rep.errors:
            print(f"  ERROR  {where}: {msg}")
    if rep.warnings and not args.quiet:
        print(f"\n{len(rep.warnings)} warning(s) — judgement calls:\n")
        for where, msg in rep.warnings:
            print(f"  warn   {where}: {msg}")

    print(f"\n{'FAIL' if rep.errors else 'PASS'}: "
          f"{len(rep.errors)} error(s), {len(rep.warnings)} warning(s)")
    if not rep.errors:
        print("The plan meets the mechanical bar. The judgement is still yours.")
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
