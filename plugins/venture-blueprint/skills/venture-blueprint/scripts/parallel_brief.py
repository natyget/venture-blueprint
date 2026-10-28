#!/usr/bin/env python3
"""Cut a roadmap into self-contained build briefs, one per workstream.

Each brief is written for a session that has none of the planning conversation:
it carries the wedge, the contract, the tokens, its own steps verbatim, the
exact files it owns, what it must not touch, and how to stop when blocked.

Before writing anything it proves that workstreams which can run at the same
time own disjoint files. If two do not, it refuses — a file claimed by two
concurrent sessions is the one failure this whole structure exists to prevent.

Usage:  python3 -I scripts/parallel_brief.py <plan-dir> --out <dir>
        python3 -I scripts/parallel_brief.py <plan-dir> --dry-run
"""

import argparse
import json
import re
import sys
from pathlib import Path


def load(plan):
    path = plan / "roadmap.json"
    if not path.exists():
        sys.exit(f"error: {path} not found")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(f"error: {path} is not valid JSON: {exc}")


def section(plan, filename, heading_re, limit=900):
    """Pull the first prose paragraph under a matching heading."""
    path = plan / filename
    if not path.exists():
        return None
    lines = path.read_text(encoding="utf-8").splitlines()
    pat = re.compile(heading_re, re.I)
    for i, line in enumerate(lines):
        if line.startswith("#") and pat.search(line):
            buf = []
            for nxt in lines[i + 1:]:
                if nxt.startswith("#"):
                    break
                stripped = nxt.strip()
                if stripped.startswith("<!--") or stripped.startswith("TODO:"):
                    continue
                if not stripped and buf:
                    break
                if stripped:
                    buf.append(stripped)
            if buf:
                return " ".join(buf)[:limit]
    return None


def find_cycle(steps_by_id):
    """A cycle makes the ordering meaningless, so the split cannot be trusted."""
    state = {}

    def visit(sid, stack):
        if state.get(sid) == 2:
            return None
        if state.get(sid) == 1:
            return stack[stack.index(sid):] + [sid]
        state[sid] = 1
        for dep in steps_by_id.get(sid, {}).get("depends") or []:
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


def transitive(steps_by_id):
    memo = {}

    def walk(sid, seen):
        if sid in memo:
            return memo[sid]
        if sid in seen:
            return set()
        seen = seen | {sid}
        out = set()
        for dep in steps_by_id.get(sid, {}).get("depends") or []:
            out.add(dep)
            out |= walk(dep, seen)
        memo[sid] = out
        return out

    return {sid: walk(sid, set()) for sid in steps_by_id}


def critical_path(steps_by_id):
    """Longest chain by effort_hours through the depends DAG."""
    memo = {}

    def cost(sid, seen):
        if sid in memo:
            return memo[sid]
        if sid in seen:
            return 0.0, []
        seen = seen | {sid}
        step = steps_by_id.get(sid, {})
        try:
            own = float(step.get("effort_hours") or 0)
        except (TypeError, ValueError):
            own = 0.0
        best, chain = 0.0, []
        for dep in step.get("depends") or []:
            if dep in steps_by_id:
                c, ch = cost(dep, seen)
                if c > best:
                    best, chain = c, ch
        memo[sid] = (own + best, chain + [sid])
        return memo[sid]

    best, chain = 0.0, []
    for sid in steps_by_id:
        c, ch = cost(sid, set())
        if c > best:
            best, chain = c, ch
    return best, chain


def concurrency_conflicts(steps_by_id, deps):
    """Files claimed by two steps in different workstreams with no ordering."""
    owners = {}
    for sid, step in steps_by_id.items():
        for f in step.get("files") or []:
            owners.setdefault(f, []).append(sid)
    conflicts = []
    for f, sids in sorted(owners.items()):
        for i in range(len(sids)):
            for j in range(i + 1, len(sids)):
                a, b = sids[i], sids[j]
                wa = steps_by_id[a].get("workstream")
                wb = steps_by_id[b].get("workstream")
                if wa == wb:
                    continue
                if b in deps.get(a, set()) or a in deps.get(b, set()):
                    continue
                conflicts.append((f, a, wa, b, wb))
    return conflicts


def step_block(step):
    order = ["id", "workstream", "anchor", "change", "why", "risk", "test",
             "pass", "revert", "effort_hours", "depends", "files", "event",
             "tier", "human", "irreversible", "binary_only", "lead_time_days"]
    out = []
    for key in order:
        if key not in step or step[key] in (None, "", [], False):
            continue
        val = step[key]
        if isinstance(val, list):
            val = ", ".join(str(v) for v in val)
        label = key.replace("_", " ").title()
        out.append(f"  {label + ':':<16}{val}")
    return "\n".join(out)


def build_brief(ws, steps, plan, data, all_steps_by_id):
    wsid = ws.get("id")
    branch = ws.get("branch") or f"build/{wsid}"
    wedge = (section(plan, "01-wedge.md", r"the wedge\b")
             or section(plan, "01-wedge.md", r"wedge")
             or "TODO: no wedge found in plan/01-wedge.md")
    blocking = [w for w in data.get("workstreams") or [] if w.get("blocking")]
    contract_paths = sorted({p for w in blocking for p in (w.get("paths") or [])})

    owned = sorted({f for s in steps for f in (s.get("files") or [])})
    others = sorted({f for sid, s in all_steps_by_id.items()
                     for f in (s.get("files") or [])
                     if s.get("workstream") != wsid} - set(owned))

    gates = data.get("gates") or []
    cannot = data.get("cannot_undo") or []
    irreversible = [s["id"] for s in steps if s.get("irreversible")]
    hours = sum(float(s.get("effort_hours") or 0) for s in steps)

    budgets = section(plan, "04-architecture.md", r"budget") or \
        "TODO: budgets not found in plan/04-architecture.md"
    tokens = section(plan, "05-design-language.md", r"^#+\s*tokens")

    out = [f"# Build brief — {wsid}", "",
           f"Branch: `{branch}`  |  {len(steps)} step(s)  |  ~{hours:g}h estimated",
           "", "## Context", "", wedge, ""]

    if ws.get("blocking"):
        out += ["**This workstream blocks every other one.** Nothing else starts "
                "until your commits exist. Land the contract completely and "
                "correctly rather than quickly.", ""]
    else:
        out += ["## The contract", "",
                "Read it and build against it. **Do not modify it.** If a step "
                "seems to need a contract change, stop and report instead of "
                "editing — a contract changed in two places is exactly the "
                "failure this split exists to prevent.", ""]
        if contract_paths:
            out += ["Contract paths (read-only for you):", ""]
            out += [f"- `{p}`" for p in contract_paths]
            out.append("")

    if tokens:
        out += ["## Design tokens", "",
                "Use tokens only. A hardcoded colour, size or spacing value is a "
                "lint error, because that is what keeps every surface consistent.",
                "", tokens, ""]

    out += ["## Your steps", "",
            "In order. One commit per step, so any single step can be reverted "
            "without unpicking the others. A step's test must pass before you "
            "commit it.", ""]
    for s in steps:
        out += [f"### {s.get('id')} — {s.get('anchor', '')}", "",
                "```", step_block(s), "```", ""]

    out += ["## Files you own", ""]
    out += [f"- `{f}`" for f in owned] or ["- (none — this workstream has no code files)"]
    out += ["", "## Do not touch", "",
            "Anything not in your list. These belong to other sessions running "
            "at the same time:", ""]
    out += [f"- `{f}`" for f in others[:40]] or ["- (nothing else is claimed)"]
    if len(others) > 40:
        out.append(f"- ...and {len(others) - 40} more")
    out.append("")

    out += ["## Budgets you must respect", "", budgets, ""]

    if gates:
        out += ["## Project gates (context — not all are yours)", ""]
        for g in gates:
            out.append(f"- `{g.get('check')}` → {g.get('pass')}")
        out.append("")

    if irreversible or cannot:
        out += ["## Irreversible", ""]
        if irreversible:
            out.append(f"These steps cannot be undone: {', '.join(irreversible)}. "
                       "Confirm with the operator before running them.")
            out.append("")
        if cannot:
            out += ["Project-wide, these cannot be undone:", ""]
            out += [f"- {c}" for c in cannot]
            out.append("")

    out += ["## When you are blocked", "",
            "Stop. Commit what passes its test. Report what you need and why. "
            "Do not change the contract, do not take files outside your list, "
            "and do not invent an interface to keep moving — a blocked step is "
            "cheap, a corrupted branch is not.", "",
            "## Done when", "",
            f"Every step above has its test passing and is committed on "
            f"`{branch}`, and nothing outside your file list has changed.", ""]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan_dir")
    ap.add_argument("--out", help="directory for the briefs")
    ap.add_argument("--dry-run", action="store_true",
                    help="check the split and print the plan, write nothing")
    args = ap.parse_args()

    plan = Path(args.plan_dir)
    if not plan.is_dir():
        sys.exit(f"error: {plan} is not a directory")
    data = load(plan)

    steps = data.get("steps") or []
    if not steps:
        sys.exit("error: roadmap.json has no steps")
    by_id = {s.get("id"): s for s in steps if s.get("id")}

    cycle = find_cycle(by_id)
    if cycle:
        print("dependency cycle: " + " -> ".join(cycle),
              file=sys.stderr)
        print("\nWith a cycle the step order is undefined, so the parallel "
              "split cannot be checked. Fix the depends lists and run again.",
              file=sys.stderr)
        return 1

    deps = transitive(by_id)

    conflicts = concurrency_conflicts(by_id, deps)
    if conflicts:
        print(f"{len(conflicts)} file-ownership conflict(s) — refusing to "
              f"generate briefs:\n", file=sys.stderr)
        for f, a, wa, b, wb in conflicts:
            print(f"  {f}\n      claimed by {a} ({wa}) and {b} ({wb}), "
                  f"with no dependency between them", file=sys.stderr)
        print("\nEither add a dependency so one waits, or move the file to a "
              "single workstream.", file=sys.stderr)
        return 1

    workstreams = data.get("workstreams") or []
    declared = {w.get("id") for w in workstreams}
    for sid, step in by_id.items():
        if step.get("workstream") not in declared:
            print(f"warning: step {sid} is in undeclared workstream "
                  f"{step.get('workstream')!r}", file=sys.stderr)
            workstreams.append({"id": step.get("workstream")})
            declared.add(step.get("workstream"))

    blocking = [w for w in workstreams if w.get("blocking")]
    rest = [w for w in workstreams if not w.get("blocking")]
    hours, chain = critical_path(by_id)

    print(f"{len(steps)} steps across {len(workstreams)} workstream(s). "
          "No file-ownership conflicts.\n")
    if blocking:
        print("Wave 1 (must finish first): "
              f"{', '.join(w['id'] for w in blocking)}")
    human = [w['id'] for w in rest if w.get('id') == 'human']
    if human:
        print(f"Start immediately in wall-clock time (lead times): {', '.join(human)}")
    parallel = [w['id'] for w in rest if w.get('id') != 'human']
    if parallel:
        print(f"Wave 2 (in parallel, one session each): {', '.join(parallel)}")
    print(f"\nCritical path: ~{hours:g}h through "
          f"{' -> '.join(chain) if chain else '(none)'}")
    print("That is what one night actually reaches. If the plan claims more, "
          "the cut line is what gives.\n")

    if args.dry_run:
        return 0
    if not args.out:
        sys.exit("error: --out is required unless --dry-run")

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    for ws in workstreams:
        wsid = ws.get("id")
        ws_steps = [s for s in steps if s.get("workstream") == wsid]
        if not ws_steps:
            continue
        path = outdir / f"brief-{wsid}.md"
        path.write_text(build_brief(ws, ws_steps, plan, data, by_id),
                        encoding="utf-8")
        print(f"  wrote {path}  ({len(ws_steps)} steps)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
