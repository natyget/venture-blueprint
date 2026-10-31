#!/usr/bin/env python3
"""Build the venture site: the plan as a map you can read at a glance and a
story you can present.

Writes one self-contained HTML file (no network, nothing to install), laid out
as a single window on a desk:

  Map     the venture at the centre and each beat of its case branching out.
          Position is hierarchy: the answer in the middle, the reasons around
          it, the facts at the tips. Moss shows the evidence: green where a
          beat is backed by sources, withered where it is still a guess.
          Click any branch for its point, its number and its sources.
  Story   the same beats as a presentation, one idea per slide: a sentence
          headline that states the point, one number, an X -> Y -> Z chain, at
          most three short points, the visual that proves it, and the sources.

The words come from plan/story.json, written by the planner following
references/presentation.md. Numbers in the story are written as tokens like
{{plan.base.break_even}} and filled in here from model.py, so a headline can
never quote a figure the projections don't support. Charts run the same model
as model.py and check themselves against it on load.

Inputs, whichever exist in the plan folder:
  story.json                                   the narrative (falls back to an outline)
  paths/<id>.json, paths/<id>.screens.json     Stage 1 paths and their screens
  assumptions.json, screens.json               the chosen plan and its screens
  business-plan.md, paths.md, departments.md, validation.md   readable documents
  traps.csv, compliance.csv                    gaps

Usage:  python3 -I scripts/build_site.py <plan-dir> [--out <file.html>]
"""

import argparse
import csv
import datetime as dt
import hashlib
import html
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

DOCS = [  # id, label, file
    ("plan", "Business plan", "business-plan.md"),
    ("paths", "Paths", "paths.md"),
    ("company", "Departments", "departments.md"),
    ("validation", "Validation", "validation.md"),
]
DIGEST_FILES = ["story.json", "assumptions.json", "screens.json", "business-plan.md",
                "paths.md", "departments.md", "validation.md", "traps.csv", "compliance.csv"]
DEFAULT_TOKENS = {"bg": "#f2f2f7", "surface": "#ffffff", "text": "#000000",
                  "muted": "#8e8e93", "accent": "#007aff", "accent_fg": "#ffffff",
                  "border": "rgba(60,60,67,0.18)", "radius": 12,
                  "font": "-apple-system, BlinkMacSystemFont, 'SF Pro Text', system-ui, sans-serif"}
SCEN_ALIAS = {"bad": "conservative", "expected": "base", "great": "optimistic"}
TONES = {"go", "promising", "caution", "stop"}
STATUSES = {"strong", "partial", "guess", "risk"}


def load_model():
    spec = importlib.util.spec_from_file_location("vb_model", HERE / "model.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def inputs_digest(plan):
    """Fingerprint of everything the site is built from, so staleness is detectable."""
    h = hashlib.sha256()
    files = [plan / f for f in DIGEST_FILES]
    if (plan / "paths").is_dir():
        files += sorted(p for p in (plan / "paths").glob("*.json")
                        if not p.stem.endswith("-financials"))
    for f in files:
        if f.exists():
            h.update(f.name.encode() + b"\0" + f.read_bytes() + b"\0")
    return h.hexdigest()[:16]


# --- markdown, enough for plan documents --------------------------------------

def md_inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", s)
    s = re.sub(r"(?<![\w])_(?!\s)(.+?)(?<!\s)_(?![\w])", r"<i>\1</i>", s)

    def link(m):
        text, url = m.group(1), m.group(2)
        if not re.match(r"^(https?://|mailto:)", url):
            return text
        return f'<a href="{url}" target="_blank" rel="noopener">{text}</a>'
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, s)
    s = re.sub(r'(?<!["\'=>])(https?://[^\s<)]+)',
               r'<a href="\1" target="_blank" rel="noopener">\1</a>', s)
    return s


def _cells(row):
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|"):
        row = row[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", row)]


LIST_RE = re.compile(r"^\s*([-*+]|\d+[.)])\s+")
BLOCK_RE = re.compile(r"^(#{1,6}\s|```|>|\s*([-*+]|\d+[.)])\s+|\s*\|)")


def md_to_html(text):
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    lines, out, toc, seen, i = text.splitlines(), [], [], set(), 0

    def slug(s):
        base = re.sub(r"[^a-z0-9]+", "-", re.sub(r"<[^>]+>", "", s).lower()).strip("-") or "s"
        sid, n = base, 2
        while sid in seen:
            sid, n = f"{base}-{n}", n + 1
        seen.add(sid)
        return sid

    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("```"):
            j, buf = i + 1, []
            while j < len(lines) and not lines[j].startswith("```"):
                buf.append(lines[j])
                j += 1
            out.append("<pre><code>" + html.escape("\n".join(buf)) + "</code></pre>")
            i = j + 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            level, txt = len(m.group(1)), m.group(2).strip()
            sid, inner = slug(txt), md_inline(txt)
            if level == 2:
                toc.append([sid, re.sub(r"<[^>]+>", "", inner)])
            out.append(f'<h{level} id="{sid}">{inner}</h{level}>')
            i += 1
            continue
        if (line.lstrip().startswith("|") and i + 1 < len(lines)
                and re.match(r"^\s*\|?\s*:?-{2,}", lines[i + 1])):
            head, i, rows = _cells(line), i + 2, []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append(_cells(lines[i]))
                i += 1
            t = ["<div class='tbl'><table><thead><tr>"]
            t += [f"<th>{md_inline(c)}</th>" for c in head]
            t.append("</tr></thead><tbody>")
            for r in rows:
                t.append("<tr>" + "".join(f"<td>{md_inline(c)}</td>" for c in r) + "</tr>")
            t.append("</tbody></table></div>")
            out.append("".join(t))
            continue
        if LIST_RE.match(line):
            ordered, items = bool(re.match(r"^\s*\d+[.)]", line)), []
            while i < len(lines) and (LIST_RE.match(lines[i]) or
                                      (items and lines[i].startswith("  ") and lines[i].strip())):
                if LIST_RE.match(lines[i]):
                    items.append(LIST_RE.sub("", lines[i]))
                else:
                    items[-1] += " " + lines[i].strip()
                i += 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{md_inline(x)}</li>" for x in items) + f"</{tag}>")
            continue
        if line.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip(">").strip())
                i += 1
            out.append("<blockquote>" + md_inline(" ".join(buf)) + "</blockquote>")
            continue
        if re.match(r"^\s*(-{3,}|\*{3,})\s*$", line):
            out.append("<hr>")
            i += 1
            continue
        buf = []
        while i < len(lines) and lines[i].strip() and not BLOCK_RE.match(lines[i]):
            buf.append(lines[i].strip())
            i += 1
        if not buf:
            buf, i = [line.strip()], i + 1
        out.append("<p>" + md_inline(" ".join(buf)) + "</p>")
    return "\n".join(out), toc


def strip_unfilled(text):
    parts = re.split(r"(?m)^(?=## )", text)
    kept = []
    for part in parts:
        body = re.sub(r"<!--.*?-->", "", part, flags=re.S)
        body = re.sub(r"^## .*$", "", body, count=1, flags=re.M).strip()
        if part.startswith("## ") and (not body or body == "TODO: fill this in."):
            continue
        kept.append(part.replace("TODO: fill this in.", ""))
    return "".join(kept)


# --- screens ------------------------------------------------------------------

def clean_html(h):
    h = re.sub(r"<\s*(script|style|iframe|object|embed|form)\b[^>]*>.*?<\s*/\s*\1\s*>", "",
               h, flags=re.S | re.I)
    h = re.sub(r"<\s*/?\s*(script|style|iframe|object|embed|link|meta|base|form)\b[^>]*>", "",
               h, flags=re.I)
    h = re.sub(r"\son\w+\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", "", h, flags=re.I)
    h = re.sub(r"(href|src)\s*=\s*([\"'])\s*javascript:[^\"']*\2", r'\1="#"', h, flags=re.I)
    return h


def load_screens(path, label, problems):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        problems.append({"severity": "high", "title": f"{path.name} is not valid JSON",
                         "detail": str(exc), "where": path.name})
        return None
    screens, ids = [], []
    for s in data.get("screens") or []:
        sid = str(s.get("id") or "").strip()
        if not sid:
            continue
        if sid in ids:
            problems.append({"severity": "medium", "title": f"Duplicate screen id '{sid}'",
                             "detail": f"In {label}.", "where": path.name})
            continue
        ids.append(sid)
        screens.append({"id": sid, "title": s.get("title") or sid,
                        "for": s.get("for", ""), "notes": s.get("notes", ""),
                        "html": clean_html(str(s.get("html") or ""))})
    if not screens:
        return None
    for s in screens:
        for tgt in re.findall(r'data-go\s*=\s*["\']([^"\']+)', s["html"]):
            if tgt not in ids:
                problems.append({"severity": "medium",
                                 "title": f"Screen '{s['id']}' links to '{tgt}', which doesn't exist",
                                 "detail": f"In the {label} screens.", "where": path.name})
    start = data.get("start") if data.get("start") in ids else ids[0]
    flows = []
    for f in data.get("flows") or []:
        steps = [x for x in f.get("steps") or [] if x in ids]
        missing = [x for x in f.get("steps") or [] if x not in ids]
        if missing:
            problems.append({"severity": "medium",
                             "title": f"Flow '{f.get('name', '?')}' uses missing screens",
                             "detail": ", ".join(missing), "where": path.name})
        if len(steps) >= 2:
            flows.append({"name": f.get("name") or "Flow", "steps": steps})
    tokens = dict(DEFAULT_TOKENS)
    tokens.update({k: v for k, v in (data.get("tokens") or {}).items() if v is not None})
    platform = data.get("platform") if data.get("platform") in ("ios", "android", "web") else "ios"
    hero = [x for x in (data.get("hero") or []) if x in ids] or ids[:3]
    return {"label": label, "platform": platform, "tokens": tokens, "start": start,
            "flows": flows, "screens": screens, "hero": hero}


# --- gaps ---------------------------------------------------------------------

def static_gaps(plan, stage):
    gaps = []
    if stage == "explore":
        return gaps  # traps, compliance and departments belong to the plan stage
    traps = plan / "traps.csv"
    if traps.exists():
        rows = list(csv.DictReader(traps.open(encoding="utf-8")))
        open_rows = [r for r in rows if (r.get("status") or "").strip().lower()
                     not in ("answered", "n/a")]
        if open_rows:
            gaps.append({"severity": "high",
                         "title": f"{len(open_rows)} of {len(rows)} trap questions unanswered",
                         "detail": "Third-party rules that can decide margin or legality.",
                         "where": "traps.csv"})
    comp = plan / "compliance.csv"
    if comp.exists():
        rows = list(csv.DictReader(comp.open(encoding="utf-8")))
        counsel = [r.get("regime", "?") for r in rows
                   if (r.get("counsel") or "").strip().lower() == "required"]
        if counsel:
            gaps.append({"severity": "medium",
                         "title": f"{len(counsel)} obligation(s) need a lawyer",
                         "detail": "; ".join(counsel[:4]), "where": "compliance.csv"})
    deps = plan / "departments.md"
    if deps.exists():
        text = deps.read_text(encoding="utf-8")
        todo = [m.group(1).split(" ", 1)[1]
                for m in re.finditer(r"(?ms)^## (D\d\d [^\n]+)\n(.*?)(?=^## |\Z)", text)
                if "TODO" in m.group(2)]
        if todo and len(todo) < 16:
            gaps.append({"severity": "medium",
                         "title": f"{len(todo)} department(s) not planned yet",
                         "detail": ", ".join(todo[:6]), "where": "departments.md"})
    return gaps


def detect_stage(plan):
    try:
        if json.loads((plan / "roadmap.json").read_text(encoding="utf-8")).get("steps"):
            return "build"
    except (OSError, json.JSONDecodeError):
        pass
    a = plan / "assumptions.json"
    if a.exists() and "TODO" not in a.read_text(encoding="utf-8"):
        return "plan"
    return "explore"


# --- numbers for the story ----------------------------------------------------

def money(x, cur="USD"):
    sym = "$" if cur in ("USD", None, "") else f"{cur} "
    s, v = ("−" if x < 0 else ""), abs(x)
    if v >= 1e6:
        return f"{s}{sym}{v / 1e6:.1f}M".replace(".0M", "M")
    if v >= 1e4:
        return f"{s}{sym}{round(v / 1e3)}k"
    if v >= 1e3:
        return f"{s}{sym}{v / 1e3:.1f}k".replace(".0k", "k")
    return f"{s}{sym}{v:,.0f}" if v >= 10 else f"{s}{sym}{v:,.2f}"


def path_metrics(model, a):
    out, cur = {}, a.get("currency", "USD")
    months = int(a.get("months", 36))
    for name, sc in (a.get("scenarios") or model.DEFAULT_SCENARIOS).items():
        rows = model.run(a, sc)
        ue = model.unit_economics(a, sc)
        be = next((r["month"] for r in rows if r["net"] >= 0), None)
        low = min(r["cash"] for r in rows)
        last = rows[-1]
        out[name] = {
            "break_even": f"month {be}" if be else f"not within {months} months",
            "funding": money(-low, cur) if low < 0 else "none",
            "revenue_end": money(last["gross_revenue"], cur) + "/mo",
            "customers_end": f"{round(last['active']):,}",
            "cash_end": money(last["cash"], cur),
            "cash_low": money(low, cur),
            "payback": f"{ue['payback']:.1f} months" if ue["payback"] else "never",
            "ltv_cac": f"{ue['ltv_cac']:.1f}×" if ue["ltv_cac"] else "n/a",
            "margin": money(ue["margin"], cur) + "/mo",
            "price": money(ue["revenue"], cur) + "/mo",
            "cac": money(ue["cac"], cur),
            "churn": f"{ue['churn'] * 100:.1f}%/mo",
        }
    return out


TOKEN_RE = re.compile(r"\{\{\s*([\w-]+)\.([\w-]+)\.([\w-]+)\s*\}\}")


def resolve(text, metrics, problems, where):
    if not isinstance(text, str):
        return text

    def sub(m):
        pid, scen, key = m.group(1), m.group(2), m.group(3)
        scen = SCEN_ALIAS.get(scen, scen)
        try:
            return metrics[pid][scen][key]
        except KeyError:
            problems.append({"severity": "high", "title": f"Unknown number {m.group(0)}",
                             "detail": f"In {where}. Use a path id, a scenario (bad, base, great) "
                                       "and a metric the model provides.",
                             "where": "story.json"})
            return "?"
    return TOKEN_RE.sub(sub, text)


def resolve_tree(node, metrics, problems, where):
    if isinstance(node, str):
        return resolve(node, metrics, problems, where)
    if isinstance(node, list):
        return [resolve_tree(x, metrics, problems, where) for x in node]
    if isinstance(node, dict):
        return {k: resolve_tree(v, metrics, problems, f"{where}.{k}") for k, v in node.items()}
    return node


def fallback_story(paths, stage):
    """An outline when story.json hasn't been written yet."""
    beats = []
    for p in paths:
        beats.append({"id": p["id"], "kind": "path", "kicker": p["name"][:24],
                      "title": p["summary"] or p["name"], "status": "guess",
                      "kpi": {"value": f"{{{{{p['id']}.base.break_even}}}}", "label": "pays for itself"},
                      "points": [], "visual": {"type": "numbers", "path": p["id"]}, "sources": []})
    return {"oneliner": "", "verdict": {"tone": "caution", "label": "No story written yet",
                                        "reason": "Write plan/story.json to tell the case."},
            "next": "Write the story, then rebuild this page.", "beats": beats}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan_dir")
    ap.add_argument("--out", help="default: <plan-dir>/venture.html")
    args = ap.parse_args()

    plan = Path(args.plan_dir)
    if not plan.is_dir():
        sys.exit(f"error: {plan} is not a directory")
    model = load_model()
    problems, skipped = [], []

    sources = []
    if (plan / "paths").is_dir():
        sources = sorted(p for p in (plan / "paths").glob("*.json")
                         if not p.stem.endswith("-financials") and not p.name.endswith(".screens.json"))
    main_file = plan / "assumptions.json"
    if main_file.exists():
        sources.append(main_file)

    paths, metrics = [], {}
    for src in sources:
        try:
            a = json.loads(src.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            skipped.append(f"{src.name}: invalid JSON ({exc})")
            continue
        if "TODO" in json.dumps(a):
            skipped.append(f"{src.name}: still the unfilled template")
            continue
        try:
            model.validate(a)
        except SystemExit:
            skipped.append(f"{src.name}: failed validation — run model.py on it to see why")
            continue
        scenarios = a.get("scenarios") or model.DEFAULT_SCENARIOS
        expected = {}
        for name, sc in scenarios.items():
            rows = model.run(a, sc)
            expected[name] = {"break_even": next((r["month"] for r in rows if r["net"] >= 0), None),
                              "low_cash": min(r["cash"] for r in rows),
                              "final_cash": rows[-1]["cash"],
                              "final_revenue": rows[-1]["gross_revenue"]}
        is_main = src == main_file
        pid = "plan" if is_main else src.stem
        screens_file = (plan / "screens.json") if is_main else src.with_name(f"{src.stem}.screens.json")
        label = "the chosen plan" if is_main else (a.get("path") or src.stem)
        screens = load_screens(screens_file, label, problems) if screens_file.exists() else None
        metrics[pid] = path_metrics(model, a)
        paths.append({"id": pid, "name": a.get("path") or ("Chosen plan" if is_main else src.stem),
                      "summary": a.get("summary", ""), "recommended": bool(a.get("recommended")),
                      "file": str(src.relative_to(plan)), "assumptions": a,
                      "expected": expected, "screens": screens})

    if not paths:
        print("Nothing to show yet:", file=sys.stderr)
        for s in skipped:
            print(f"  skipped {s}", file=sys.stderr)
        return 1

    stage = detect_stage(plan)
    story_file = plan / "story.json"
    story_written = False
    if story_file.exists():
        try:
            story = json.loads(story_file.read_text(encoding="utf-8"))
            story_written = "TODO" not in json.dumps(story)
        except json.JSONDecodeError as exc:
            problems.append({"severity": "high", "title": "story.json is not valid JSON",
                             "detail": str(exc), "where": "story.json"})
            story = None
    else:
        story = None
    if not story_written:
        story = fallback_story(paths, stage)
        problems.append({"severity": "high", "title": "The story hasn't been written",
                         "detail": "This page is showing an automatic outline. Write plan/story.json "
                                   "following references/presentation.md.", "where": "story.json"})
    story = resolve_tree(story, metrics, problems, "story")

    ids = {p["id"] for p in paths}
    for b in story.get("beats") or []:
        v = b.get("visual") or {}
        ref = v.get("path") or v.get("set")
        if ref and ref not in ids:
            problems.append({"severity": "medium",
                             "title": f"Beat '{b.get('id')}' shows '{ref}', which isn't a path",
                             "detail": f"Known: {', '.join(sorted(ids))}.", "where": "story.json"})
        if v.get("type") == "screens":
            p = next((p for p in paths if p["id"] == ref), None)
            if p and not p["screens"]:
                problems.append({"severity": "medium",
                                 "title": f"Beat '{b.get('id')}' shows screens for '{ref}', which has none",
                                 "detail": "Draw them first (references/product-preview.md).",
                                 "where": "story.json"})

    docs = []
    for did, label, fname in DOCS:
        f = plan / fname
        if not f.exists():
            continue
        raw = f.read_text(encoding="utf-8")
        if raw.count("TODO: fill this in.") * 2 >= max(1, len(re.findall(r"(?m)^## ", raw))):
            continue
        body, toc = md_to_html(strip_unfilled(raw))
        if toc:
            docs.append({"id": did, "label": label, "file": fname, "html": body, "toc": toc})

    primary = next((i for i, p in enumerate(paths) if p["id"] == "plan"), None)
    if primary is None:
        primary = next((i for i, p in enumerate(paths) if p["recommended"]), 0)

    venture = (story.get("venture")
               or next((p["assumptions"].get("venture") for p in paths if p["assumptions"].get("venture")), None)
               or plan.resolve().name)
    data = {"venture": venture, "stage": stage, "generated": dt.date.today().isoformat(),
            "primary": primary, "paths": paths, "story": story, "docs": docs,
            "gaps": static_gaps(plan, stage) + problems}
    blob = json.dumps(data).replace("</", "<\\/")
    page = (TEMPLATE.replace("__TITLE__", html.escape(str(venture)))
                    .replace("__DIGEST__", inputs_digest(plan))
                    .replace("__DATA__", blob))
    out = Path(args.out) if args.out else plan / "venture.html"
    out.write_text(page, encoding="utf-8")
    beats = story.get("beats") or []
    print(f"Wrote {out}")
    print(f"  {len(beats)} beat(s), {len(paths)} path(s), "
          f"{sum(len(p['screens']['screens']) for p in paths if p['screens'])} screen(s), "
          f"{len(docs)} document(s), stage: {stage}")
    for s in skipped:
        print(f"  skipped {s}")
    for p in problems:
        print(f"  note: {p['title']}")
    print("Open it in a browser. It runs entirely on the page; nothing is sent anywhere.")
    return 0


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<!-- vb-inputs: __DIGEST__ -->
<title>__TITLE__</title>
<style>
/* One window on a quiet desk. The venture sits in the middle; the case grows out of it as moss. */
:root{
  --desk:#e8eaed;--win:#ffffff;--bar:#f7f7f8;--ink:#1d1d1f;--ink2:#6e6e73;--ink3:#a1a1a6;
  --hair:rgba(0,0,0,.09);--well:#f2f2f5;--dot:#e3e4e8;--sel:#0071e3;--onsel:#fff;--danger:#d70015;
  --glass:rgba(252,252,253,.84);
  --moss0:#1f2d16;--moss1:#3b5a1d;--moss2:#5d9527;--moss3:#92cd3d;--moss4:#d2f169;--tip:#e8c93a;--seed:#a1a1a6;--wither:#a9987a;
  --shadow:0 0 0 .5px rgba(0,0,0,.16),0 28px 80px rgba(28,34,48,.2),0 8px 22px rgba(28,34,48,.08);
  --pop:0 0 0 .5px rgba(0,0,0,.12),0 12px 40px rgba(28,34,48,.18);
  --font:-apple-system,BlinkMacSystemFont,"SF Pro Text","Helvetica Neue",Helvetica,Arial,sans-serif;
  --display:-apple-system,BlinkMacSystemFont,"SF Pro Display","Helvetica Neue",Helvetica,Arial,sans-serif;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
}
@media (prefers-color-scheme:dark){:root{
  --desk:#0d0e10;--win:#1c1c1e;--bar:#232326;--ink:#f5f5f7;--ink2:#a1a1a6;--ink3:#6c6c71;
  --hair:rgba(255,255,255,.1);--well:#2a2a2d;--dot:#2b2c30;--sel:#0a84ff;--danger:#ff453a;--glass:rgba(36,36,39,.86);
  --moss0:#2a4220;--moss1:#47742a;--moss2:#6fae33;--moss3:#a5e04b;--moss4:#e1ff88;--tip:#fff07a;--seed:#5e5e63;--wither:#8c7d62;
  --shadow:0 0 0 .5px rgba(255,255,255,.12),0 28px 80px rgba(0,0,0,.55);--pop:0 0 0 .5px rgba(255,255,255,.14),0 12px 40px rgba(0,0,0,.5);
  color-scheme:dark;}}
*{box-sizing:border-box}
html,body{height:100%;margin:0}
body{background:var(--desk);color:var(--ink);font:13px/1.4 var(--font);-webkit-font-smoothing:antialiased;overflow:hidden}
button{font:inherit;color:inherit}
:focus-visible{outline:3px solid color-mix(in srgb,var(--sel) 45%,transparent);outline-offset:1px;border-radius:6px}
svg.i{width:1em;height:1em;stroke:currentColor;fill:none;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round;flex:none}

.win{position:fixed;inset:max(18px,env(safe-area-inset-top,0px)) max(18px,env(safe-area-inset-right,0px)) max(18px,env(safe-area-inset-bottom,0px)) max(18px,env(safe-area-inset-left,0px));
  background:var(--win);border-radius:12px;box-shadow:var(--shadow);display:grid;grid-template-rows:52px 1fr 28px;overflow:hidden}
.bar{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;padding:0 12px 0 18px;border-bottom:.5px solid var(--hair);position:relative;z-index:6}
.lights{display:flex;gap:8px}.lights i{width:12px;height:12px;border-radius:50%;box-shadow:inset 0 0 0 .5px rgba(0,0,0,.18)}
.ttl{display:flex;align-items:center;gap:8px;font-weight:600;font-size:13px;white-space:nowrap}
.tools{display:flex;align-items:center;justify-content:flex-end;gap:6px}
.seg{display:inline-flex;background:var(--well);border-radius:8px;padding:2px}
.seg button{border:0;background:transparent;height:24px;padding:0 12px;border-radius:6px;font-size:12.5px;cursor:pointer;display:inline-flex;align-items:center;gap:6px}
.seg button[aria-pressed=true]{background:var(--win);box-shadow:0 1px 2px rgba(0,0,0,.12),0 0 0 .5px rgba(0,0,0,.05);font-weight:600}
.tb{height:28px;min-width:28px;padding:0 8px;border:0;border-radius:6px;background:transparent;color:var(--ink2);display:inline-flex;align-items:center;gap:6px;cursor:pointer;font-size:12.5px}
.tb:hover,.tb[aria-expanded=true]{background:var(--well);color:var(--ink)}
.tb svg{width:16px;height:16px}
.stage{position:relative;overflow:hidden;background:var(--win)}
.foot{display:flex;align-items:center;justify-content:center;gap:14px;font-size:11px;color:var(--ink2);background:var(--bar);border-top:.5px solid var(--hair);padding:0 12px;white-space:nowrap;overflow:hidden;font-variant-numeric:tabular-nums}
.foot .sp{color:var(--ink3)}
.lg{display:inline-flex;align-items:center;gap:5px}.lg i{width:8px;height:8px;border-radius:2px;display:inline-block}

/* map */
#map{position:absolute;inset:0;width:100%;height:100%;display:block;cursor:grab;touch-action:none}
#map.grab{cursor:grabbing}
#map text{font-family:var(--font);fill:var(--ink)}
.node{cursor:pointer}
.node .lbl{font-size:13px;font-weight:600}
.node .num{font-size:11px;fill:var(--ink3);font-weight:500}
.node:hover .lbl{fill:var(--sel)}
.node.sel .lbl{fill:var(--sel)}
.leaf text{font-size:10.5px;fill:var(--ink2)}
.hint{position:absolute;left:50%;bottom:16px;transform:translateX(-50%);color:var(--ink3);font-size:12px;pointer-events:none;transition:opacity .4s}
.maptools{position:absolute;left:14px;bottom:14px;display:flex;gap:4px;z-index:3}
.maptools button{width:28px;height:28px;border:0;border-radius:7px;background:var(--glass);box-shadow:var(--pop);-webkit-backdrop-filter:blur(20px);backdrop-filter:blur(20px);color:var(--ink2);cursor:pointer;display:grid;place-items:center}

/* inspector */
.info{position:absolute;top:12px;right:12px;bottom:12px;width:360px;z-index:8;background:var(--glass);-webkit-backdrop-filter:blur(28px) saturate(1.6);backdrop-filter:blur(28px) saturate(1.6);
  border-radius:12px;box-shadow:var(--pop);display:flex;flex-direction:column;overflow:hidden;transform:translateX(0);transition:transform .25s ease,opacity .25s}
.info[hidden]{display:flex!important;transform:translateX(calc(100% + 24px));opacity:0;pointer-events:none}
.info-x{position:absolute;top:10px;right:10px;width:22px;height:22px;border-radius:50%;border:0;background:var(--well);color:var(--ink2);display:grid;place-items:center;z-index:2;cursor:pointer}
.info-b{overflow:auto;padding:22px 20px 20px;display:flex;flex-direction:column;gap:16px;overscroll-behavior:contain}
.kick{display:flex;align-items:center;gap:7px;font-size:11px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:var(--ink3)}
.sdot{width:8px;height:8px;border-radius:2px;display:inline-block;flex:none}
.p-title{margin:0;font:600 20px/1.22 var(--display);letter-spacing:-.015em;text-wrap:balance}
.kpi .v{font:700 40px/1 var(--display);letter-spacing:-.03em}
.kpi .l{font-size:13px;color:var(--ink2);margin-top:4px}
.kpi .n{font-size:12px;color:var(--ink3);margin-top:2px}
.chain{display:flex;align-items:stretch;gap:0;flex-wrap:wrap}
.chain .c{display:flex;flex-direction:column;min-width:0}
.chain .c b{font:700 19px/1.1 var(--display);letter-spacing:-.02em}
.chain .c span{font-size:11.5px;color:var(--ink2);margin-top:2px;line-height:1.25}
.chain .ar{color:var(--ink3);padding:2px 10px 0;font-size:16px}
.pts{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:8px}
.pts li{display:grid;grid-template-columns:16px 1fr;gap:6px;font-size:14px;line-height:1.4}
.pts li::before{content:"";width:6px;height:6px;border-radius:2px;background:var(--moss2);margin-top:7px}
.cap{font-size:11px;font-weight:600;color:var(--ink3);margin:0 0 6px}
.srcs{display:flex;flex-direction:column;gap:4px;font-size:12px}
.srcs a,.srcs span{color:var(--ink2);text-decoration:none;display:flex;gap:6px;align-items:baseline}
.srcs a:hover{color:var(--sel)}
.srcs .d{color:var(--ink3);font-variant-numeric:tabular-nums;white-space:nowrap;margin-left:auto}
.case{display:flex;flex-direction:column;gap:2px}
.case a{display:grid;grid-template-columns:20px 1fr;gap:10px;align-items:start;text-decoration:none;color:var(--ink);padding:6px;margin:0 -6px;border-radius:7px}
.case a:hover{background:color-mix(in srgb,var(--ink) 6%,transparent)}
.case .n{width:20px;height:20px;border-radius:5px;display:grid;place-items:center;color:#fff;font-size:11px;font-weight:700;margin-top:1px}
.case b{display:block;font-size:13px}.case b+span{display:block;font-size:12.5px;color:var(--ink2);line-height:1.35;margin-top:1px}
.btn{height:30px;padding:0 14px;border-radius:7px;border:0;background:color-mix(in srgb,var(--ink) 7%,transparent);color:var(--ink);font-weight:500;cursor:pointer;display:inline-flex;align-items:center;gap:6px}
.btn.pri{background:var(--sel);color:#fff}
.pill{display:inline-flex;align-items:center;gap:6px;height:24px;padding:0 10px;border-radius:12px;font-size:12px;font-weight:600;
  background:color-mix(in srgb,var(--c) 15%,transparent);color:var(--c)}
.miniv{border-radius:10px;overflow:hidden}

/* story */
#story{position:absolute;inset:0;display:none;flex-direction:column}
#story.on{display:flex}
.slide{flex:1;min-height:0;display:grid;grid-template-rows:auto auto 1fr;padding:44px 64px 18px;gap:22px;animation:fade .35s ease}
@keyframes fade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){.slide{animation:none}}
.s-kick{display:flex;align-items:center;gap:8px;font-size:12px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;color:var(--ink3)}
.s-title{margin:0;font:700 clamp(28px,3.4vw,46px)/1.1 var(--display);letter-spacing:-.03em;max-width:24ch;text-wrap:balance}
.s-body{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:48px;min-height:0;align-items:center}
.s-body.solo{grid-template-columns:minmax(0,1fr);max-width:760px;align-self:start;margin-top:4vh}
.s-left{display:flex;flex-direction:column;gap:26px;min-width:0}
.s-left .kpi .v{font-size:clamp(44px,5.4vw,76px)}
.s-left .kpi .l{font-size:16px}
.s-left .chain .c b{font-size:26px}.s-left .chain .c span{font-size:13px}.s-left .chain .ar{font-size:22px;padding:4px 14px 0}
.s-left .pts li{font-size:17px}
.s-body.wide{grid-template-columns:minmax(0,1fr)}
.s-body.wide .s-right{width:100%;max-width:1000px;margin:0 auto}
.s-right .mtx{font-size:16px}.s-right .mtx th{font-size:13px}.s-right .mtx td{padding:14px 12px}
.s-right .bars .br{font-size:16px}.s-right .bars b{font-size:18px}.s-right .tl .w{font-size:18px}.s-right .tl .x{font-size:15px}
.s-right{min-width:0;min-height:0;height:100%;display:flex;align-items:center;justify-content:center}
.s-foot{display:flex;align-items:center;gap:14px;padding:10px 64px 16px;font-size:11.5px;color:var(--ink3)}
.s-foot .srcline{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.s-foot .srcline a{color:var(--ink3)}
.s-foot .srcline a:hover{color:var(--sel)}
.prog{display:flex;gap:4px}.prog i{width:18px;height:3px;border-radius:2px;background:var(--hair)}.prog i.on{background:var(--ink2)}.prog i.done{background:var(--ink3)}
.nav2{display:flex;gap:6px}
.nav2 button{width:30px;height:30px;border:0;border-radius:8px;background:var(--well);cursor:pointer;display:grid;place-items:center;color:var(--ink)}
.cover{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:18px;padding:40px}
.cover .icon{width:84px;height:84px;border-radius:20px;background:linear-gradient(145deg,var(--moss2),var(--moss1));display:grid;place-items:center;color:#fff;font:700 34px var(--display);box-shadow:0 10px 30px rgba(59,90,29,.35)}
.cover h1{margin:0;font:700 clamp(40px,5vw,64px)/1.05 var(--display);letter-spacing:-.035em}
.cover p{margin:0;font-size:clamp(17px,1.6vw,22px);color:var(--ink2);max-width:34ch;line-height:1.35}

/* visuals */
.vis{width:100%;height:100%;max-height:520px;display:flex;align-items:center;justify-content:center}
.chartbox{width:100%}
.chartbox svg{display:block;width:100%;height:auto}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--ink2);margin-top:8px;align-items:center}
.legend span{display:inline-flex;align-items:center;gap:6px}
.legend i{width:9px;height:9px;border-radius:2px;display:inline-block}
.stats{display:flex;gap:28px;margin-bottom:14px}
.stats div{font-size:12px;color:var(--ink2)}
.stats b{display:block;font:700 22px/1.1 var(--display);color:var(--ink);letter-spacing:-.02em}
.cmp{display:grid;gap:14px;width:100%}
.cmpc{border-radius:12px;background:var(--well);padding:16px;display:flex;flex-direction:column;gap:10px;position:relative}
.cmpc.rec{box-shadow:0 0 0 2px var(--moss2)}
.cmpc h4{margin:0;font:600 15px/1.2 var(--display)}
.cmpc .row3{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.cmpc .row3 div{font-size:11px;color:var(--ink2)}
.cmpc .row3 b{display:block;font:700 16px var(--display);color:var(--ink)}
.spark{display:block;width:100%;height:44px}
.mtx{width:100%;border-collapse:separate;border-spacing:0;font-size:13px}
.mtx th{font-weight:600;color:var(--ink2);text-align:left;padding:8px 10px;font-size:12px}
.mtx td{padding:10px;border-top:.5px solid var(--hair)}
.mtx tr.us td{background:color-mix(in srgb,var(--moss3) 14%,transparent);font-weight:600}
.mtx tr.us td:first-child{border-radius:8px 0 0 8px}.mtx tr.us td:last-child{border-radius:0 8px 8px 0}
.bars{width:100%;display:flex;flex-direction:column;gap:12px}
.bars .br{display:grid;grid-template-columns:minmax(90px,30%) 1fr auto;gap:12px;align-items:center;font-size:13.5px}
.bars .tr{height:14px;border-radius:7px;background:var(--well);overflow:hidden}
.bars .fl{height:100%;border-radius:7px;background:var(--moss2)}
.bars b{font:700 15px var(--display)}
.tl{display:flex;width:100%;gap:0;position:relative}
.tl .st{flex:1;padding:18px 12px 0 0;position:relative;border-top:2px solid var(--hair)}
.tl .st::before{content:"";position:absolute;top:-7px;left:0;width:12px;height:12px;border-radius:50%;background:var(--moss2);box-shadow:0 0 0 3px var(--win)}
.tl .w{font:700 15px var(--display)}.tl .x{font-size:13px;color:var(--ink2);margin-top:4px;line-height:1.35}
.quote{max-width:560px}
.quote q{display:block;font:500 clamp(20px,2.2vw,30px)/1.3 var(--display);letter-spacing:-.015em;quotes:"“" "”"}
.quote .who{margin-top:14px;color:var(--ink2);font-size:14px}
.sens{width:100%;display:flex;flex-direction:column;gap:2px}
.sens .r{display:grid;grid-template-columns:130px 1fr;gap:12px;align-items:center;padding:8px 0;font-size:13.5px}
.sens .tk{position:relative;height:16px}
.sens .mid{position:absolute;left:50%;top:-4px;bottom:-4px;border-left:1px dashed var(--ink3)}
.sens .b{position:absolute;top:2px;height:12px;border-radius:6px}
.sens .r.top{font-weight:700}

/* product imagery */
.hero{position:relative;width:100%;height:100%;min-height:300px;border-radius:18px;overflow:hidden;display:flex;align-items:center;justify-content:center}
.hero .bgw{position:absolute;inset:0}
.hero .row{position:relative;display:flex;align-items:center;justify-content:center}
.dev{position:relative;flex:none}
.dev .inner{position:absolute;top:0;left:0;transform-origin:top left}
.f-ios,.f-android{width:393px;height:852px;border-radius:58px;background:#0b0b0c;padding:11px;box-shadow:0 0 0 1.5px #3a3a3c,0 0 0 4px #1c1c1e,0 40px 80px rgba(0,0,0,.35)}
.f-android{border-radius:40px;padding:9px}
.f-web{width:1180px;height:760px;border-radius:12px;background:#fff;box-shadow:0 0 0 .5px rgba(0,0,0,.2),0 40px 80px rgba(0,0,0,.3);overflow:hidden}
.scr{position:relative;width:100%;height:100%;overflow:hidden;border-radius:47px}
.f-android .scr{border-radius:32px}.f-web .scr{border-radius:0;height:calc(100% - 44px)}
.island{position:absolute;top:11px;left:50%;transform:translateX(-50%);width:124px;height:36px;border-radius:20px;background:#000;z-index:6}
.punch{position:absolute;top:12px;left:50%;transform:translateX(-50%);width:14px;height:14px;border-radius:50%;background:#000;z-index:6}
.status{position:absolute;top:0;left:0;right:0;height:52px;display:flex;align-items:center;justify-content:space-between;padding:4px 36px 0 44px;font:600 16px/1 -apple-system,system-ui,sans-serif;z-index:5}
.status .bat{width:25px;height:12px;border-radius:4px;border:1.5px solid currentColor;position:relative;opacity:.9}
.status .bat::after{content:"";position:absolute;inset:1.5px;right:5px;background:currentColor;border-radius:1.5px}
.homebar{position:absolute;bottom:8px;left:50%;transform:translateX(-50%);width:138px;height:5px;border-radius:3px;z-index:6;opacity:.85}
.webbar{height:44px;display:flex;align-items:center;gap:8px;padding:0 14px;background:#f2f2f5;border-bottom:.5px solid rgba(0,0,0,.1)}
.webbar i{width:12px;height:12px;border-radius:50%;display:inline-block}
.webbar .url{flex:1;max-width:520px;margin:0 auto;background:#fff;border-radius:8px;height:28px;display:flex;align-items:center;justify-content:center;font-size:13px;color:#6e6e73}

/* app screen kit — screens use these classes; colours come from the screen tokens */
.vbd{position:absolute;inset:0;overflow:hidden;background:var(--bg);color:var(--text);font:17px/1.32 var(--font);letter-spacing:-.01em;padding-top:54px;pointer-events:none}
.f-android .vbd{padding-top:36px;font-size:16px}.f-web .vbd{padding:0;font-size:15px}
.vbd *{box-sizing:border-box}
.vbd svg.i{width:22px;height:22px;stroke-width:1.9}
.vbd .bar{display:flex;align-items:center;gap:8px;padding:8px 16px;min-height:44px;font-weight:600;border:0;grid-template-columns:none}
.vbd .bar .t{flex:1;text-align:center;font-size:17px}
.vbd .bar .a{color:var(--accent);display:inline-flex;align-items:center;gap:2px;font-weight:400;min-width:60px}
.vbd .bar .a.r{justify-content:flex-end}
.vbd .title{font-size:34px;font-weight:700;letter-spacing:-.03em;line-height:1.1;padding:4px 16px 10px}
.vbd .sub{font-size:15px;color:var(--muted);padding:0 16px 12px}
.vbd .section-h{font-size:13px;color:var(--muted);text-transform:uppercase;letter-spacing:.03em;padding:18px 32px 7px}
.vbd .h{font-size:22px;font-weight:700;letter-spacing:-.02em;padding:16px 16px 8px}
.vbd .list{background:var(--surface);border-radius:var(--radius);margin:0 16px;overflow:hidden}
.vbd .row{display:flex;align-items:center;gap:12px;padding:11px 16px;min-height:44px;position:relative}
.vbd .row+.row::before{content:"";position:absolute;top:0;left:16px;right:0;border-top:.5px solid var(--border)}
.vbd .row .tx{flex:1;min-width:0}.vbd .row .t{font-size:17px}.vbd .row .s{font-size:14px;color:var(--muted);margin-top:1px}
.vbd .row .r{color:var(--muted);font-size:16px;display:flex;align-items:center;gap:4px}
.vbd .ic{width:30px;height:30px;border-radius:8px;background:var(--accent);color:var(--accent-fg);display:flex;align-items:center;justify-content:center;flex:none}
.vbd .ic svg.i{width:18px;height:18px}
.vbd .card{background:var(--surface);border-radius:calc(var(--radius) + 4px);margin:0 16px 12px;padding:14px;overflow:hidden}
.vbd .img{border-radius:var(--radius);aspect-ratio:16/10;display:flex;align-items:flex-end;padding:10px;font-size:13px;font-weight:600;color:#fff;
  background:linear-gradient(135deg,var(--accent),color-mix(in srgb,var(--accent) 35%,#000));margin-bottom:10px;text-shadow:0 1px 2px rgba(0,0,0,.3)}
.vbd .img.tall{aspect-ratio:4/5}.vbd .img.sq{aspect-ratio:1}.vbd .hero{margin:0 0 12px;border-radius:0;aspect-ratio:4/3}
.vbd .btn{display:block;margin:12px 16px;padding:15px;border-radius:calc(var(--radius) + 2px);background:var(--accent);color:var(--accent-fg);text-align:center;font-weight:600;font-size:17px;height:auto}
.vbd .btn.ghost{background:color-mix(in srgb,var(--accent) 12%,transparent);color:var(--accent)}
.vbd .btn.sm{display:inline-block;margin:0;padding:7px 14px;font-size:15px;border-radius:20px}
.vbd .input{margin:8px 16px;padding:12px 14px;border-radius:var(--radius);background:var(--surface);color:var(--muted);display:flex;align-items:center;gap:8px}
.vbd .search{margin:4px 16px 12px;padding:9px 12px;border-radius:11px;background:color-mix(in srgb,var(--text) 7%,transparent);color:var(--muted);display:flex;align-items:center;gap:8px;font-size:17px;width:auto;height:auto}
.vbd .chips{display:flex;gap:8px;overflow:hidden;padding:4px 16px 12px}
.vbd .chip{padding:7px 14px;border-radius:18px;background:var(--surface);font-size:15px;white-space:nowrap}.vbd .chip.on{background:var(--accent);color:var(--accent-fg)}
.vbd .badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:13px;font-weight:600;background:color-mix(in srgb,var(--accent) 15%,transparent);color:var(--accent)}
.vbd .avatar{width:40px;height:40px;border-radius:50%;background:color-mix(in srgb,var(--accent) 22%,var(--surface));color:var(--accent);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:15px;flex:none}
.vbd .grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:0 16px 12px}.vbd .grid2 .card{margin:0}
.vbd .stat .k{font-size:13px;color:var(--muted)}.vbd .stat .v{font-size:28px;font-weight:700;letter-spacing:-.02em}
.vbd .map{position:relative;height:220px;margin:0 16px 12px;border-radius:var(--radius);overflow:hidden;background-color:color-mix(in srgb,var(--accent) 6%,var(--surface));
  background-image:linear-gradient(color-mix(in srgb,var(--text) 6%,transparent) 1px,transparent 1px),linear-gradient(90deg,color-mix(in srgb,var(--text) 6%,transparent) 1px,transparent 1px);background-size:28px 28px}
.vbd .pin{position:absolute;width:14px;height:14px;border-radius:50%;background:var(--accent);box-shadow:0 0 0 4px color-mix(in srgb,var(--accent) 25%,transparent)}
.vbd .tabbar{position:absolute;left:0;right:0;bottom:0;display:flex;justify-content:space-around;padding:8px 0 30px;background:color-mix(in srgb,var(--surface) 92%,transparent);border-top:.5px solid var(--border)}
.f-android .vbd .tabbar{padding-bottom:14px}
.vbd .tab{display:flex;flex-direction:column;align-items:center;gap:2px;font-size:10.5px;color:var(--muted);min-width:60px}.vbd .tab.on{color:var(--accent)}
.vbd .done{display:flex;flex-direction:column;align-items:center;text-align:center;gap:10px;padding:40px 24px 10px}
.vbd .done .ok{width:72px;height:72px;border-radius:50%;background:var(--accent);color:var(--accent-fg);display:flex;align-items:center;justify-content:center}
.vbd .done .ok svg.i{width:40px;height:40px;stroke-width:2.6}
.vbd .code{font:600 30px/1 ui-monospace,Menlo,monospace;letter-spacing:.12em;text-align:center;padding:14px;margin:8px 16px;border-radius:var(--radius);background:var(--surface)}
.vbd .note{font-size:13px;color:var(--muted);padding:6px 16px}
.vbd .sheet{position:absolute;left:0;right:0;bottom:0;background:var(--surface);border-radius:20px 20px 0 0;padding:6px 0 16px;box-shadow:0 -6px 24px rgba(0,0,0,.08)}
.vbd .divider{height:.5px;background:var(--border);margin:8px 16px}.vbd .spacer{height:16px}
.vbd .web{max-width:1080px;margin:0 auto;padding:24px 32px}
.vbd .webnav{display:flex;align-items:center;gap:24px;padding:14px 32px;border-bottom:.5px solid var(--border);font-size:14px}
.vbd .webnav .logo{font-weight:700;font-size:17px;margin-right:auto}

/* docs + menus */
.pop{position:absolute;background:var(--glass);-webkit-backdrop-filter:blur(24px) saturate(1.6);backdrop-filter:blur(24px) saturate(1.6);border-radius:10px;box-shadow:var(--pop);padding:5px;z-index:20;font-size:13px}
.menu{top:46px;right:12px;width:260px}
.menu button{width:100%;display:grid;grid-template-columns:18px 1fr auto;align-items:center;gap:8px;border:0;background:none;border-radius:5px;padding:5px 8px;text-align:left;cursor:pointer}
.menu button:hover{background:var(--sel);color:#fff}
.menu button:hover .k{color:#fff}
.menu .k{color:var(--ink3);font-size:12px}
.menu .hd{font-size:11px;font-weight:600;color:var(--ink3);padding:6px 8px 2px}
.menu hr{border:0;border-top:.5px solid var(--hair);margin:5px 8px}
.reader{position:absolute;inset:0;z-index:15;background:var(--win);display:grid;grid-template-columns:220px minmax(0,1fr);overflow:hidden}
.reader[hidden]{display:none}
.rtoc{border-right:.5px solid var(--hair);padding:18px 10px;overflow:auto;background:var(--bar)}
.rtoc a{display:block;color:var(--ink2);text-decoration:none;padding:5px 10px;border-radius:6px;font-size:12.5px}
.rtoc a:hover{background:var(--well);color:var(--ink)}
.rtoc .h{font-weight:700;font-size:13px;color:var(--ink);padding:4px 10px 10px}
.art{overflow:auto;padding:34px 56px 60px;font-size:15px;line-height:1.6}
.art>*{max-width:760px}
.art h1{font:700 30px/1.15 var(--display);letter-spacing:-.025em;margin:0 0 16px}
.art h2{font:700 21px/1.2 var(--display);letter-spacing:-.015em;margin:32px 0 8px;scroll-margin-top:16px}
.art h3{font-size:16px;margin:22px 0 6px}.art p{margin:0 0 12px}.art ul,.art ol{padding-left:22px}
.art a{color:var(--sel)}.art code{font:13px var(--mono);background:var(--well);padding:1px 5px;border-radius:5px}
.art blockquote{margin:0 0 12px;padding:2px 14px;border-left:3px solid var(--moss2);color:var(--ink2)}
.tbl{overflow-x:auto;margin:6px 0 16px;border-radius:10px;box-shadow:0 0 0 .5px var(--hair);max-width:none!important}
.art table{border-collapse:collapse;width:100%;font-size:13px;line-height:1.4}
.art th{background:var(--well);text-align:left;font-weight:600;padding:8px 12px}
.art td{padding:8px 12px;border-top:.5px solid var(--hair);vertical-align:top}
.banner{position:absolute;top:10px;left:50%;transform:translateX(-50%);z-index:30;background:color-mix(in srgb,var(--danger) 14%,var(--win));color:var(--danger);padding:8px 14px;border-radius:10px;font-weight:600;display:none;box-shadow:var(--pop)}

@media (max-width:820px){
  .win{inset:0;border-radius:0}
  .bar{grid-template-columns:auto 1fr auto;padding:0 8px}.lights{display:none}.ttl{justify-content:flex-start}
  .info{left:8px;right:8px;width:auto;top:auto;height:62%;bottom:8px}
  .slide{padding:24px 20px 10px;gap:16px}.s-body{grid-template-columns:minmax(0,1fr);gap:22px;overflow:auto}
  .s-foot{padding:8px 20px 12px}.s-right{height:auto;min-height:280px}
  .reader{grid-template-columns:minmax(0,1fr)}.rtoc{display:none}.art{padding:22px}
  .tb .t{display:none}
}
</style>
</head>
<body>
<div class="win">
  <div class="bar">
    <div class="lights"><i style="background:#ff5f57"></i><i style="background:#febc2e"></i><i style="background:#28c840"></i></div>
    <div class="ttl" id="ttl"></div>
    <div class="tools">
      <div class="seg" role="group" aria-label="View"><button id="v-map" aria-pressed="true"></button><button id="v-story" aria-pressed="false"></button></div>
      <button class="tb" id="b-docs" aria-expanded="false" aria-haspopup="menu"></button>
    </div>
    <div class="pop menu" id="menu" hidden role="menu"></div>
  </div>
  <div class="stage" id="stage">
    <div class="banner" id="parity" role="alert"></div>
    <svg id="map" role="img"></svg>
    <div class="maptools"><button id="z-in" aria-label="Zoom in">+</button><button id="z-out" aria-label="Zoom out">−</button><button id="z-fit" aria-label="Fit"></button></div>
    <div class="hint" id="hint">Click a branch to read it · press Story to see it told in order</div>
    <aside class="info" id="info" hidden aria-live="polite"><button class="info-x" id="info-x" aria-label="Close"></button><div class="info-b" id="info-b"></div></aside>
    <section id="story" aria-roledescription="presentation"></section>
    <section class="reader" id="reader" hidden></section>
  </div>
  <div class="foot" id="foot"></div>
</div>

<script id="vb-data" type="application/json">__DATA__</script>
<script id="vb-model">
/* The same model as scripts/model.py. Keep the two identical: every page
   checks itself against model.py's results when it loads, and
   tests/test_model_parity.py compares them value by value. */
var DEFAULT_SCENARIOS = {conservative:{new_x:0.6,growth_x:0.7,churn_x:1.5,cac_x:1.4},base:{},optimistic:{new_x:1.4,growth_x:1.2,churn_x:0.75,cac_x:0.8}};
function val(o,k,d){return (o&&o[k]!==undefined&&o[k]!==null)?o[k]:d;}
function scenariosOf(a){var s=a.scenarios;return (s&&Object.keys(s).length)?s:DEFAULT_SCENARIOS;}
function fixedAt(cost,active,month){
  if(month<val(cost,"start_month",1))return 0;
  var end=val(cost,"end_month",null);
  if(end!==null&&month>end)return 0;
  var monthly=+cost.monthly;
  var steps=(cost.steps||[]).slice().sort(function(x,y){return x.at_customers-y.at_customers;});
  for(var i=0;i<steps.length;i++){if(active>=steps[i].at_customers)monthly=+steps[i].monthly;}
  return monthly;
}
function lineRevenue(line,active,nw,px){
  var attach=+val(line,"attach_rate",1),kind=line.kind,payers;
  if(kind==="one_time"){payers=nw*attach;return [line.price*px*payers,payers,payers];}
  payers=active*attach;
  if(kind==="subscription")return [line.price*px*payers,payers,payers];
  if(kind==="per_unit"){var units=payers*line.units_per_customer_month;return [line.price*px*units,units,payers];}
  var tx=payers*(+val(line,"transactions_per_customer_month",1));
  return [line.rate*px*line.gmv_per_customer_month*payers,tx,payers];
}
function lineFees(line,gross,tx){
  return gross*(+val(line,"store_commission",0))+gross*(+val(line,"processing_pct",0))+tx*(+val(line,"processing_fixed",0));
}
function runModel(a,sc){
  var c=a.customers,months=+val(a,"months",36);
  var newX=val(sc,"new_x",1),growthX=val(sc,"growth_x",1);
  var churn=Math.min(1,c.churn_monthly*val(sc,"churn_x",1)),px=val(sc,"price_x",1);
  var cac=val(c,"cac",0)*val(sc,"cac_x",1),cap=val(c,"new_max_per_month",null);
  var growth=val(c,"new_growth_monthly",0)*growthX;
  var active=+val(c,"starting",0),cash=+val(a,"starting_cash",0),rows=[];
  for(var m=1;m<=months;m++){
    var nw=c.new_first_month*newX*Math.pow(1+growth,m-1);
    if(cap!==null)nw=Math.min(nw,cap);
    var churned=active*churn;
    active=Math.max(0,active+nw-churned);
    var gross=0,fees=0,byLine={};
    a.revenue_lines.forEach(function(l){var r=lineRevenue(l,active,nw,px);byLine[l.name]=r[0];gross+=r[0];fees+=lineFees(l,r[0],r[1]);});
    var variable=0;
    (a.variable_costs||[]).forEach(function(v){variable+=(+val(v,"per_customer_month",0))*active;variable+=(+val(v,"pct_of_revenue",0))*gross;});
    var fixed=0;(a.fixed_costs||[]).forEach(function(f){fixed+=fixedAt(f,active,m);});
    var acquisition=nw*cac,margin=gross-fees-variable,net=margin-fixed-acquisition;
    cash+=net;
    rows.push({month:m,"new":nw,churned:churned,active:active,gross_revenue:gross,fees:fees,variable_costs:variable,
      gross_margin:margin,fixed_costs:fixed,acquisition_spend:acquisition,net:net,cash:cash,by_line:byLine});
  }
  return rows;
}
function unitEconomics(a,sc){
  var c=a.customers,px=val(sc,"price_x",1),churn=Math.min(1,c.churn_monthly*val(sc,"churn_x",1));
  var cac=val(c,"cac",0)*val(sc,"cac_x",1),gross=0,fees=0;
  a.revenue_lines.forEach(function(l){if(l.kind==="one_time")return;var r=lineRevenue(l,1,0,px);gross+=r[0];fees+=lineFees(l,r[0],r[1]);});
  var variable=0;(a.variable_costs||[]).forEach(function(v){variable+=(+val(v,"per_customer_month",0))+(+val(v,"pct_of_revenue",0))*gross;});
  var margin=gross-fees-variable,payback=margin>0?cac/margin:null,ltv=churn>0?margin/churn:null;
  return {revenue:gross,fees:fees,variable:variable,margin:margin,cac:cac,churn:churn,payback:payback,ltv:ltv,ltv_cac:(ltv&&cac)?ltv/cac:null};
}
function atScale(a,n){
  var ue=unitEconomics(a,{}),revenue=ue.revenue*n,fees=ue.fees*n,variable=ue.variable*n,fixed=0;
  (a.fixed_costs||[]).forEach(function(f){fixed+=(val(f,"end_month",null)===null)?fixedAt(f,n,1e6):0;});
  var margin=revenue-fees-variable-fixed;
  return {customers:n,revenue:revenue,fees:fees,variable:variable,fixed:fixed,margin:margin,margin_pct:revenue?margin/revenue:null};
}
function summarize(rows){
  var be=null,low=rows[0];
  for(var i=0;i<rows.length;i++){if(be===null&&rows[i].net>=0)be=rows[i].month;if(rows[i].cash<low.cash)low=rows[i];}
  return {break_even:be,low_cash:low.cash,low_month:low.month,funding:Math.max(0,-low.cash),final:rows[rows.length-1]};
}
</script>
<script>
(function(){
"use strict";
const D=JSON.parse(document.getElementById("vb-data").textContent);
const S=D.story||{beats:[]};
const $=(s,r=document)=>r.querySelector(s);
const css=v=>getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const esc=s=>String(s==null?"":s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

const IC={home:"M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z",search:"M11 4a7 7 0 1 0 0 14a7 7 0 1 0 0-14zM20 20l-4-4",plus:"M12 5v14M5 12h14",
user:"M12 12a4 4 0 1 0 0-8a4 4 0 1 0 0 8zM4 21a8 8 0 0 1 16 0",users:"M9 11a4 4 0 1 0 0-8a4 4 0 1 0 0 8zM2 21a7 7 0 0 1 14 0M16 3.5a4 4 0 0 1 0 7.5M22 21a7 7 0 0 0-4-6.3",
calendar:"M4 6h16v15H4zM4 10h16M8 3v4M16 3v4","map-pin":"M12 21s-7-6.2-7-12a7 7 0 0 1 14 0c0 5.8-7 12-7 12zM12 11.5a2.5 2.5 0 1 0 0-5a2.5 2.5 0 1 0 0 5z",
bell:"M6 9a6 6 0 0 1 12 0c0 6 2 8 2 8H4s2-2 2-8M10 21h4",chat:"M4 5h16v11H9l-5 4z",settings:"M4 6h9M17 6h3M4 12h3M11 12h9M4 18h11M19 18h1M15 4v4M9 10v4M17 16v4",
"chevron-right":"M9 6l6 6-6 6","chevron-left":"M15 6l-6 6 6 6",check:"M5 12.5l4.5 4.5L19 7",star:"M12 3l2.8 5.7 6.2.9-4.5 4.4 1.1 6.2L12 17.3 6.4 20.2l1.1-6.2L3 9.6l6.2-.9z",
camera:"M4 8h3l2-3h6l2 3h3v12H4zM12 17a4 4 0 1 0 0-8a4 4 0 1 0 0 8z",wallet:"M3 7h16a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H3zM3 7l13-3v3M16 13.5h2",
heart:"M12 20s-8-5-8-11a4.5 4.5 0 0 1 8-2.8A4.5 4.5 0 0 1 20 9c0 6-8 11-8 11z",share:"M12 3v12M7 8l5-5 5 5M5 13v7h14v-7",clock:"M12 21a9 9 0 1 0 0-18a9 9 0 1 0 0 18zM12 7v5l3 2",
ticket:"M3 6h18v4a2 2 0 0 0 0 4v4H3v-4a2 2 0 0 0 0-4zM14 6v12",tool:"M14.5 6.5a4 4 0 0 0-5.3 5.3L4 17l3 3 5.2-5.2a4 4 0 0 0 5.3-5.3l-2.5 2.5-2.5-.5-.5-2.5z",
image:"M4 5h16v14H4zM4 16l5-5 4 4 3-3 4 4M15.5 9.5h.01",filter:"M4 5h16l-6 8v6l-4-2v-4z",more:"M5 12h.01M12 12h.01M19 12h.01",x:"M6 6l12 12M18 6L6 18",
upload:"M12 16V4M7 9l5-5 5 5M4 20h16",lock:"M6 11h12v10H6zM8 11V8a4 4 0 0 1 8 0v3",chart:"M5 20V11M12 20V5M19 20v-6M3 20h18",card:"M3 6h18v12H3zM3 10h18M7 15h3",
phone:"M8 2.5h8a2 2 0 0 1 2 2v15a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2v-15a2 2 0 0 1 2-2zM11 18.5h2",doc:"M7 3h7l5 5v13H7zM14 3v5h5M10 13h6M10 17h6",
building:"M5 21V4h10v17M15 9h4v12M8 8h2M8 12h2M8 16h2M3 21h18",alert:"M12 3L2 20h20zM12 10v4M12 17h.01",target:"M12 21a9 9 0 1 0 0-18a9 9 0 1 0 0 18zM12 16a4 4 0 1 0 0-8a4 4 0 1 0 0 8zM12 12h.01",
tag:"M3 12V4h8l10 10-8 8zM7.5 8.5h.01",receipt:"M6 3h12v18l-3-2-3 2-3-2-3 2zM9 8h6M9 12h6M9 16h4",arrow:"M5 12h14M13 6l6 6-6 6",play:"M8 5v14l11-7z",
trend:"M3 17l6-6 4 4 8-8M15 7h6v6",eye:"M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12zM12 15a3 3 0 1 0 0-6a3 3 0 1 0 0 6z",info:"M12 21a9 9 0 1 0 0-18a9 9 0 1 0 0 18zM12 11v6M12 7.5h.01",
copy:"M8 8h12v12H8zM4 16V4h12",map:"M9 4L3 6v14l6-2 6 2 6-2V4l-6 2zM9 4v14M15 6v14",book:"M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2zM4 19V5",fit:"M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5",
folder:"M3 6h6l2 2h10v11H3z"};
const icon=(n,cls)=>`<svg class="i ${cls||""}" viewBox="0 0 24 24" aria-hidden="true"><path d="${IC[n]||IC.info}"/></svg>`;

/* ---------- status, tone, numbers ---------- */
const STATUS={strong:{c:"--moss2",t:"Backed by evidence"},partial:{c:"--tip",t:"Partly backed"},guess:{c:"--seed",t:"Still a guess"},risk:{c:"--danger",t:"Risk or gap"}};
const TONE={go:{c:"--moss2",i:"check"},promising:{c:"--sel",i:"trend"},caution:{c:"--tip",i:"alert"},stop:{c:"--danger",i:"x"}};
const SC_LABEL={conservative:"Bad year",base:"Expected",optimistic:"Great year"};
const SC_COLOR={conservative:"--danger",base:"--sel",optimistic:"--moss2"};
const P_COLOR=["--sel","--moss2","--wither","--tip"];
const cur=a=>(!a.currency||a.currency==="USD")?"$":a.currency+" ";
function money(x,a){if(x==null||isNaN(x))return "—";const s=x<0?"−":"",v=Math.abs(x),c=cur(a);
  if(v>=1e6)return s+c+(v/1e6).toFixed(v>=1e7||v%1e6===0?0:1)+"M";if(v>=1e4)return s+c+Math.round(v/1e3)+"k";
  if(v>=1e3)return s+c+(v/1e3).toFixed(v%1e3===0?0:1)+"k";if(v===0)return c+"0";return s+c+Math.round(v);}
const pathOf=id=>D.paths.find(p=>p.id===id)||D.paths[D.primary]||D.paths[0];
function results(a){const out={},sc=scenariosOf(a);Object.keys(sc).forEach(n=>{out[n]=runModel(a,sc[n]);});return out;}
function srcState(b){const s=String((b||{}).source||"").trim();if(!s||/^TODO/i.test(s))return "missing";if(/UNVERIFIED/i.test(s))return "unverified";return "ok";}
function evidence(a){const bl=[a.customers].concat(a.revenue_lines,a.variable_costs||[],a.fixed_costs||[]);return {guess:bl.filter(b=>srcState(b)!=="ok").length,total:bl.length};}

(function(){const bad=[];D.paths.forEach(p=>{const r=results(p.assumptions);Object.keys(p.expected).forEach(n=>{
  const e=p.expected[n],s=summarize(r[n]),off=(x,y)=>Math.abs(x-y)>Math.max(0.01,Math.abs(y)*1e-6);
  if(e.break_even!==s.break_even||off(s.low_cash,e.low_cash)||off(s.final.cash,e.final_cash)||off(s.final.gross_revenue,e.final_revenue))bad.push(p.name+" / "+n);});});
  if(bad.length){const b=$("#parity");b.style.display="block";b.textContent="Charts disagree with model.py for "+bad.join(", ")+". Rebuild this page.";}})();

/* ---------- beats: the story, plus what's missing ---------- */
const BEATS=(S.beats||[]).map(b=>Object.assign({},b));
(function(){const g=(D.gaps||[]).slice().sort((x,y)=>({high:0,medium:1,low:2}[x.severity]||3)-({high:0,medium:1,low:2}[y.severity]||3));
  if(g.length)BEATS.push({id:"gaps",kind:"gaps",kicker:"What's missing",status:"risk",title:g.length===1?"One thing still needs an answer":`${g.length} things still need an answer`,
    points:g.slice(0,3).map(x=>x.title),facts:g.slice(0,8).map(x=>({label:x.title,status:"risk"})),sources:g.slice(0,6).map(x=>({label:x.title+" — "+x.where}))});})();
const tone=TONE[(S.verdict||{}).tone]||TONE.caution;

/* ---------- visuals ---------- */
function niceTicks(lo,hi,n){if(hi===lo)hi=lo+1;let span=hi-lo,step=Math.pow(10,Math.floor(Math.log10(span/n)));const e=span/n/step;
  if(e>=7.5)step*=10;else if(e>=3.5)step*=5;else if(e>=1.5)step*=2;const t=[];for(let v=Math.floor(lo/step)*step;v<=hi+step*.5;v+=step)t.push(+v.toFixed(10));return t;}
function lineSVG(series,key,a,W,H){const L=54,R=10,T=8,B=26,N=series[0].rows.length;let vals=[];series.forEach(s=>s.rows.forEach(r=>vals.push(r[key])));
  let lo=Math.min(0,...vals),hi=Math.max(0,...vals);const tk=niceTicks(lo,hi,4);lo=tk[0];hi=tk[tk.length-1];
  const X=m=>L+(m-1)/Math.max(1,N-1)*(W-L-R),Y=v=>T+(hi-v)/(hi-lo||1)*(H-T-B),h=[];
  tk.forEach(t=>{h.push(`<line x1="${L}" x2="${W-R}" y1="${Y(t)}" y2="${Y(t)}" stroke="${css(t===0?"--ink3":"--hair")}" stroke-width="${t===0?1:.6}"/>`);
    h.push(`<text x="${L-8}" y="${Y(t)+4}" text-anchor="end" fill="${css("--ink3")}" font-size="11">${key==="active"?Math.round(t).toLocaleString():money(t,a)}</text>`);});
  for(let y=0;y*12<N;y++)h.push(`<text x="${X(Math.min(N,y*12+6.5))}" y="${H-6}" text-anchor="middle" fill="${css("--ink2")}" font-size="11.5" font-weight="600">Year ${y+1}</text>`);
  for(let y=12;y<N;y+=12)h.push(`<line x1="${X(y+.5)}" x2="${X(y+.5)}" y1="${T}" y2="${H-B}" stroke="${css("--hair")}" stroke-dasharray="3 4"/>`);
  series.forEach(s=>{h.push(`<path d="${s.rows.map((r,j)=>(j?"L":"M")+X(r.month).toFixed(1)+" "+Y(r[key]).toFixed(1)).join(" ")}" fill="none" stroke="${s.color}" stroke-width="${s.bold?3:2}" stroke-linejoin="round" stroke-linecap="round"/>`);
    const last=s.rows[N-1];h.push(`<circle cx="${X(N)}" cy="${Y(last[key])}" r="3.5" fill="${s.color}"/>`);});
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(key)} over ${N} months">${h.join("")}</svg>`;}
function spark(vals,color){const w=200,h=44,lo=Math.min(0,...vals),hi=Math.max(0,...vals),r=hi-lo||1,X=i=>i/(vals.length-1)*w,Y=v=>h-3-(v-lo)/r*(h-6);
  return `<svg class="spark" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true"><line x1="0" x2="${w}" y1="${Y(0)}" y2="${Y(0)}" stroke="${css("--ink3")}" stroke-dasharray="2 3" stroke-width="1" vector-effect="non-scaling-stroke"/><path d="${vals.map((v,i)=>(i?"L":"M")+X(i).toFixed(1)+" "+Y(v).toFixed(1)).join(" ")}" fill="none" stroke="${color}" stroke-width="2.2" vector-effect="non-scaling-stroke"/></svg>`;}

function vNumbers(v,host,big){const p=pathOf(v.path),a=p.assumptions,r=results(a),key=v.metric==="revenue"?"gross_revenue":v.metric==="customers"?"active":"cash";
  const series=Object.keys(r).map(n=>({name:SC_LABEL[n]||n,color:css(SC_COLOR[n]||"--ink2"),rows:r[n],bold:n==="base"}));
  const W=Math.max(320,host.clientWidth||520),H=big?Math.min(360,Math.max(220,W*.5)):180;
  host.innerHTML=`<div class="chartbox">${lineSVG(series,key,a,W,H)}<div class="legend">${series.map(s=>`<span><i style="background:${s.color}"></i>${esc(s.name)}</span>`).join("")}<span style="margin-left:auto">${{cash:"Cash in the bank",gross_revenue:"Revenue per month",active:"Customers"}[key]} · ${esc(p.name)}</span></div></div>`;}
function vCompare(v,host){const ids=v.paths||D.paths.filter(p=>p.id!=="plan").map(p=>p.id);const ps=ids.map(pathOf);
  host.innerHTML=`<div class="cmp" style="grid-template-columns:repeat(${Math.min(ps.length,3)},minmax(0,1fr))">${ps.map((p,i)=>{const a=p.assumptions,r=results(a),bk=r.base?"base":Object.keys(r)[0],s=summarize(r[bk]),N=r[bk].length,ev=evidence(a);
    const ok=s.break_even!==null&&s.funding===0,mid=s.break_even!==null&&s.funding>0,c=ok?"--moss2":mid?"--tip":"--danger";
    return `<div class="cmpc ${p.recommended?"rec":""}"><div style="display:flex;justify-content:space-between;gap:8px;align-items:center"><h4>${esc(p.name)}</h4>${p.recommended?`<span class="pill" style="--c:var(--moss1)">${icon("star")} Pick</span>`:""}</div>
      <span class="pill" style="--c:var(${c});align-self:flex-start">${icon(ok?"check":mid?"alert":"x")} ${ok?"Pays for itself":mid?"Needs funding first":"Doesn't pay yet"}</span>
      ${spark(r[bk].map(x=>x.cash),css(c))}
      <div class="row3"><div>Pays back<b>${s.break_even?"M"+s.break_even:"Never"}</b></div><div>Cash needed<b>${s.funding>0?money(s.funding,a):"None"}</b></div><div>Year ${Math.round(N/12)}<b>${money(s.final.gross_revenue,a)}/mo</b></div></div>
      <div style="font-size:11px;color:var(--ink3)">${ev.guess} of ${ev.total} inputs still guesses</div></div>`;}).join("")}</div>`;}
function vBars(v,host){const items=v.items||[],mx=Math.max(1,...items.map(x=>+x.value||0));
  host.innerHTML=`<div class="bars">${items.map((x,i)=>`<div class="br"><span>${esc(x.label)}</span><div class="tr"><div class="fl" style="width:${(+x.value||0)/mx*100}%;background:var(${i===(v.highlight??-1)?"--moss3":"--moss2"})"></div></div><b>${esc(x.display||x.value)}</b></div>`).join("")}</div>`;}
function vMatrix(v,host){const cols=v.cols||[],rows=v.rows||[];
  host.innerHTML=`<table class="mtx"><thead><tr><th></th>${cols.map(c=>`<th>${esc(c)}</th>`).join("")}</tr></thead><tbody>${rows.map(r=>`<tr class="${r.us?"us":""}"><td><b>${esc(r.name)}</b></td>${(r.cells||[]).map(c=>`<td>${c===true?`<span style="color:var(--moss2)">${icon("check")}</span>`:c===false?`<span style="color:var(--ink3)">—</span>`:esc(c)}</td>`).join("")}</tr>`).join("")}</tbody></table>`;}
function vTimeline(v,host){host.innerHTML=`<div class="tl">${(v.items||[]).map(x=>`<div class="st"><div class="w">${esc(x.when)}</div><div class="x">${esc(x.what)}</div></div>`).join("")}</div>`;}
function vQuote(v,host){host.innerHTML=`<div class="quote"><q>${esc(v.text)}</q><div class="who">${esc(v.who||"")}${v.url?` · <a href="${esc(v.url)}" target="_blank" rel="noopener" style="color:var(--ink3)">source</a>`:""}</div></div>`;}
function vSens(v,host){const p=pathOf(v.path),a0=p.assumptions,sc=scenariosOf(a0),bk=sc.base?"base":Object.keys(sc)[0];
  const tweak=(f)=>{const a=JSON.parse(JSON.stringify(a0));f(a);const r=runModel(a,sc[bk]);return r[r.length-1].cash;},ref=tweak(()=>{});
  const D2=[["New customers",(a,m)=>{a.customers.new_first_month*=m;},true],["Growth",(a,m)=>{a.customers.new_growth_monthly=(a.customers.new_growth_monthly||0)*m;},true],
    ["Churn",(a,m)=>{a.customers.churn_monthly*=m;},false],["Cost to win",(a,m)=>{a.customers.cac=(a.customers.cac||0)*m;},false],
    ["Prices",(a,m)=>{a.revenue_lines.forEach(l=>{if(l.price!==undefined)l.price*=m;if(l.rate!==undefined)l.rate=Math.min(1,l.rate*m);});},true],
    ["Fixed costs",(a,m)=>{(a.fixed_costs||[]).forEach(f=>{f.monthly*=m;(f.steps||[]).forEach(s=>{s.monthly*=m;});});},false]];
  const rs=D2.map(([l,f,up])=>{const lo=tweak(a=>f(a,.8))-ref,hi=tweak(a=>f(a,1.2))-ref;return {l,worse:up?lo:hi,better:up?hi:lo};}).sort((x,y)=>Math.abs(y.better-y.worse)-Math.abs(x.better-x.worse));
  const mx=Math.max(1,...rs.map(r=>Math.max(Math.abs(r.worse),Math.abs(r.better))));
  host.innerHTML=`<div class="sens">${rs.map((r,k)=>`<div class="r ${k===0?"top":""}"><span>${r.l}</span><div class="tk"><span class="mid"></span><span class="b" style="right:50%;width:${Math.abs(r.worse)/mx*50}%;background:var(--danger)"></span><span class="b" style="left:50%;width:${Math.abs(r.better)/mx*50}%;background:var(--moss2)"></span></div></div>`).join("")}
    <div class="legend"><span><i style="background:var(--danger)"></i>20% worse</span><span><i style="background:var(--moss2)"></i>20% better</span><span style="margin-left:auto">Effect on cash at the end · ${esc(p.name)}</span></div></div>`;}

function device(set,id,scale){const plat=set.platform,size=plat==="web"?[1180,760]:[393,852],t=set.tokens,scr=set.screens.find(s=>s.id===id)||set.screens[0];
  const vars=`--bg:${t.bg};--surface:${t.surface};--text:${t.text};--muted:${t.muted};--accent:${t.accent};--accent-fg:${t.accent_fg};--border:${t.border};--radius:${parseFloat(t.radius)||12}px;--font:${t.font}`;
  const chrome=plat==="web"?`<div class="webbar"><i style="background:#ff5f57"></i><i style="background:#febc2e"></i><i style="background:#28c840"></i><div class="url">${esc(String(D.venture).toLowerCase().replace(/[^a-z0-9]+/g,""))}.com</div></div>`:"";
  const notch=plat==="ios"?'<div class="island"></div>':plat==="android"?'<div class="punch"></div>':"";
  const status=plat==="web"?"":`<div class="status" style="color:${t.text}"><span>9:41</span><span class="bat"></span></div><div class="homebar" style="background:${t.text}"></div>`;
  return `<div class="dev" style="width:${size[0]*scale}px;height:${size[1]*scale}px"><div class="inner f-${plat}" style="transform:scale(${scale})">${chrome}<div class="scr" style="background:${t.bg}">${notch}${status}<div class="vbd" style="${vars}">${scr.html}</div></div></div></div>`;}
function vScreens(v,host,big){const p=pathOf(v.path||v.set),set=p.screens;if(!set){host.innerHTML=`<div style="color:var(--ink3)">No screens drawn yet.</div>`;return;}
  const ids=(v.ids&&v.ids.length?v.ids:set.hero).slice(0,3),hh=Math.max(220,(host.clientHeight||420)-40),acc=set.tokens.accent;
  let row;
  if(set.platform==="web"){const s=Math.min((host.clientWidth||600)*0.86/1180,hh/760);row=device(set,ids[0],s);}
  else{const s=Math.min(hh/852,((host.clientWidth||600)/ (ids.length*393*0.86)));
    const order=ids.length===3?[ids[1],ids[0],ids[2]]:ids;
    row=order.map((id,k)=>{const mid=ids.length===3&&k===1,sc=mid?s:s*.86;return `<div style="margin:0 ${-393*sc*0.08}px;z-index:${mid?2:1};transform:translateY(${mid?0:hh*0.04}px)">${device(set,id,sc)}</div>`;}).join("");}
  host.innerHTML=`<div class="hero" style="height:${hh+40}px"><div class="bgw" style="background:radial-gradient(120% 90% at 50% 10%,color-mix(in srgb,${acc} 34%,transparent),transparent 70%),linear-gradient(160deg,color-mix(in srgb,${acc} 14%,var(--well)),var(--well))"></div><div class="row">${row}</div></div>`;
  host.querySelectorAll("i[data-i]").forEach(el=>{el.outerHTML=icon(el.getAttribute("data-i"));});}
function visual(v,host,big){if(!v||!v.type){host.innerHTML="";return;}
  ({numbers:vNumbers,compare:vCompare,bars:vBars,matrix:vMatrix,timeline:vTimeline,quote:vQuote,sensitivity:vSens,screens:vScreens}[v.type]||(()=>{host.innerHTML="";}))(v,host,big);}

/* ---------- shared bits ---------- */
function kpiHTML(k){return k&&k.value?`<div class="kpi"><div class="v">${esc(k.value)}</div>${k.label?`<div class="l">${esc(k.label)}</div>`:""}${k.note?`<div class="n">${esc(k.note)}</div>`:""}</div>`:"";}
function chainHTML(c){return c&&c.length?`<div class="chain">${c.map((x,i)=>`${i?`<span class="ar">→</span>`:""}<div class="c"><b>${esc(x.value)}</b><span>${esc(x.label)}</span></div>`).join("")}</div>`:"";}
function ptsHTML(p){return p&&p.length?`<ul class="pts">${p.map(x=>`<li>${esc(x)}</li>`).join("")}</ul>`:"";}
function srcHTML(s){return s&&s.length?`<div><p class="cap">Sources</p><div class="srcs">${s.map(x=>x.url?`<a href="${esc(x.url)}" target="_blank" rel="noopener">${icon("doc")}<span>${esc(x.label)}</span><span class="d">${esc(x.date||"")}</span></a>`:`<span>${icon("doc")}<span>${esc(x.label)}</span><span class="d">${esc(x.date||"")}</span></span>`).join("")}</div></div>`:"";}
const stHTML=st=>{const s=STATUS[st]||STATUS.guess;return `<span class="sdot" style="background:var(${s.c})" title="${s.t}"></span>`;};

/* ---------- map ---------- */
const svg=$("#map"),NS="http://www.w3.org/2000/svg";let view={x:0,y:0,k:1},sel=null,anim=null;
function rnd(seed){let s=seed%2147483647;if(s<=0)s+=2147483646;return ()=>(s=s*16807%2147483647)/2147483647;}
function layout(){const n=BEATS.length,R1=230,R2=410,nodes=[];
  BEATS.forEach((b,i)=>{const ang=-Math.PI/2+i*2*Math.PI/n;const x=Math.cos(ang)*R1,y=Math.sin(ang)*R1*.78;
    const facts=(b.facts&&b.facts.length?b.facts:(b.sources||[]).map(s=>({label:s.label,status:b.status}))).slice(0,6);
    const span=Math.min(2*Math.PI/n*.8,.9),leaves=facts.map((f,j)=>{const a2=ang+(facts.length>1?(j/(facts.length-1)-.5)*span:0);return {f,x:Math.cos(a2)*R2,y:Math.sin(a2)*R2*.78,ang:a2};});
    nodes.push({b,i,x,y,ang,leaves});});
  return nodes;}
function mossAlong(x0,y0,cx,cy,x1,y1,status,density,seed,thick){const r=rnd(seed),out=[],len=Math.hypot(x1-x0,y1-y0),steps=Math.max(8,Math.round(len/(density)));
  const cols={strong:["--moss1","--moss2","--moss3","--moss4"],partial:["--moss1","--moss2","--tip","--moss3"],guess:["--seed"],risk:["--wither","--danger"]}[status]||["--seed"];
  for(let i=0;i<=steps;i++){const t=i/steps,mt=1-t,x=mt*mt*x0+2*mt*t*cx+t*t*x1,y=mt*mt*y0+2*mt*t*cy+t*t*y1;
    const n=status==="guess"?(i%2?0:1):1+Math.round(r()*thick);
    for(let k=0;k<n;k++){const jx=(r()-.5)*thick*3.2,jy=(r()-.5)*thick*3.2,c=cols[Math.floor(r()*cols.length)];out.push({x:x+jx,y:y+jy,t,c,s:status==="guess"?2.4:2.6+r()*1.6});}}
  return out;}
function drawMap(){const nodes=layout();const g=[];const moss=[];
  nodes.forEach(n=>{const st0=n.b.status||"guess",strands=st0==="guess"?1:st0==="partial"?3:4;
    for(let s=0;s<strands;s++){const off=(s-(strands-1)/2)*16,cx=n.x*.45+Math.cos(n.ang+1.57)*off+Math.cos(n.ang+.5)*34,cy=n.y*.45+Math.sin(n.ang+1.57)*off+Math.sin(n.ang+.5)*26;
      moss.push(...mossAlong(0,0,cx,cy,n.x,n.y,st0,3.4,n.i*97+s*7+11,1.3).map(m=>Object.assign(m,{t:m.t*.55})));}
    n.leaves.forEach((l,j)=>{const st1=l.f.status||st0,k=st1==="guess"?1:2;
      for(let s=0;s<k;s++){const lx=(n.x+l.x)/2+Math.cos(l.ang+.6)*(14+s*10),ly=(n.y+l.y)/2+Math.sin(l.ang+.6)*(11+s*8);
        moss.push(...mossAlong(n.x,n.y,lx,ly,l.x,l.y,st1,4.6,n.i*131+j*17+s*5+3,.8).map(m=>Object.assign(m,{t:.55+m.t*.45})));}});});
  g.push(`<g id="moss">${moss.map(m=>`<rect x="${(m.x-m.s/2).toFixed(1)}" y="${(m.y-m.s/2).toFixed(1)}" width="${m.s.toFixed(1)}" height="${m.s.toFixed(1)}" fill="var(${m.c})" data-t="${m.t.toFixed(3)}" opacity="0"/>`).join("")}</g>`);
  nodes.forEach(n=>{n.leaves.forEach(l=>{const right=l.x>=0,lab=String(l.f.label||"");const short=lab.length>34?lab.slice(0,33)+"…":lab;
      g.push(`<g class="leaf node" data-i="${n.i}" transform="translate(${l.x.toFixed(1)},${l.y.toFixed(1)})"><rect x="-3.5" y="-3.5" width="7" height="7" rx="1.5" fill="var(${(STATUS[l.f.status||n.b.status]||STATUS.guess).c})"/><text x="${right?9:-9}" y="3.5" text-anchor="${right?"start":"end"}">${esc(short)}</text></g>`);});
    const right=n.x>=-1,lab=n.b.kicker||n.b.kind||"";
    g.push(`<g class="node beat" data-i="${n.i}" tabindex="0" role="button" aria-label="${esc(lab)}: ${esc(n.b.title||"")}" transform="translate(${n.x.toFixed(1)},${n.y.toFixed(1)})">
      <rect x="-11" y="-11" width="22" height="22" rx="5.5" fill="var(--win)" stroke="var(${(STATUS[n.b.status]||STATUS.guess).c})" stroke-width="2"/>
      <rect x="-8" y="-8" width="16" height="16" rx="4" fill="var(${(STATUS[n.b.status]||STATUS.guess).c})"/>
      <text x="0" y="4" text-anchor="middle" style="font:700 10.5px var(--font);fill:${n.b.status==="partial"?"#1d1d1f":"#fff"}">${n.i+1}</text>
      <text class="lbl" x="${right?18:-18}" y="4.5" text-anchor="${right?"start":"end"}">${esc(lab)}</text>
      <text class="num" x="${right?18:-18}" y="20" text-anchor="${right?"start":"end"}">${esc(n.b.kpi&&n.b.kpi.value?(n.b.kpi.value+(n.b.kpi.label?" · "+(n.b.kpi.label.length>24?n.b.kpi.label.slice(0,23)+"…":n.b.kpi.label):"")):"")}</text></g>`);});
  const ini=String(D.venture).split(/\s+/).map(w=>w[0]).join("").slice(0,2).toUpperCase();
  g.push(`<g class="node" id="center" tabindex="0" role="button" aria-label="Overview"><rect x="-34" y="-34" width="68" height="68" rx="16" fill="var(--moss1)"/><rect x="-34" y="-34" width="68" height="68" rx="16" fill="url(#cg)"/>
    <text x="0" y="9" text-anchor="middle" style="fill:#fff;font:700 26px var(--display)">${esc(ini)}</text>
    <text x="0" y="56" text-anchor="middle" style="font:700 17px var(--display);fill:var(--ink)">${esc(D.venture)}</text>
    <text x="0" y="74" text-anchor="middle" style="font-size:12px;font-weight:600;fill:var(${tone.c})">${esc((S.verdict||{}).label||"")}</text></g>`);
  svg.innerHTML=`<defs><linearGradient id="cg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffffff" stop-opacity=".25"/><stop offset="1" stop-color="#000" stop-opacity=".1"/></linearGradient></defs><g id="world">${g.join("")}</g>`;
  grow();bindMap();if(window.innerWidth>820)inspect(null);fit();}
function grow(){const rects=[...svg.querySelectorAll("#moss rect")];const reduce=window.matchMedia&&matchMedia("(prefers-reduced-motion: reduce)").matches;
  if(reduce){rects.forEach(r=>r.setAttribute("opacity",".9"));return;}
  const t0=performance.now(),dur=1400;cancelAnimationFrame(anim);
  (function step(now){const p=Math.min(1,(now-t0)/dur);rects.forEach(r=>{if(r.getAttribute("opacity")==="0"&&+r.dataset.t<=p)r.setAttribute("opacity",".9");});if(p<1)anim=requestAnimationFrame(step);})(t0);}
function applyView(){$("#world",svg).setAttribute("transform",`translate(${view.x},${view.y}) scale(${view.k})`);}
function fit(){const r=svg.getBoundingClientRect(),w=r.width-(!$("#info").hidden&&r.width>820?380:0);const k=Math.min(w/1060,r.height/840,1.3);view={k,x:w/2,y:r.height/2};applyView();}
function bindMap(){svg.querySelectorAll(".node").forEach(el=>{const open=()=>{if(el.id==="center")inspect(null);else inspect(+el.dataset.i);};
    el.addEventListener("click",e=>{e.stopPropagation();open();});el.addEventListener("keydown",e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();open();}});});}
let drag=null;svg.addEventListener("pointerdown",e=>{if(e.target.closest(".node"))return;drag={x:e.clientX,y:e.clientY,vx:view.x,vy:view.y};svg.classList.add("grab");svg.setPointerCapture(e.pointerId);});
svg.addEventListener("pointermove",e=>{if(!drag)return;view.x=drag.vx+e.clientX-drag.x;view.y=drag.vy+e.clientY-drag.y;applyView();});
svg.addEventListener("pointerup",()=>{drag=null;svg.classList.remove("grab");});
svg.addEventListener("wheel",e=>{e.preventDefault();const r=svg.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top,k2=Math.max(.3,Math.min(3,view.k*Math.exp(-e.deltaY*.0015)));
  view.x=mx-(mx-view.x)*k2/view.k;view.y=my-(my-view.y)*k2/view.k;view.k=k2;applyView();},{passive:false});
$("#z-in").onclick=()=>{view.k=Math.min(3,view.k*1.2);applyView();};$("#z-out").onclick=()=>{view.k=Math.max(.3,view.k/1.2);applyView();};$("#z-fit").onclick=fit;
$("#z-fit").innerHTML=icon("fit");

function inspect(i){sel=i;const box=$("#info-b");$("#info").hidden=false;$("#hint").style.opacity=0;
  svg.querySelectorAll(".beat").forEach(el=>el.classList.toggle("sel",+el.dataset.i===i));
  if(i===null){const p=pathOf(null),ev=evidence(p.assumptions);
    box.innerHTML=`<div class="kick">Overview</div><h2 class="p-title">${esc(S.oneliner||D.venture)}</h2>
      <span class="pill" style="--c:var(${tone.c});align-self:flex-start">${icon(tone.i)} ${esc((S.verdict||{}).label||"")}</span>
      ${(S.verdict||{}).reason?`<p style="margin:0;font-size:14px;color:var(--ink2)">${esc(S.verdict.reason)}</p>`:""}
      <div><p class="cap">The case, in order</p><div class="case">${BEATS.map((b,k)=>`<a href="#" data-go="${k}"><span class="n" style="background:var(${(STATUS[b.status]||STATUS.guess).c})">${k+1}</span><span><b>${esc(b.kicker||b.kind)}</b><span>${esc(b.title||"")}</span></span></a>`).join("")}</div></div>
      <div style="font-size:12px;color:var(--ink3)">${ev.guess} of ${ev.total} model inputs are still guesses.</div>
      ${S.next?`<div><p class="cap">Next step</p><p style="margin:0;font-size:14px">${esc(S.next)}</p></div>`:""}
      <div style="display:flex;gap:8px"><button class="btn pri" id="go-story">${icon("play")} Tell the story</button></div>`;
    box.querySelectorAll("[data-go]").forEach(a=>a.onclick=e=>{e.preventDefault();inspect(+a.dataset.go);});
    $("#go-story").onclick=()=>present(0);return;}
  const b=BEATS[i];
  box.innerHTML=`<div class="kick">${stHTML(b.status)} ${esc(b.kicker||b.kind)} <span style="margin-left:auto;font-weight:500;text-transform:none;letter-spacing:0">${(STATUS[b.status]||STATUS.guess).t}</span></div>
    <h2 class="p-title">${esc(b.title||"")}</h2>${kpiHTML(b.kpi)}${chainHTML(b.chain)}${ptsHTML(b.points)}
    ${b.visual&&b.visual.type?`<div class="miniv" id="mv"></div>`:""}${srcHTML(b.sources)}
    <div style="display:flex;gap:8px"><button class="btn pri" id="go-here">${icon("play")} Present from here</button></div>`;
  if(b.visual&&b.visual.type){const mv=$("#mv");requestAnimationFrame(()=>visual(b.visual,mv,false));}
  $("#go-here").onclick=()=>present(i+1);}
$("#info-x").onclick=()=>{$("#info").hidden=true;sel=null;svg.querySelectorAll(".beat").forEach(el=>el.classList.remove("sel"));fit();};

/* ---------- story ---------- */
let slide=0;
function slideCount(){return BEATS.length+1;}
function present(n){mode("story");slide=Math.max(0,Math.min(slideCount()-1,n));renderSlide();}
function renderSlide(){const st=$("#story");const total=slideCount(),i=slide;
  const prog=`<div class="prog">${Array.from({length:total},(_,k)=>`<i class="${k===i?"on":k<i?"done":""}"></i>`).join("")}</div>`;
  const navs=`<div class="nav2"><button id="sp" aria-label="Previous">${icon("chevron-left")}</button><button id="sn" aria-label="Next">${icon("chevron-right")}</button></div>`;
  if(i===0){st.innerHTML=`<div class="slide cover"><div class="icon">${esc(String(D.venture).split(/\s+/).map(w=>w[0]).join("").slice(0,2).toUpperCase())}</div><h1>${esc(D.venture)}</h1>
      ${S.oneliner?`<p>${esc(S.oneliner)}</p>`:""}<span class="pill" style="--c:var(${tone.c});height:30px;font-size:13.5px">${icon(tone.i)} ${esc((S.verdict||{}).label||"")}</span>
      ${(S.verdict||{}).reason?`<div style="color:var(--ink3);font-size:14px;max-width:46ch">${esc(S.verdict.reason)}</div>`:""}</div>
      <div class="s-foot"><span class="srcline">${BEATS.length} beats · press → to begin</span>${prog}${navs}</div>`;}
  else{const b=BEATS[i-1],hasV=b.visual&&b.visual.type,left=kpiHTML(b.kpi)+chainHTML(b.chain)+ptsHTML(b.points);
    const src=(b.sources||[]).map(x=>x.url?`<a href="${esc(x.url)}" target="_blank" rel="noopener">${esc(x.label)}${x.date?" ("+esc(x.date)+")":""}</a>`:esc(x.label)).join(" · ");
    st.innerHTML=`<div class="slide"><div class="s-kick">${stHTML(b.status)} ${esc(b.kicker||b.kind)}<span style="margin-left:auto">${i} / ${total-1}</span></div>
      <h1 class="s-title">${esc(b.title||"")}</h1>
      <div class="s-body ${!hasV?"solo":left.trim()?"":"wide"}" style="${hasV&&left.trim()&&["compare","matrix","timeline"].includes(b.visual.type)?"grid-template-columns:minmax(0,3fr) minmax(0,8fr)":""}">${left.trim()?`<div class="s-left">${left}</div>`:""}${hasV?`<div class="s-right"><div class="vis" id="sv"></div></div>`:""}</div></div>
      <div class="s-foot"><span class="srcline">${src?"Sources: "+src:(STATUS[b.status]||STATUS.guess).t}</span>${prog}${navs}</div>`;
    if(hasV){const sv=$("#sv");requestAnimationFrame(()=>visual(b.visual,sv,true));}}
  $("#sp").onclick=()=>{if(slide>0){slide--;renderSlide();}};$("#sn").onclick=()=>{if(slide<total-1){slide++;renderSlide();}};}
document.addEventListener("keydown",e=>{if(!$("#story").classList.contains("on"))return;
  if(e.key==="ArrowRight"||e.key===" "||e.key==="PageDown"){e.preventDefault();if(slide<slideCount()-1){slide++;renderSlide();}}
  else if(e.key==="ArrowLeft"||e.key==="PageUp"){e.preventDefault();if(slide>0){slide--;renderSlide();}}
  else if(e.key==="Escape")mode("map");});

/* ---------- chrome ---------- */
function mode(m){const story=m==="story";$("#story").classList.toggle("on",story);$("#v-map").setAttribute("aria-pressed",!story);$("#v-story").setAttribute("aria-pressed",story);
  svg.style.display=story?"none":"block";$(".maptools").style.display=story?"none":"flex";$("#hint").style.display=story?"none":"block";
  if(story){$("#info").hidden=true;}else{renderMapOnce();}$("#reader").hidden=true;}
let mapDrawn=false;function renderMapOnce(){if(!mapDrawn){drawMap();mapDrawn=true;}}
$("#v-map").innerHTML=icon("map")+"Map";$("#v-story").innerHTML=icon("play")+"Story";
$("#v-map").onclick=()=>mode("map");$("#v-story").onclick=()=>present(slide||0);
$("#ttl").innerHTML=`${icon("folder")}<span>${esc(D.venture)}</span>`;
$("#b-docs").innerHTML=icon("book")+'<span class="t">Documents</span>';
const menu=$("#menu");
menu.innerHTML=`<div class="hd">Read the full documents</div>`+(D.docs.length?D.docs.map(d=>`<button data-doc="${d.id}">${icon("doc")}<span>${esc(d.label)}</span><span class="k">${esc(d.file)}</span></button>`).join(""):`<div class="hd" style="font-weight:400">None written yet</div>`);
$("#b-docs").onclick=e=>{e.stopPropagation();const open=menu.hidden;menu.hidden=!open;$("#b-docs").setAttribute("aria-expanded",open);};
document.addEventListener("click",()=>{menu.hidden=true;$("#b-docs").setAttribute("aria-expanded","false");});
menu.querySelectorAll("[data-doc]").forEach(b=>b.onclick=()=>{const d=D.docs.find(x=>x.id===b.dataset.doc),r=$("#reader");
  r.innerHTML=`<nav class="rtoc"><div class="h">${esc(d.label)}</div>${d.toc.map(t=>`<a href="#" data-sec="${t[0]}">${esc(t[1])}</a>`).join("")}<div style="padding:14px 10px"><button class="btn" id="rclose">${icon("x")} Close</button></div></nav><article class="art">${d.html}</article>`;
  r.hidden=false;r.querySelectorAll("[data-sec]").forEach(a=>a.onclick=e=>{e.preventDefault();const t=r.querySelector("#"+CSS.escape(a.dataset.sec));if(t)t.scrollIntoView({behavior:"smooth"});});
  $("#rclose").onclick=()=>{r.hidden=true;};});
(function(){const c={strong:0,partial:0,guess:0,risk:0};(S.beats||[]).forEach(b=>{c[b.status||"guess"]=(c[b.status||"guess"]||0)+1;});
  $("#foot").innerHTML=`<span>${(S.beats||[]).length} beats</span><span class="sp">·</span>`+["strong","partial","guess","risk"].map(k=>`<span class="lg"><i style="background:var(${STATUS[k].c})"></i>${c[k]} ${STATUS[k].t.toLowerCase()}</span>`).join("")+
    `<span class="sp">·</span><span>${esc({explore:"Brainstorm",plan:"Plan",build:"Build"}[D.stage]||"")}, ${esc(D.generated)}</span><span class="sp">·</span><span>Runs on this page only</span>`;})();
window.addEventListener("resize",()=>{clearTimeout(window.__rt);window.__rt=setTimeout(()=>{if($("#story").classList.contains("on"))renderSlide();else fit();},150);});
const startStory=location.hash==="#story";mode(startStory?"story":"map");if(startStory)present(0);
})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    sys.exit(main())
