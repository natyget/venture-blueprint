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
import contextlib
import csv
import datetime as dt
import hashlib
import importlib.util
import io
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
                         "financial", "organization", "statement of work",
                         "milestones", "long-term", "unverified"],
    "departments.md": ["cross-functional"],
    "validation.md": ["riskiest", "experiment", "pass", "kill", "results"],
}
# Once the founder has chosen, paths.md must record the choice and its reasons.
CHOSEN_EXTRA = {"paths.md": ["choice", "constraint", "rejected"]}

PLAN_DOCS = ["00-brief.md", "paths.md", "01-wedge.md", "02-economics.md",
             "03-compliance.md", "04-architecture.md", "05-design-language.md",
             "06-growth.md", "07-monetization.md", "08-ecosystem.md",
             "departments.md", "validation.md", "10-red-team.md", "business-plan.md"]
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


def load_script(name):
    spec = importlib.util.spec_from_file_location(f"vb_{name}", SKILL / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


DEPT_LABELS = ["what breaks first", "day one", "stack", "who", "agents can run", "kpi"]


def check_departments(plan, rep):
    path = plan / "departments.md"
    if not path.exists():
        return  # reported by check_docs
    text = re.sub(r"<!--.*?-->", "", path.read_text(encoding="utf-8"), flags=re.S)
    try:
        roster = json.loads((SKILL / "templates" / "departments.json")
                            .read_text(encoding="utf-8"))["departments"]
    except (OSError, json.JSONDecodeError, KeyError):
        roster = []
    for d in roster:
        m = re.search(r"(?ms)^##\s+" + re.escape(d["id"]) + r"\b[^\n]*\n(.*?)(?=^## |\Z)", text)
        where = f"departments.md/{d['id']}"
        if not m:
            rep.error(where, f"{d['name']}: section missing — every department is "
                             "planned or marked not applicable with a reason")
            continue
        body = m.group(1).lower()
        if "not applicable" in body:
            if len(body.strip()) < 60:
                rep.error(where, f"{d['name']}: not applicable needs the reason")
            elif not re.search(r"\b(until|revisit|when|once|if)\b", body):
                rep.warn(where, f"{d['name']}: not applicable with no trigger to revisit")
            continue
        for label in DEPT_LABELS:
            if label not in body:
                rep.error(where, f'{d["name"]}: missing "{label}"')


def check_screens(path, label, required, rep):
    if not path.exists():
        if required:
            rep.error(path.name, "missing — the core loop is drawn as a clickable "
                                 "prototype (references/product-preview.md)")
        else:
            rep.warn(path.name, f"no screens for {label} — the paths are easier to "
                                "choose between when each can be seen")
        return
    problems = []
    site = load_script("build_site")
    data = site.load_screens(path, label, problems)
    for pr in problems:
        rep.error(path.name, pr["title"])
    if data is None:
        rep.error(path.name, "no screens in the file")
        return
    if required and len(data["screens"]) < 3:
        rep.error(path.name, f"only {len(data['screens'])} screen(s) — draw the whole "
                             "core loop, the buyer's screen and the money moment")


def check_paths_dir(plan, rep):
    pdir = plan / "paths"
    files = sorted(f for f in pdir.glob("*.json")
                   if not f.name.endswith(".screens.json")) if pdir.is_dir() else []
    if len(files) < 2:
        rep.error("paths/", f"{len(files)} path file(s) — compare at least two genuinely "
                            "different paths, each with its own assumptions")
    model = load_script("model")
    for f in files:
        raw = f.read_text(encoding="utf-8")
        if "TODO" in raw:
            rep.error(f"paths/{f.name}", "still has TODO markers")
            continue
        try:
            a = json.loads(raw)
        except json.JSONDecodeError as exc:
            rep.error(f"paths/{f.name}", f"invalid JSON: {exc}")
            continue
        buf = io.StringIO()
        try:
            with contextlib.redirect_stderr(buf):
                model.validate(a)
        except SystemExit:
            rep.error(f"paths/{f.name}", buf.getvalue().strip().replace("error: ", "") or "invalid")
            continue
        missing = [n for n, b in ([("customers", a.get("customers"))]
                                  + [(l.get("name", "?"), l) for l in a.get("revenue_lines", [])])
                   if source_state(b) == "missing"]
        if missing:
            rep.error(f"paths/{f.name}", f"no source on: {', '.join(missing)} — "
                                         "UNVERIFIED with a reason is fine at this stage")
        check_screens(f.with_name(f"{f.stem}.screens.json"),
                      a.get("path") or f.stem, False, rep)


STORY_KINDS = {
    "explore": {"question", "evidence", "path", "recommendation", "test"},
    "plan": {"problem", "customer", "solution", "why-now", "market", "competition", "model",
             "numbers", "go-to-market", "team", "departments", "compliance", "traction",
             "evidence", "risks", "next"},
}
STORY_REQUIRED = {
    "explore": ["question", "path", "recommendation", "test"],
    "plan": ["problem", "customer", "solution", "market", "competition", "model", "numbers",
             "risks", "next"],
}
VISUALS = {"numbers", "compare", "sensitivity", "screens", "bars", "matrix", "timeline", "quote"}
TONES = {"go", "promising", "caution", "stop"}
STATUSES = {"strong", "partial", "guess", "risk"}
TOKEN = re.compile(r"\{\{\s*([\w-]+)\.([\w-]+)\.([\w-]+)\s*\}\}")


def nwords(s):
    """Words, not punctuation: "A · Consumer app" is three."""
    return sum(1 for w in TOKEN.sub("N", str(s or "")).split() if re.search(r"[^\W_]", w))


def story_metrics(plan):
    """Every path's model metrics, keyed as story tokens address them."""
    site, model = load_script("build_site"), load_script("model")
    files = []
    if (plan / "paths").is_dir():
        files = [(f.stem, f) for f in sorted((plan / "paths").glob("*.json"))
                 if not f.name.endswith(".screens.json") and not f.stem.endswith("-financials")]
    if (plan / "assumptions.json").exists():
        files.append(("plan", plan / "assumptions.json"))
    out, inputs = {}, {}
    for pid, f in files:
        try:
            raw = f.read_text(encoding="utf-8")
            if "TODO" in raw:
                continue
            a = json.loads(raw)
            with contextlib.redirect_stderr(io.StringIO()):
                model.validate(a)
        except (OSError, json.JSONDecodeError, SystemExit):
            continue
        out[pid], inputs[pid] = site.path_metrics(model, a), a
    return out, inputs, site.SCEN_ALIAS


def check_story(plan, stage, rep):
    path = plan / "story.json"
    if not path.exists():
        rep.error("story.json", "missing — the venture site tells the case from it "
                                "(references/presentation.md)")
        return
    raw = path.read_text(encoding="utf-8")
    if "TODO" in raw:
        rep.error("story.json", "still has TODO markers")
        return
    try:
        s = json.loads(raw)
    except json.JSONDecodeError as exc:
        rep.error("story.json", f"invalid JSON: {exc}")
        return
    key = "explore" if stage == "explore" else "plan"
    if not nwords(s.get("oneliner")):
        rep.error("story.json", "no oneliner — what this is and for whom")
    elif nwords(s.get("oneliner")) > 16:
        rep.error("story.json", f"oneliner is {nwords(s.get('oneliner'))} words; keep it to 16")
    v = s.get("verdict") or {}
    if v.get("tone") not in TONES:
        rep.error("story.json", f"verdict.tone must be one of {sorted(TONES)}")
    if not nwords(v.get("label")) or nwords(v.get("label")) > 6:
        rep.error("story.json", "verdict.label: 1-6 words")
    if nwords(v.get("reason")) > 20:
        rep.error("story.json", f"verdict.reason is {nwords(v.get('reason'))} words; keep it to 20")
    if not nwords(s.get("next")):
        rep.warn("story.json", "no next step")

    metrics, inputs, alias = story_metrics(plan)
    beats = s.get("beats") or []
    if not beats:
        rep.error("story.json", "no beats")
        return
    kinds = []
    for i, b in enumerate(beats):
        where = f"story.json/{b.get('id') or i}"
        kind = b.get("kind")
        kinds.append(kind)
        if kind not in STORY_KINDS[key]:
            rep.error(where, f"kind {kind!r} isn't part of the {key} story: "
                             f"{', '.join(sorted(STORY_KINDS[key]))}")
        if not 1 <= nwords(b.get("kicker")) <= 3:
            rep.error(where, "kicker: 1-3 words")
        tw = nwords(b.get("title"))
        if tw < 4:
            rep.error(where, "title must be a sentence that states the point, not a label")
        elif tw > 14:
            rep.error(where, f"title is {tw} words; keep it to 14")
        status = b.get("status")
        if status not in STATUSES:
            rep.error(where, f"status must be one of {sorted(STATUSES)}")
        srcs = b.get("sources") or []
        if status == "strong" and not any(x.get("url") and x.get("date") for x in srcs):
            rep.error(where, "status 'strong' needs at least one source with a url and a date")
        for x in srcs:
            if x.get("url") and not x.get("date"):
                rep.warn(where, f"source {x.get('label', '?')!r} has no date read")
        pts = b.get("points") or []
        if len(pts) > 3:
            rep.error(where, f"{len(pts)} points; three is the ceiling")
        for pt in pts:
            if nwords(pt) > 14:
                rep.error(where, f"point is {nwords(pt)} words (max 14): {str(pt)[:60]}")
        kpi = b.get("kpi") or {}
        if kpi and nwords(kpi.get("label")) > 6:
            rep.error(where, "kpi.label: keep it to 6 words")
        if kpi and re.search(r"[$€£]\s?\d", str(kpi.get("value", ""))) \
                and not TOKEN.search(str(kpi.get("value", ""))) and not srcs:
            rep.warn(where, f"kpi {kpi.get('value')!r} is typed by hand — a model figure "
                            "should be a token, a research figure needs a source")
        chain = b.get("chain") or []
        if chain and not 2 <= len(chain) <= 4:
            rep.error(where, "chain: 2-4 steps")
        for c in chain:
            if nwords(c.get("label")) > 6:
                rep.error(where, f"chain label too long: {str(c.get('label'))[:50]}")
        facts = b.get("facts") or []
        if len(facts) > 6:
            rep.warn(where, f"{len(facts)} facts; the map shows six")
        vis = b.get("visual") or {}
        if vis:
            if vis.get("type") not in VISUALS:
                rep.error(where, f"visual.type must be one of {sorted(VISUALS)}")
            ref = vis.get("path") or vis.get("set")
            if ref and ref not in metrics:
                rep.error(where, f"visual shows {ref!r}, which isn't a path with valid numbers")
            if vis.get("type") == "screens" and ref:
                sf = (plan / "screens.json") if ref == "plan" else (plan / "paths" / f"{ref}.screens.json")
                if not sf.exists():
                    rep.error(where, f"screens visual for {ref!r}, but {sf.name} doesn't exist")
        if not (kpi or chain or vis):
            rep.warn(where, "only words — give it a number, a chain or a visual")
        blob = json.dumps(b)
        for m in TOKEN.finditer(blob):
            pid, scen, metric = m.group(1), alias.get(m.group(2), m.group(2)), m.group(3)
            if pid not in metrics:
                rep.error(where, f"{m.group(0)}: no path {pid!r} with valid numbers")
            elif scen not in metrics[pid]:
                rep.error(where, f"{m.group(0)}: no scenario {m.group(2)!r}")
            elif metric not in metrics[pid][scen]:
                rep.error(where, f"{m.group(0)}: unknown metric {metric!r}")
        for field in [b.get("title")] + list(pts):
            found = [x.group(0) for x in BANNED.finditer(str(field or ""))]
            if found:
                rep.warn(where, f"slogan wording {', '.join(dict.fromkeys(found))} — say the concrete thing")

    for req in STORY_REQUIRED[key]:
        if req not in kinds:
            rep.error("story.json", f"no '{req}' beat — the {key} story needs: "
                                    f"{', '.join(STORY_REQUIRED[key])}")
    firsts = [kinds.index(k) for k in STORY_REQUIRED[key] if k in kinds]
    if firsts != sorted(firsts):
        rep.error("story.json", "beats are out of order — tell it as: "
                                f"{' → '.join(STORY_REQUIRED[key])}")
    if key == "explore" and kinds.count("path") < 2:
        rep.error("story.json", "one beat per path, at least two")

    primary = inputs.get("plan") or next((a for a in inputs.values() if a.get("recommended")), None) \
        or next(iter(inputs.values()), None)
    if primary and v.get("tone") == "go":
        blocks = ([primary.get("customers")] + list(primary.get("revenue_lines") or [])
                  + list(primary.get("variable_costs") or []) + list(primary.get("fixed_costs") or []))
        guesses = sum(1 for bl in blocks if source_state(bl) != "ok")
        if guesses * 2 > len(blocks):
            rep.error("story.json", f"verdict 'go' while {guesses} of {len(blocks)} model inputs "
                                    "are unverified — say 'promising' until the riskiest are tested")


def check_site(plan, rep):
    page = plan / "venture.html"
    if not page.exists():
        rep.warn("venture.html", "missing — run build_site.py so the founder can click "
                                 "through the plan")
        return
    m = re.search(r"vb-inputs:\s*([0-9a-f]+)", page.read_text(encoding="utf-8")[:2000])
    if not m or m.group(1) != load_script("build_site").inputs_digest(plan):
        rep.warn("venture.html", "older than the plan files — rerun build_site.py so "
                                 "the founder isn't looking at stale numbers")


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

    if stage == "explore":
        check_paths_dir(plan, rep)
    if stage in ("plan", "build"):
        check_departments(plan, rep)
        check_screens(plan / "screens.json", "the chosen plan", True, rep)
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

    check_story(plan, stage, rep)
    check_site(plan, rep)

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
