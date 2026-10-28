#!/usr/bin/env python3
"""Build the venture site: one clickable page that holds the whole plan.

Writes a single self-contained HTML file (no network, nothing to install):

  Overview     the verdict, the key numbers as tiles, three futures, the product
  Product      a clickable prototype of the app's screens, in a device frame
  Numbers      bad / base / great projections with live sliders, year-by-year
               bars, what the result depends on most, and cost versus revenue
               at scale
  Paths        the options compared side by side
  Plan, Company, Validation   the business plan, department plan and
               experiments, rendered with a table of contents
  Gaps         everything unverified, unanswered or worrying, by severity

The page runs the same model as model.py and checks itself against model.py's
results when it opens, so the two cannot silently disagree.

Inputs, whichever exist in the plan folder:
  paths/<id>.json, paths/<id>.screens.json     Stage 1 paths and their screens
  assumptions.json, screens.json               the chosen plan and its screens
  business-plan.md, paths.md, departments.md, validation.md
  traps.csv, compliance.csv

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

DOCS = [  # id, nav label, file, icon, tile colour
    ("plan", "Plan", "business-plan.md", "doc", "--blueF"),
    ("company", "Company", "departments.md", "building", "--indigoF"),
    ("validation", "Validation", "validation.md", "flask", "--purpleF"),
]
DIGEST_FILES = ["assumptions.json", "screens.json", "business-plan.md", "paths.md",
                "departments.md", "validation.md", "traps.csv", "compliance.csv"]
DEFAULT_TOKENS = {"bg": "#f2f2f7", "surface": "#ffffff", "text": "#000000",
                  "muted": "#8e8e93", "accent": "#007aff", "accent_fg": "#ffffff",
                  "border": "rgba(60,60,67,0.18)", "radius": 12,
                  "font": "-apple-system, BlinkMacSystemFont, 'SF Pro Text', system-ui, sans-serif"}


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
    """Drop sections that are still scaffold placeholders. Returns (text, dropped)."""
    parts = re.split(r"(?m)^(?=## )", text)
    kept, dropped = [], 0
    for part in parts:
        body = re.sub(r"<!--.*?-->", "", part, flags=re.S)
        body = re.sub(r"^## .*$", "", body, count=1, flags=re.M).strip()
        if part.startswith("## ") and (not body or body == "TODO: fill this in."):
            dropped += 1
            continue
        kept.append(part.replace("TODO: fill this in.", ""))
    return "".join(kept), dropped


def section_text(text, heading):
    m = re.search(r"(?ms)^##\s+" + re.escape(heading) + r"\s*$\n(.*?)(?=^## |\Z)", text)
    if not m:
        return ""
    body = re.sub(r"<!--.*?-->", "", m.group(1), flags=re.S).strip()
    if not body or body.startswith("TODO"):
        return ""
    return body.split("\n\n")[0].strip()


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
                                 "detail": f"In the {label} prototype. Add the screen or fix the link.",
                                 "where": path.name})
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
    return {"label": label, "platform": platform, "tokens": tokens, "start": start,
            "flows": flows, "screens": screens}


# --- gaps from the plan files -------------------------------------------------

def static_gaps(plan):
    gaps = []
    traps = plan / "traps.csv"
    if traps.exists():
        rows = list(csv.DictReader(traps.open(encoding="utf-8")))
        open_rows = [r for r in rows if (r.get("status") or "").strip().lower()
                     not in ("answered", "n/a")]
        if open_rows:
            ids = ", ".join(r.get("id", "?") for r in open_rows[:8])
            gaps.append({"severity": "high",
                         "title": f"{len(open_rows)} of {len(rows)} trap questions unanswered",
                         "detail": "Each is a third-party rule that can decide your margin or "
                                   f"legality: {ids}" + ("…" if len(open_rows) > 8 else "."),
                         "where": "traps.csv"})
    comp = plan / "compliance.csv"
    if comp.exists():
        rows = list(csv.DictReader(comp.open(encoding="utf-8")))
        counsel = [r.get("regime", "?") for r in rows
                   if (r.get("counsel") or "").strip().lower() == "required"]
        if counsel:
            gaps.append({"severity": "medium",
                         "title": f"{len(counsel)} obligation(s) need a lawyer before launch",
                         "detail": "; ".join(counsel[:5]), "where": "compliance.csv"})
        unstepped = [r.get("regime", "?") for r in rows
                     if not (r.get("step") or "").strip()
                     and (r.get("approach") or "").strip().lower() != "avoid feature"]
        if unstepped:
            gaps.append({"severity": "low",
                         "title": f"{len(unstepped)} obligation(s) have no build step yet",
                         "detail": "Fine while planning; each needs a step before building: "
                                   + "; ".join(unstepped[:5]), "where": "compliance.csv"})
    deps = plan / "departments.md"
    if deps.exists():
        text = deps.read_text(encoding="utf-8")
        todo = [m.group(1).split(" ", 1)[1]
                for m in re.finditer(r"(?ms)^## (D\d\d [^\n]+)\n(.*?)(?=^## |\Z)", text)
                if "TODO" in m.group(2)]
        if todo:
            gaps.append({"severity": "medium",
                         "title": f"{len(todo)} department(s) not planned yet",
                         "detail": ", ".join(todo[:8]) + ("…" if len(todo) > 8 else ""),
                         "where": "departments.md"})
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


NEXT = {
    "explore": "Choose a path, or a mix of two, and say which. The plan stage starts from your choice.",
    "plan": "Run the first experiment in Validation before building anything. Then decide: build, change, or stop.",
    "build": "Start the contracts workstream. The session briefs are in plan/briefs.",
}


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

    paths = []
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
        label = "chosen plan" if is_main else (a.get("path") or src.stem)
        screens = load_screens(screens_file, label, problems) if screens_file.exists() else None
        paths.append({
            "id": pid,
            "name": a.get("path") or ("Chosen plan" if is_main and len(sources) > 1
                                      else str(a.get("venture") or src.stem)),
            "summary": a.get("summary", ""),
            "recommended": bool(a.get("recommended")),
            "file": str(src.relative_to(plan)),
            "assumptions": a,
            "expected": expected,
            "screens": screens,
        })

    if not paths:
        print("Nothing to show yet:", file=sys.stderr)
        for s in skipped:
            print(f"  skipped {s}", file=sys.stderr)
        print("Write plan/paths/<name>.json (Stage 1) or fill plan/assumptions.json "
              "(Stage 2) first.", file=sys.stderr)
        return 1

    docs = []
    for did, label, fname, icon, color in DOCS:
        f = plan / fname
        if not f.exists():
            continue
        raw = f.read_text(encoding="utf-8")
        if raw.count("TODO: fill this in.") * 2 >= max(1, len(re.findall(r"(?m)^## ", raw))):
            continue  # mostly unwritten: a page of blanks is noise, not a draft
        text, dropped = strip_unfilled(raw)
        body, toc = md_to_html(text)
        if not toc:
            continue
        draft = dropped > 0 or "TODO" in f.read_text(encoding="utf-8")
        docs.append({"id": did, "label": label, "icon": icon, "color": color,
                     "html": body, "toc": toc, "draft": draft, "file": fname})

    paths_doc = None
    if (plan / "paths.md").exists():
        text, _ = strip_unfilled((plan / "paths.md").read_text(encoding="utf-8"))
        body, toc = md_to_html(text)
        if toc:
            paths_doc = {"html": body, "toc": toc}

    bp = (plan / "business-plan.md").read_text(encoding="utf-8") if (plan / "business-plan.md").exists() else ""

    pm = (plan / "paths.md").read_text(encoding="utf-8") if (plan / "paths.md").exists() else ""
    concept = section_text(bp, "Concept") or section_text(pm, "Recommendation")
    primary = next((i for i, p in enumerate(paths) if p["id"] == "plan"), None)
    if primary is None:
        primary = next((i for i, p in enumerate(paths) if p["recommended"]), 0)
    if not concept:
        concept = paths[primary]["summary"]

    venture = (next((p["assumptions"].get("venture") for p in paths if p["id"] == "plan"), None)
               or next((p["assumptions"].get("venture") for p in paths
                        if p["assumptions"].get("venture")), None)
               or plan.resolve().name)
    stage = detect_stage(plan)
    digest = inputs_digest(plan)
    data = {
        "venture": venture, "concept": md_inline(concept) if concept else "",
        "stage": stage, "next": NEXT[stage], "generated": dt.date.today().isoformat(),
        "primary": primary, "paths": paths, "docs": docs, "pathsDoc": paths_doc,
        "gaps": static_gaps(plan) + problems,
    }
    blob = json.dumps(data).replace("</", "<\\/")
    page = (TEMPLATE.replace("__TITLE__", html.escape(f"{venture}"))
                    .replace("__DIGEST__", digest)
                    .replace("__DATA__", blob))
    out = Path(args.out) if args.out else plan / "venture.html"
    out.write_text(page, encoding="utf-8")
    n_screens = sum(len(p["screens"]["screens"]) for p in paths if p["screens"])
    print(f"Wrote {out}")
    print(f"  {len(paths)} path(s), {n_screens} screen(s), {len(docs)} document(s), "
          f"stage: {stage}")
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
:root{
  --bg:#f5f5f7;--card:#fff;--fill:#f2f2f7;--fill2:#e5e5ea;--sep:rgba(60,60,67,.14);
  --label:#1d1d1f;--label2:#6e6e73;--label3:#8e8e93;
  --blue:#0066cc;--green:#248a3d;--red:#d70015;--orange:#c93400;--teal:#0e7c86;--purple:#8944ab;--indigo:#3634a3;
  --blueF:#007aff;--greenF:#34c759;--redF:#ff3b30;--orangeF:#ff9500;--purpleF:#af52de;--tealF:#30b0c7;
  --indigoF:#5856d6;--pinkF:#ff2d55;--yellowF:#ffcc00;--grayF:#8e8e93;
  --sh:0 1px 1px rgba(0,0,0,.03),0 4px 14px rgba(0,0,0,.05);
}
@media (prefers-color-scheme:dark){:root{
  --bg:#000;--card:#1c1c1e;--fill:#2c2c2e;--fill2:#3a3a3c;--sep:rgba(84,84,88,.55);
  --label:#f5f5f7;--label2:#98989d;--label3:#6e6e73;
  --blue:#0a84ff;--green:#30d158;--red:#ff453a;--orange:#ff9f0a;--teal:#40c8e0;--purple:#bf5af2;--indigo:#5e5ce6;
  --blueF:#0a84ff;--greenF:#30d158;--redF:#ff453a;--orangeF:#ff9f0a;--purpleF:#bf5af2;--tealF:#40c8e0;
  --indigoF:#5e5ce6;--pinkF:#ff375f;--yellowF:#ffd60a;--grayF:#8e8e93;--sh:none;
}}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--label);
  font:15px/1.45 -apple-system,BlinkMacSystemFont,"SF Pro Text","Helvetica Neue",system-ui,sans-serif;
  -webkit-font-smoothing:antialiased;letter-spacing:-.005em}
b,strong{font-weight:600}
.num{font-variant-numeric:tabular-nums}
button{font:inherit;color:inherit}
:focus-visible{outline:3px solid color-mix(in srgb,var(--blueF) 55%,transparent);outline-offset:2px;border-radius:8px}
svg.i{width:1em;height:1em;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;flex:none}

/* shell */
.app{display:grid;grid-template-columns:232px minmax(0,1fr);min-height:100vh}
.side{position:sticky;top:0;height:100vh;padding:22px 12px;border-right:.5px solid var(--sep);
  background:color-mix(in srgb,var(--bg) 82%,var(--card));display:flex;flex-direction:column;gap:2px}
.brand{padding:4px 10px 18px}
.brand .v{font-size:17px;font-weight:700;letter-spacing:-.02em}
.brand .s{font-size:12px;color:var(--label2)}
.nav{display:flex;align-items:center;gap:10px;padding:7px 10px;border-radius:9px;color:var(--label);
  text-decoration:none;font-size:14.5px}
.nav:hover{background:var(--fill)}
.nav[aria-current=page]{background:var(--fill2);font-weight:600}
.nav .cnt{margin-left:auto;font-size:12px;color:var(--label2);font-weight:500}
.nav .cnt.hot{color:#fff;background:var(--redF);border-radius:10px;padding:0 7px;line-height:18px}
.tile{width:26px;height:26px;border-radius:7px;display:inline-flex;align-items:center;justify-content:center;
  background:var(--c,var(--blueF));color:#fff;font-size:15px;flex:none}
.tile.lg{width:34px;height:34px;border-radius:9px;font-size:19px}
.tile.sm{width:22px;height:22px;border-radius:6px;font-size:13px}
main{padding:34px 40px 80px;min-width:0}
.page{display:none;max-width:1120px;margin:0 auto}
.page.on{display:block}
.ph{margin-bottom:22px}
.eyebrow{font-size:13px;font-weight:600;color:var(--label2);text-transform:uppercase;letter-spacing:.06em}
h1{font-size:34px;line-height:1.12;font-weight:700;letter-spacing:-.025em;margin:4px 0 6px}
.lede{font-size:17px;color:var(--label2);max-width:760px;margin:0}
h2.sh{font-size:22px;font-weight:700;letter-spacing:-.02em;margin:34px 0 12px;display:flex;align-items:center;gap:10px}
.cap{font-size:13px;color:var(--label2)}
.card{background:var(--card);border-radius:18px;box-shadow:var(--sh);padding:20px}
.card.flat{padding:0;overflow:hidden}
.row2{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:16px}
.row3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}
.ov{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:16px;align-items:start}
.nb{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:16px;align-items:start}

/* verdict */
.verdict{display:flex;gap:16px;align-items:flex-start}
.vicon{width:52px;height:52px;border-radius:50%;display:flex;align-items:center;justify-content:center;
  background:var(--c);color:#fff;font-size:28px;flex:none}
.verdict .vt{font-size:24px;font-weight:700;letter-spacing:-.02em;line-height:1.15}
.verdict .vs{font-size:16px;color:var(--label2);margin-top:4px}
.chip{display:inline-flex;align-items:center;gap:6px;font-size:12.5px;font-weight:600;padding:4px 10px;border-radius:20px;
  background:color-mix(in srgb,var(--c) 14%,transparent);color:var(--c)}

/* metric tiles */
.metrics{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:16px}
.metric{background:var(--card);border-radius:16px;box-shadow:var(--sh);padding:14px 16px;display:flex;flex-direction:column;gap:6px;min-width:0}
.metric .mh{display:flex;align-items:center;gap:8px;font-size:13px;font-weight:600;color:var(--label2)}
.metric .mv{font-size:28px;font-weight:700;letter-spacing:-.025em;line-height:1.05}
.metric .mv small{font-size:15px;font-weight:600;color:var(--label2);margin-left:2px}
.metric .mc{font-size:12px;color:var(--label3)}
.spark{display:block;width:100%;height:34px}

/* futures */
.future{background:var(--card);border-radius:16px;box-shadow:var(--sh);padding:14px 16px}
.future .fh{display:flex;align-items:center;gap:8px;font-weight:600}
.future .fh .vi{margin-left:auto;font-size:18px}
.future .fv{display:flex;gap:18px;margin:8px 0 4px}
.future .fv div{font-size:12px;color:var(--label2)}
.future .fv b{display:block;font-size:17px;color:var(--label);letter-spacing:-.01em}
.dot{width:9px;height:9px;border-radius:50%;display:inline-block;flex:none}

/* lists (iOS grouped) */
.group{margin-bottom:22px}
.gh{display:flex;align-items:center;gap:8px;font-size:13px;font-weight:600;color:var(--label2);
  text-transform:uppercase;letter-spacing:.04em;margin:0 4px 8px}
.glist{background:var(--card);border-radius:14px;box-shadow:var(--sh);overflow:hidden}
.grow{padding:12px 16px;position:relative}
.grow+.grow::before{content:"";position:absolute;top:0;left:16px;right:0;border-top:.5px solid var(--sep)}
.gline{display:flex;align-items:baseline;gap:10px}
.gline .gl{flex:1;font-size:15px}
.gline .gv{font-weight:600;font-variant-numeric:tabular-nums}
.gline .gv.changed{color:var(--blue)}
.gwas{font-size:12px;color:var(--label3);text-align:right;min-height:16px}
.gf{font-size:12.5px;color:var(--label2);margin:8px 6px 0;display:flex;gap:6px;align-items:flex-start}
.badge{display:inline-flex;font-size:10.5px;font-weight:700;letter-spacing:.03em;padding:2px 6px;border-radius:5px;
  background:color-mix(in srgb,var(--c) 15%,transparent);color:var(--c);white-space:nowrap}
.rng{position:relative;margin-top:8px;height:22px}
.rng input{position:absolute;inset:0;width:100%;margin:0;accent-color:var(--blueF);background:transparent}
.rng .tick{position:absolute;top:1px;width:2px;height:20px;border-radius:1px;background:var(--label3);opacity:.55;pointer-events:none;transform:translateX(-1px)}

/* segmented control */
.seg{display:inline-flex;background:var(--fill);border-radius:9px;padding:2px;gap:0}
.seg button{border:0;background:transparent;padding:5px 12px;border-radius:7px;font-size:13px;cursor:pointer;color:var(--label)}
.seg button[aria-pressed=true]{background:var(--card);box-shadow:0 1px 3px rgba(0,0,0,.12),0 0 0 .5px rgba(0,0,0,.04);font-weight:600}
@media (prefers-color-scheme:dark){.seg button[aria-pressed=true]{background:var(--fill2)}}
.toolbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:12px}
.toolbar .sp{flex:1}

/* charts */
.chart{position:relative}
.chart svg{display:block;width:100%;height:auto;touch-action:pan-y}
.ct{display:flex;align-items:baseline;gap:10px;margin-bottom:4px}
.ct .t{font-size:13px;font-weight:600;color:var(--label2)}
.ct .v{font-size:28px;font-weight:700;letter-spacing:-.025em}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:12.5px;color:var(--label2);margin-top:6px}
.legend span{display:inline-flex;align-items:center;gap:6px}
.tip{position:absolute;pointer-events:none;background:color-mix(in srgb,var(--card) 92%,transparent);
  backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border-radius:12px;
  box-shadow:0 0 0 .5px var(--sep),0 8px 24px rgba(0,0,0,.14);padding:9px 12px;font-size:12.5px;min-width:170px;opacity:0;transition:opacity .1s;z-index:3}
.tip .h{font-weight:600;margin-bottom:4px}
.tip .r{display:flex;justify-content:space-between;gap:14px;align-items:center}

/* sensitivity */
.sens .sr{display:grid;grid-template-columns:120px minmax(0,1fr);gap:12px;align-items:center;padding:9px 16px}
.sens .sr+.sr{border-top:.5px solid var(--sep)}
.sens .sl{font-size:14px;display:flex;flex-direction:column;gap:2px}
.sens .track{position:relative;height:22px}
.sens .mid{position:absolute;left:50%;top:0;bottom:0;border-left:1px dashed var(--label3)}
.sens .b{position:absolute;top:5px;height:12px;border-radius:6px}
.sens .top{background:color-mix(in srgb,var(--orangeF) 10%,transparent)}
.scl .sr{display:grid;grid-template-columns:86px minmax(0,1fr) 92px;gap:12px;align-items:center;padding:10px 16px}
.scl .sr+.sr{border-top:.5px solid var(--sep)}
.scl .stack{display:flex;height:14px;border-radius:7px;overflow:hidden;background:var(--fill)}
.scl .m{text-align:right;font-weight:600;font-variant-numeric:tabular-nums}

/* paths */
.pcards{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}
.pcard{background:var(--card);border-radius:18px;box-shadow:var(--sh);padding:18px;cursor:pointer;border:0;text-align:left;
  display:flex;flex-direction:column;gap:10px;position:relative}
.pcard[aria-pressed=true]{box-shadow:0 0 0 2.5px var(--blueF),var(--sh)}
.pcard .pn{display:flex;align-items:center;gap:10px;font-size:17px;font-weight:700;letter-spacing:-.015em}
.pcard .ps{font-size:13.5px;color:var(--label2);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:2.8em}
.pcard .pk{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.pcard .pk div{font-size:11.5px;color:var(--label2)}
.pcard .pk b{display:block;font-size:17px;color:var(--label);letter-spacing:-.01em}
.rec{align-self:flex-start;margin-bottom:-2px}

/* product */
.prod{display:grid;grid-template-columns:auto minmax(0,1fr);gap:28px;align-items:start}
.devwrap{display:flex;flex-direction:column;align-items:center;gap:12px}
.flowbar{display:flex;align-items:center;gap:10px;background:var(--card);box-shadow:var(--sh);border-radius:14px;padding:8px 10px;font-size:13.5px;min-height:44px}
.flowbar .ft{font-weight:600}
.flowbar button{border:0;background:var(--fill);border-radius:8px;width:32px;height:28px;cursor:pointer;display:inline-flex;align-items:center;justify-content:center}
.pips{display:flex;gap:5px}.pips span{width:7px;height:7px;border-radius:50%;background:var(--fill2)}.pips span.on{background:var(--blueF)}
.strip{display:flex;gap:14px;overflow-x:auto;padding:6px 4px 14px;margin-top:22px}
.thumb{border:0;background:none;padding:0;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:6px;font-size:12px;color:var(--label2)}
.thumb[aria-current=true]{color:var(--blue);font-weight:600}
.thumb[aria-current=true] .mini{box-shadow:0 0 0 2.5px var(--blueF)}
.mini{border-radius:14px;overflow:hidden;pointer-events:none}
.toggle{display:flex;align-items:center;justify-content:space-between;gap:10px}
.sw{appearance:none;-webkit-appearance:none;width:44px;height:26px;border-radius:13px;background:var(--fill2);position:relative;cursor:pointer;transition:background .15s;flex:none;margin:0}
.sw::after{content:"";position:absolute;top:2px;left:2px;width:22px;height:22px;border-radius:50%;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,.25);transition:left .15s}
.sw:checked{background:var(--greenF)}.sw:checked::after{left:20px}
.linkchips{display:flex;gap:6px;flex-wrap:wrap;margin-top:6px}
.linkchips button{border:0;background:var(--fill);border-radius:14px;padding:4px 10px;font-size:12.5px;cursor:pointer}

/* device frames */
.dev{position:relative;flex:none}
.dev .inner{position:absolute;top:0;left:0;transform-origin:top left}
.f-ios{width:393px;height:852px;border-radius:58px;background:#0b0b0c;padding:11px;
  box-shadow:0 0 0 1.5px #3a3a3c,0 0 0 4px #1c1c1e,0 30px 60px rgba(0,0,0,.25)}
.f-android{width:393px;height:852px;border-radius:40px;background:#0b0b0c;padding:9px;
  box-shadow:0 0 0 1.5px #3a3a3c,0 30px 60px rgba(0,0,0,.25)}
.f-web{width:1180px;height:760px;border-radius:12px;background:var(--card);box-shadow:0 0 0 .5px var(--sep),0 30px 60px rgba(0,0,0,.2);overflow:hidden}
.scr{position:relative;width:100%;height:100%;overflow:hidden;border-radius:47px}
.f-android .scr{border-radius:32px}
.f-web .scr{border-radius:0;height:calc(100% - 44px)}
.island{position:absolute;top:11px;left:50%;transform:translateX(-50%);width:124px;height:36px;border-radius:20px;background:#000;z-index:6}
.punch{position:absolute;top:12px;left:50%;transform:translateX(-50%);width:14px;height:14px;border-radius:50%;background:#000;z-index:6}
.status{position:absolute;top:0;left:0;right:0;height:52px;display:flex;align-items:center;justify-content:space-between;
  padding:4px 36px 0 44px;font:600 16px/1 -apple-system,system-ui,sans-serif;z-index:5;pointer-events:none}
.f-android .status{height:34px;padding:0 22px;font-size:13px}
.status .ic{display:flex;gap:6px;align-items:center}
.status .bat{width:25px;height:12px;border-radius:4px;border:1.5px solid currentColor;opacity:.9;position:relative}
.status .bat::after{content:"";position:absolute;inset:1.5px;right:5px;background:currentColor;border-radius:1.5px}
.homebar{position:absolute;bottom:8px;left:50%;transform:translateX(-50%);width:138px;height:5px;border-radius:3px;z-index:6;opacity:.85}
.webbar{height:44px;display:flex;align-items:center;gap:8px;padding:0 14px;background:var(--fill);border-bottom:.5px solid var(--sep)}
.webbar i{width:12px;height:12px;border-radius:50%;display:inline-block}
.webbar .url{flex:1;max-width:520px;margin:0 auto;background:var(--card);border-radius:8px;height:28px;display:flex;align-items:center;justify-content:center;font-size:13px;color:var(--label2)}

/* app screen kit — screens use these classes; colours come from the screen tokens */
.vbd{--radius:12px;position:absolute;inset:0;overflow-y:auto;overflow-x:hidden;background:var(--bg);color:var(--text);
  font:17px/1.32 var(--font);letter-spacing:-.01em;padding-top:54px;padding-bottom:34px;scrollbar-width:none}
.vbd::-webkit-scrollbar{display:none}
.f-android .vbd{padding-top:36px;padding-bottom:16px;font-size:16px}
.f-web .vbd{padding:0;font-size:15px}
.vbd *{box-sizing:border-box}
.vbd svg.i{width:22px;height:22px;stroke-width:1.9}
.vbd .bar{display:flex;align-items:center;gap:8px;padding:8px 16px;min-height:44px;font-weight:600}
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
.vbd .row .ic+.tx{flex:1}
.vbd .row .tx{flex:1;min-width:0}
.vbd .row .t{font-size:17px}
.vbd .row .s{font-size:14px;color:var(--muted);margin-top:1px}
.vbd .row .r{color:var(--muted);font-size:16px;display:flex;align-items:center;gap:4px}
.vbd .ic{width:30px;height:30px;border-radius:8px;background:var(--accent);color:var(--accent-fg);display:flex;align-items:center;justify-content:center;flex:none}
.vbd .ic svg.i{width:18px;height:18px}
.vbd .card{background:var(--surface);border-radius:calc(var(--radius) + 4px);margin:0 16px 12px;padding:14px;overflow:hidden}
.vbd .img{border-radius:var(--radius);aspect-ratio:16/10;display:flex;align-items:flex-end;padding:10px;font-size:13px;font-weight:600;color:#fff;
  background:linear-gradient(135deg,var(--accent),color-mix(in srgb,var(--accent) 35%,#000));margin-bottom:10px;text-shadow:0 1px 2px rgba(0,0,0,.3)}
.vbd .img.tall{aspect-ratio:4/5}.vbd .img.sq{aspect-ratio:1}
.vbd .hero{margin:0 0 12px;border-radius:0;aspect-ratio:4/3}
.vbd .btn{display:block;margin:12px 16px;padding:15px;border-radius:calc(var(--radius) + 2px);background:var(--accent);color:var(--accent-fg);
  text-align:center;font-weight:600;font-size:17px}
.vbd .btn.ghost{background:color-mix(in srgb,var(--accent) 12%,transparent);color:var(--accent)}
.vbd .btn.sm{display:inline-block;margin:0;padding:7px 14px;font-size:15px;border-radius:20px}
.vbd .input{margin:8px 16px;padding:12px 14px;border-radius:var(--radius);background:var(--surface);color:var(--muted);display:flex;align-items:center;gap:8px}
.vbd .search{margin:4px 16px 12px;padding:9px 12px;border-radius:11px;background:color-mix(in srgb,var(--text) 7%,transparent);color:var(--muted);display:flex;align-items:center;gap:8px;font-size:17px}
.vbd .search svg.i{width:18px;height:18px}
.vbd .chips{display:flex;gap:8px;overflow-x:auto;padding:4px 16px 12px;scrollbar-width:none}
.vbd .chips::-webkit-scrollbar{display:none}
.vbd .chip{padding:7px 14px;border-radius:18px;background:var(--surface);font-size:15px;white-space:nowrap}
.vbd .chip.on{background:var(--accent);color:var(--accent-fg)}
.vbd .badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:13px;font-weight:600;
  background:color-mix(in srgb,var(--accent) 15%,transparent);color:var(--accent)}
.vbd .avatar{width:40px;height:40px;border-radius:50%;background:color-mix(in srgb,var(--accent) 22%,var(--surface));color:var(--accent);
  display:flex;align-items:center;justify-content:center;font-weight:700;font-size:15px;flex:none}
.vbd .grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:0 16px 12px}
.vbd .grid2 .card{margin:0}
.vbd .stat .k{font-size:13px;color:var(--muted)}
.vbd .stat .v{font-size:28px;font-weight:700;letter-spacing:-.02em}
.vbd .map{position:relative;height:220px;margin:0 16px 12px;border-radius:var(--radius);overflow:hidden;
  background-color:color-mix(in srgb,var(--accent) 6%,var(--surface));
  background-image:linear-gradient(color-mix(in srgb,var(--text) 6%,transparent) 1px,transparent 1px),linear-gradient(90deg,color-mix(in srgb,var(--text) 6%,transparent) 1px,transparent 1px);
  background-size:28px 28px}
.vbd .pin{position:absolute;width:14px;height:14px;border-radius:50%;background:var(--accent);box-shadow:0 0 0 4px color-mix(in srgb,var(--accent) 25%,transparent)}
.vbd .tabbar{position:sticky;bottom:-34px;margin-top:24px;display:flex;justify-content:space-around;padding:8px 0 30px;
  background:color-mix(in srgb,var(--surface) 88%,transparent);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border-top:.5px solid var(--border)}
.f-android .vbd .tabbar{bottom:-16px;padding-bottom:14px}
.vbd .tab{display:flex;flex-direction:column;align-items:center;gap:2px;font-size:10.5px;color:var(--muted);min-width:60px}
.vbd .tab.on{color:var(--accent)}
.vbd .empty{text-align:center;color:var(--muted);padding:40px 24px}
.vbd .done{display:flex;flex-direction:column;align-items:center;text-align:center;gap:10px;padding:40px 24px 10px}
.vbd .done .ok{width:72px;height:72px;border-radius:50%;background:var(--accent);color:var(--accent-fg);display:flex;align-items:center;justify-content:center}
.vbd .done .ok svg.i{width:40px;height:40px;stroke-width:2.6}
.vbd .code{font:600 30px/1 ui-monospace,Menlo,monospace;letter-spacing:.12em;text-align:center;padding:14px;margin:8px 16px;border-radius:var(--radius);background:var(--surface)}
.vbd .note{font-size:13px;color:var(--muted);padding:6px 16px}
.vbd .sheet{position:sticky;bottom:0;margin-top:16px;background:var(--surface);border-radius:20px 20px 0 0;padding:6px 0 16px;box-shadow:0 -6px 24px rgba(0,0,0,.08)}
.vbd .divider{height:.5px;background:var(--border);margin:8px 16px}
.vbd .spacer{height:16px}
.vbd .web{max-width:1080px;margin:0 auto;padding:24px 32px}
.vbd .webnav{display:flex;align-items:center;gap:24px;padding:14px 32px;border-bottom:.5px solid var(--border);font-size:14px}
.vbd .webnav .logo{font-weight:700;font-size:17px;margin-right:auto}
.vbd [data-go],.vbd [data-back]{cursor:pointer}
.vbd.hot [data-go],.vbd.hot [data-back]{outline:2.5px solid color-mix(in srgb,#ff9500 85%,transparent);outline-offset:-2px;border-radius:10px}

/* documents */
.doc{display:grid;grid-template-columns:200px minmax(0,1fr);gap:28px;align-items:start}
.toc{position:sticky;top:24px;font-size:13px;display:flex;flex-direction:column;gap:2px}
.toc a{color:var(--label2);text-decoration:none;padding:5px 10px;border-radius:7px}
.toc a:hover{background:var(--fill);color:var(--label)}
.art{background:var(--card);border-radius:18px;box-shadow:var(--sh);padding:28px 36px;max-width:820px;font-size:16px;line-height:1.6}
.art h1{font-size:28px}.art h2{font-size:22px;font-weight:700;letter-spacing:-.02em;margin:34px 0 8px;scroll-margin-top:20px}
.art h2:first-child{margin-top:0}
.art h3{font-size:17px;margin:22px 0 6px}
.art p{margin:0 0 12px}.art ul,.art ol{padding-left:22px;margin:0 0 12px}.art li{margin:4px 0}
.art a{color:var(--blue)}
.art code{font:13.5px ui-monospace,Menlo,monospace;background:var(--fill);padding:1px 5px;border-radius:5px}
.art pre{background:var(--fill);border-radius:12px;padding:12px 14px;overflow-x:auto}
.art pre code{background:none;padding:0}
.art blockquote{margin:0 0 12px;padding:4px 16px;border-left:3px solid var(--blueF);color:var(--label2)}
.tbl{overflow-x:auto;margin:6px 0 16px;border-radius:12px;box-shadow:0 0 0 .5px var(--sep)}
.art table{border-collapse:collapse;width:100%;font-size:13.5px;line-height:1.4}
.art th{background:var(--fill);text-align:left;font-weight:600;padding:9px 12px;white-space:nowrap}
.art td{padding:9px 12px;border-top:.5px solid var(--sep);vertical-align:top}
.draft{margin-bottom:14px}

/* gaps */
.gitem{width:100%;border:0;background:none;text-align:left;cursor:pointer;display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:12px;align-items:center;padding:12px 16px}
.gitem .gt{font-size:15px;font-weight:500}
.gitem .gw{font-size:12px;color:var(--label3);white-space:nowrap}
.gdet{display:none;padding:0 16px 14px 54px;font-size:14px;color:var(--label2)}
.gdet .fix{display:inline-flex;margin-top:6px;font-size:12px}
.gwrap.open .gdet{display:block}
.gwrap+.gwrap{border-top:.5px solid var(--sep)}
.gwrap{position:relative}

.banner{display:none;background:color-mix(in srgb,var(--redF) 12%,transparent);color:var(--red);padding:12px 16px;border-radius:14px;font-weight:600;margin-bottom:16px}
.foot{margin-top:40px;color:var(--label3);font-size:12px}
textarea.copy{width:100%;height:150px;font:12px ui-monospace,Menlo,monospace;margin-top:8px;display:none;background:var(--fill);color:var(--label);border:0;border-radius:10px;padding:10px}
.btn{border:0;background:var(--fill);border-radius:10px;padding:8px 14px;font-size:14px;cursor:pointer;font-weight:500}
.btn.pri{background:var(--blueF);color:#fff}
.btns{display:flex;gap:8px;margin-top:12px;flex-wrap:wrap}
.empty{color:var(--label2);padding:30px;text-align:center}

@media (max-width:1060px){.ov,.nb{grid-template-columns:minmax(0,1fr)}.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:860px){.prod{grid-template-columns:minmax(0,1fr)}.doc{grid-template-columns:minmax(0,1fr)}.toc{display:none}.row2,.row3{grid-template-columns:minmax(0,1fr)}}
@media (max-width:760px){
  .app{grid-template-columns:minmax(0,1fr)}
  .side{position:fixed;top:auto;bottom:0;left:0;right:0;height:auto;flex-direction:row;justify-content:space-around;padding:6px 4px calc(6px + env(safe-area-inset-bottom));
    border-right:0;border-top:.5px solid var(--sep);z-index:20;backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);background:color-mix(in srgb,var(--bg) 85%,transparent)}
  .brand{display:none}
  .nav{flex-direction:column;gap:3px;padding:4px 2px;font-size:10px;background:none!important}
  .nav .cnt{display:none}
  main{padding:22px 16px 110px}
  h1{font-size:30px}
  .art{padding:20px}
  .metrics{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}
}
</style>
</head>
<body>
<div class="app">
  <nav class="side" id="nav" aria-label="Sections"></nav>
  <main>
    <div class="banner" id="parity" role="alert"></div>
    <section class="page" id="p-overview"></section>
    <section class="page" id="p-product"></section>
    <section class="page" id="p-numbers"></section>
    <section class="page" id="p-paths"></section>
    <section class="page" id="p-plan"></section>
    <section class="page" id="p-company"></section>
    <section class="page" id="p-validation"></section>
    <section class="page" id="p-gaps"></section>
    <div class="foot" id="foot"></div>
  </main>
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
const $=(s,r=document)=>r.querySelector(s);

/* ---------- icons (one set for the site and the app screens) ---------- */
const IC={home:"M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z",search:"M11 4a7 7 0 1 0 0 14a7 7 0 1 0 0-14zM20 20l-4-4",
plus:"M12 5v14M5 12h14",user:"M12 12a4 4 0 1 0 0-8a4 4 0 1 0 0 8zM4 21a8 8 0 0 1 16 0",
users:"M9 11a4 4 0 1 0 0-8a4 4 0 1 0 0 8zM2 21a7 7 0 0 1 14 0M16 3.5a4 4 0 0 1 0 7.5M22 21a7 7 0 0 0-4-6.3",
calendar:"M4 6h16v15H4zM4 10h16M8 3v4M16 3v4","map-pin":"M12 21s-7-6.2-7-12a7 7 0 0 1 14 0c0 5.8-7 12-7 12zM12 11.5a2.5 2.5 0 1 0 0-5a2.5 2.5 0 1 0 0 5z",
bell:"M6 9a6 6 0 0 1 12 0c0 6 2 8 2 8H4s2-2 2-8M10 21h4",chat:"M4 5h16v11H9l-5 4z",
settings:"M4 6h9M17 6h3M4 12h3M11 12h9M4 18h11M19 18h1M15 4v4M9 10v4M17 16v4","chevron-right":"M9 6l6 6-6 6","chevron-left":"M15 6l-6 6 6 6",
check:"M5 12.5l4.5 4.5L19 7",star:"M12 3l2.8 5.7 6.2.9-4.5 4.4 1.1 6.2L12 17.3 6.4 20.2l1.1-6.2L3 9.6l6.2-.9z",
camera:"M4 8h3l2-3h6l2 3h3v12H4zM12 17a4 4 0 1 0 0-8a4 4 0 1 0 0 8z",wallet:"M3 7h16a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H3zM3 7l13-3v3M16 13.5h2",
heart:"M12 20s-8-5-8-11a4.5 4.5 0 0 1 8-2.8A4.5 4.5 0 0 1 20 9c0 6-8 11-8 11z",share:"M12 3v12M7 8l5-5 5 5M5 13v7h14v-7",
clock:"M12 21a9 9 0 1 0 0-18a9 9 0 1 0 0 18zM12 7v5l3 2",ticket:"M3 6h18v4a2 2 0 0 0 0 4v4H3v-4a2 2 0 0 0 0-4zM14 6v12",
tool:"M14.5 6.5a4 4 0 0 0-5.3 5.3L4 17l3 3 5.2-5.2a4 4 0 0 0 5.3-5.3l-2.5 2.5-2.5-.5-.5-2.5z",
image:"M4 5h16v14H4zM4 16l5-5 4 4 3-3 4 4M15.5 9.5h.01",filter:"M4 5h16l-6 8v6l-4-2v-4z",more:"M5 12h.01M12 12h.01M19 12h.01",
x:"M6 6l12 12M18 6L6 18",upload:"M12 16V4M7 9l5-5 5 5M4 20h16",lock:"M6 11h12v10H6zM8 11V8a4 4 0 0 1 8 0v3",
chart:"M5 20V11M12 20V5M19 20v-6M3 20h18",card:"M3 6h18v12H3zM3 10h18M7 15h3",
phone:"M8 2.5h8a2 2 0 0 1 2 2v15a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2v-15a2 2 0 0 1 2-2zM11 18.5h2",
signpost:"M12 2v20M6 5h11l2.5 2.5L17 10H6zM18 13H7l-2.5 2.5L7 18h11",doc:"M7 3h7l5 5v13H7zM14 3v5h5M10 13h6M10 17h6",
building:"M5 21V4h10v17M15 9h4v12M8 8h2M8 12h2M8 16h2M3 21h18",flask:"M9 3h6M10 3v6L5 19a1.5 1.5 0 0 0 1.3 2h11.4A1.5 1.5 0 0 0 19 19l-5-10V3M7.5 14h9",
alert:"M12 3L2 20h20zM12 10v4M12 17h.01",target:"M12 21a9 9 0 1 0 0-18a9 9 0 1 0 0 18zM12 16a4 4 0 1 0 0-8a4 4 0 1 0 0 8zM12 12h.01",
tag:"M3 12V4h8l10 10-8 8zM7.5 8.5h.01",receipt:"M6 3h12v18l-3-2-3 2-3-2-3 2zM9 8h6M9 12h6M9 16h4",
arrow:"M5 12h14M13 6l6 6-6 6",play:"M8 5v14l11-7z",trend:"M3 17l6-6 4 4 8-8M15 7h6v6",eye:"M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12zM12 15a3 3 0 1 0 0-6a3 3 0 1 0 0 6z",
info:"M12 21a9 9 0 1 0 0-18a9 9 0 1 0 0 18zM12 11v6M12 7.5h.01",copy:"M8 8h12v12H8zM4 16V4h12",rotate:"M4 12a8 8 0 1 0 2.3-5.7M4 4v5h5"};
const icon=(n,cls)=>`<svg class="i ${cls||""}" viewBox="0 0 24 24" aria-hidden="true"><path d="${IC[n]||IC.info}"/></svg>`;
const tile=(n,c,size)=>`<span class="tile ${size||""}" style="--c:var(${c})">${icon(n)}</span>`;

/* ---------- formatting ---------- */
const esc=s=>String(s==null?"":s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const cur=a=>(!a.currency||a.currency==="USD")?"$":a.currency+" ";
function money(x,a,compact){if(x==null||isNaN(x))return "—";const s=x<0?"−":"",v=Math.abs(x),c=cur(a);
  if(compact){if(v>=1e6)return s+c+(v/1e6).toFixed(v>=1e7||v%1e6===0?0:1)+"M";if(v>=1e4)return s+c+Math.round(v/1e3)+"k";
    if(v>=1e3)return s+c+(v/1e3).toFixed(v%1e3===0?0:1)+"k";if(v===0)return c+"0";if(v>=10)return s+c+Math.round(v);}
  return s+c+(v>=100?Math.round(v).toLocaleString():v.toFixed(2));}
const pct=(x,d)=>x==null?"—":(x*100).toFixed(d==null?0:d)+"%";
const cnt=x=>Math.round(x).toLocaleString();
const css=v=>getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const clone=o=>JSON.parse(JSON.stringify(o));

/* ---------- scenarios, paths, sliders ---------- */
const SC_LABEL={conservative:"Bad year",base:"Expected",optimistic:"Great year"};
const SC_SHORT={conservative:"Bad",base:"Expected",optimistic:"Great"};
const SC_COLOR={conservative:"--redF",base:"--blueF",optimistic:"--greenF"};
const P_COLOR=["--blueF","--purpleF","--orangeF","--tealF","--pinkF","--indigoF"];
const scLabel=n=>SC_LABEL[n]||n, scShort=n=>SC_SHORT[n]||n, scColor=(n,i)=>css(SC_COLOR[n]||P_COLOR[(i||0)%6]);
const st={page:"overview",sel:D.primary||0,mode:"scen",metric:"gross_revenue",scen:"base",sliders:{},set:null,screen:null,hist:[],flow:null,hot:false,gfilter:"all",open:{}};

function defaults(a){const c=a.customers;return {new_first_month:c.new_first_month,new_growth_monthly:val(c,"new_growth_monthly",0),
  churn_monthly:c.churn_monthly,cac:val(c,"cac",0),price_mult:1,fixed_mult:1,starting_cash:+val(a,"starting_cash",0)};}
function sliders(i){return st.sliders[i]||(st.sliders[i]=defaults(D.paths[i].assumptions));}
function effective(i,override){const p=D.paths[i],a=clone(p.assumptions),s=override||sliders(i),c=a.customers;
  c.new_first_month=s.new_first_month;c.new_growth_monthly=s.new_growth_monthly;c.churn_monthly=s.churn_monthly;c.cac=s.cac;a.starting_cash=s.starting_cash;
  a.revenue_lines.forEach(l=>{if(l.price!==undefined)l.price*=s.price_mult;if(l.rate!==undefined)l.rate=Math.min(1,l.rate*s.price_mult);});
  (a.fixed_costs||[]).forEach(f=>{f.monthly*=s.fixed_mult;(f.steps||[]).forEach(x=>{x.monthly*=s.fixed_mult;});});
  return a;}
function results(a){const out={},sc=scenariosOf(a);Object.keys(sc).forEach(n=>{out[n]=runModel(a,sc[n]);});return out;}
function baseKey(a){const sc=scenariosOf(a);return sc.base?"base":Object.keys(sc)[0];}
function srcState(b){const s=String((b||{}).source||"").trim();if(!s||/^TODO/i.test(s))return "missing";if(/UNVERIFIED/i.test(s))return "unverified";return "ok";}
function blocks(a){return [a.customers].concat(a.revenue_lines,a.variable_costs||[],a.fixed_costs||[]);}
function badgeFor(state){return state==="ok"?`<span class="badge" style="--c:var(--green)">SOURCED</span>`:
  state==="unverified"?`<span class="badge" style="--c:var(--orange)">UNVERIFIED</span>`:`<span class="badge" style="--c:var(--red)">NO SOURCE</span>`;}

function verdict(a,rows){const s=summarize(rows),ue=unitEconomics(a,scenariosOf(a)[baseKey(a)]||{}),N=rows.length;
  if(ue.margin<=0)return {k:"red",icon:"x",c:"--redF",t:"Doesn't work yet",s:"Each customer costs more to serve than they pay. Growth makes it worse."};
  if(s.break_even===null)return {k:"red",icon:"x",c:"--redF",t:"Doesn't work yet",s:`Never pays for itself within ${Math.round(N/12)} years in the expected case.`};
  if(s.funding>0)return {k:"orange",icon:"alert",c:"--orangeF",t:"Works, if you can fund the gap",s:`Pays for itself from month ${s.break_even}, but needs ${money(s.funding,a,true)} more than your starting cash first.`};
  return {k:"green",icon:"check",c:"--greenF",t:"Works on these numbers",s:`Pays for itself from month ${s.break_even} without needing more than your starting cash.`};}

/* parity with model.py, checked before anything moves */
(function(){const bad=[];D.paths.forEach(p=>{const r=results(p.assumptions);Object.keys(p.expected).forEach(n=>{
  const e=p.expected[n],s=summarize(r[n]),off=(x,y)=>Math.abs(x-y)>Math.max(0.01,Math.abs(y)*1e-6);
  if(e.break_even!==s.break_even||off(s.low_cash,e.low_cash)||off(s.final.cash,e.final_cash)||off(s.final.gross_revenue,e.final_revenue))bad.push(p.name+" / "+n);});});
  if(bad.length){const b=$("#parity");b.style.display="block";b.textContent="This page's model disagrees with model.py for "+bad.join(", ")+". Trust financials.md and regenerate the page.";}})();

/* ---------- charts ---------- */
function niceTicks(lo,hi,n){if(hi===lo)hi=lo+1;let span=hi-lo,step=Math.pow(10,Math.floor(Math.log10(span/n)));const e=span/n/step;
  if(e>=7.5)step*=10;else if(e>=3.5)step*=5;else if(e>=1.5)step*=2;const t=[];for(let v=Math.floor(lo/step)*step;v<=hi+step*.5;v+=step)t.push(+v.toFixed(10));return t;}
function spark(vals,color,zero){const w=200,h=34,lo=Math.min(...vals,zero?0:Infinity),hi=Math.max(...vals,zero?0:-Infinity),r=hi-lo||1;
  const X=i=>i/(vals.length-1)*w,Y=v=>h-2-(v-lo)/r*(h-4);let z="";
  if(zero&&lo<0)z=`<line x1="0" x2="${w}" y1="${Y(0)}" y2="${Y(0)}" stroke="${css("--label3")}" stroke-dasharray="2 3" stroke-width="1"/>`;
  return `<svg class="spark" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true">${z}<path d="${vals.map((v,i)=>(i?"L":"M")+X(i).toFixed(1)+" "+Y(v).toFixed(1)).join(" ")}" fill="none" stroke="${color}" stroke-width="2" vector-effect="non-scaling-stroke" stroke-linejoin="round"/></svg>`;}

function lineChart(host,S,key,fmt){host.innerHTML=`<div class="tip"></div>`;const tip=$(".tip",host);
  const W=Math.max(300,host.clientWidth),H=Math.round(Math.min(320,Math.max(200,W*.4))),L=56,R=12,T=10,B=30,N=S[0].rows.length;
  let vals=[];S.forEach(s=>s.rows.forEach(r=>vals.push(r[key])));let lo=Math.min(0,...vals),hi=Math.max(0,...vals);const tk=niceTicks(lo,hi,4);lo=tk[0];hi=tk[tk.length-1];
  const X=m=>L+(m-1)/Math.max(1,N-1)*(W-L-R),Y=v=>T+(hi-v)/(hi-lo||1)*(H-T-B);const h=[];
  tk.forEach(t=>{h.push(`<line x1="${L}" x2="${W-R}" y1="${Y(t)}" y2="${Y(t)}" stroke="${css(t===0?"--label3":"--sep")}" stroke-width="${t===0?1:.5}"/>`);
    h.push(`<text x="${L-8}" y="${Y(t)+4}" text-anchor="end" fill="${css("--label3")}" font-size="11">${fmt(t)}</text>`);});
  for(let y=12;y<N;y+=12)h.push(`<line x1="${X(y+.5)}" x2="${X(y+.5)}" y1="${T}" y2="${H-B}" stroke="${css("--sep")}" stroke-dasharray="3 4"/>`);
  for(let y=0;y*12<N;y++)h.push(`<text x="${X(Math.min(N,y*12+6.5))}" y="${H-9}" text-anchor="middle" fill="${css("--label2")}" font-size="11.5" font-weight="600">Year ${y+1}</text>`);
  S.forEach(s=>{h.push(`<path d="${s.rows.map((r,j)=>(j?"L":"M")+X(r.month).toFixed(1)+" "+Y(r[key]).toFixed(1)).join(" ")}" fill="none" stroke="${s.color}" stroke-width="${s.bold?3:2.2}" stroke-linejoin="round" stroke-linecap="round"/>`);
    if(key==="cash"){const sm=summarize(s.rows);if(sm.low_cash<0)h.push(`<circle cx="${X(sm.low_month)}" cy="${Y(sm.low_cash)}" r="4.5" fill="${s.color}" stroke="${css("--card")}" stroke-width="2"/>`);}});
  h.push(`<line class="xh" x1="0" x2="0" y1="${T}" y2="${H-B}" stroke="${css("--label3")}" visibility="hidden"/>`);
  S.forEach(s=>h.push(`<circle class="hv" r="4.5" fill="${s.color}" stroke="${css("--card")}" stroke-width="2" visibility="hidden"/>`));
  h.push(`<rect class="hit" x="${L}" y="${T}" width="${W-L-R}" height="${H-T-B}" fill="transparent"/>`);
  host.insertAdjacentHTML("beforeend",`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Chart over ${N} months">${h.join("")}</svg>`);
  const svg=$("svg",host),xh=$(".xh",svg),dots=svg.querySelectorAll(".hv"),hit=$(".hit",svg);
  function mv(ev){const rc=svg.getBoundingClientRect();let m=Math.round(((ev.clientX-rc.left)*W/rc.width-L)/(W-L-R)*(N-1))+1;m=Math.max(1,Math.min(N,m));
    xh.setAttribute("x1",X(m));xh.setAttribute("x2",X(m));xh.setAttribute("visibility","visible");
    S.forEach((s,i)=>{dots[i].setAttribute("cx",X(m));dots[i].setAttribute("cy",Y(s.rows[m-1][key]));dots[i].setAttribute("visibility","visible");});
    tip.innerHTML=`<div class="h">Month ${m} · Year ${Math.ceil(m/12)}</div>`+S.map(s=>`<div class="r"><span><span class="dot" style="background:${s.color}"></span> ${esc(s.name)}</span><b class="num">${fmt(s.rows[m-1][key])}</b></div>`).join("");
    tip.style.opacity=1;const px=X(m)*rc.width/W;let left=px+14;if(left+200>rc.width)left=px-214;tip.style.left=Math.max(0,left)+"px";tip.style.top="8px";}
  hit.addEventListener("pointermove",mv);hit.addEventListener("pointerdown",mv);
  hit.addEventListener("pointerleave",()=>{tip.style.opacity=0;xh.setAttribute("visibility","hidden");dots.forEach(d=>d.setAttribute("visibility","hidden"));});}

function yearBars(host,S,key,fmt){const N=S[0].rows.length,Yn=Math.ceil(N/12),W=Math.max(300,host.clientWidth),H=200,L=8,R=8,T=22,B=26;
  const sumKey=key==="cash"||key==="active";const vals=S.map(s=>{const out=[];for(let y=0;y<Yn;y++){const sl=s.rows.slice(y*12,(y+1)*12);
      out.push(sumKey?sl[sl.length-1][key]:sl.reduce((a,r)=>a+r[key],0));}return out;});
  const all=vals.flat(),lo=Math.min(0,...all),hi=Math.max(0,...all),Y=v=>T+(hi-v)/((hi-lo)||1)*(H-T-B);
  const gw=(W-L-R)/Yn,bw=Math.min(46,(gw-28)/S.length),h=[];
  h.push(`<line x1="${L}" x2="${W-R}" y1="${Y(0)}" y2="${Y(0)}" stroke="${css("--label3")}" stroke-width="1"/>`);
  for(let y=0;y<Yn;y++){const x0=L+y*gw+(gw-bw*S.length-(S.length-1)*4)/2;
    S.forEach((s,i)=>{const v=vals[i][y],x=x0+i*(bw+4),y1=Y(Math.max(0,v)),y2=Y(Math.min(0,v)),ht=Math.max(1.5,y2-y1);
      h.push(`<rect x="${x}" y="${y1}" width="${bw}" height="${ht}" rx="4" fill="${s.color}"><title>${esc(s.name)}, year ${y+1}: ${fmt(v)}</title></rect>`);
      h.push(`<text x="${x+bw/2}" y="${v>=0?y1-5:y2+12}" text-anchor="middle" font-size="10.5" font-weight="600" fill="${css("--label2")}">${fmt(v)}</text>`);});
    h.push(`<text x="${L+y*gw+gw/2}" y="${H-6}" text-anchor="middle" font-size="12" font-weight="600" fill="${css("--label")}">Year ${y+1}</text>`);}
  host.innerHTML=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Year by year">${h.join("")}</svg>`;}

/* ---------- navigation ---------- */
function pages(){const out=[["overview","Overview","home","--blueF"]];
  if(D.paths.some(p=>p.screens))out.push(["product","Product","phone","--pinkF"]);
  out.push(["numbers","Numbers","chart","--greenF"]);
  if(D.paths.length>1||D.pathsDoc)out.push(["paths","Paths","signpost","--orangeF"]);
  D.docs.forEach(d=>out.push([d.id,d.label,d.icon,d.color]));
  out.push(["gaps","Gaps","alert","--redF"]);return out;}
function renderNav(){const g=allGaps(),hot=g.filter(x=>x.severity==="high").length;
  $("#nav").innerHTML=`<div class="brand"><div class="v">${esc(D.venture)}</div><div class="s">${esc({explore:"Brainstorm",plan:"Plan",build:"Build"}[D.stage]||"")} · ${esc(D.generated)}</div></div>`+
    pages().map(([id,label,ic,c])=>`<a class="nav" href="#${id}" ${st.page===id?'aria-current="page"':""}>${tile(ic,c)}<span>${label}</span>${id==="gaps"&&g.length?`<span class="cnt ${hot?"hot":""}">${hot||g.length}</span>`:""}</a>`).join("");}
function go(){const id=(location.hash||"#overview").slice(1).split("/")[0];st.page=pages().some(p=>p[0]===id)?id:"overview";
  document.querySelectorAll(".page").forEach(p=>p.classList.toggle("on",p.id==="p-"+st.page));renderNav();render();window.scrollTo(0,0);}
function render(){({overview:rOverview,product:rProduct,numbers:rNumbers,paths:rPaths,gaps:rGaps}[st.page]||rDoc)();}

/* ---------- overview ---------- */
function rOverview(){const i=st.sel,p=D.paths[i],a=effective(i),r=results(a),bk=baseKey(a),rows=r[bk],s=summarize(rows),v=verdict(a,rows),ue=unitEconomics(a,scenariosOf(a)[bk]);
  const N=rows.length,yrs=Math.round(N/12),bl=blocks(a),unv=bl.filter(b=>srcState(b)!=="ok").length,last=rows[N-1];
  const sc=p.screens,shot=sc?sc.screens.find(x=>x.id===sc.start)||sc.screens[0]:null;
  const top=allGaps().filter(g=>g.severity==="high").slice(0,3);
  const futures=Object.keys(r).map((n,k)=>{const sm=summarize(r[n]),vv=verdict(a,r[n]);return `<div class="future">
      <div class="fh"><span class="dot" style="background:${scColor(n,k)}"></span>${esc(scLabel(n))}<span class="vi" style="color:var(${vv.c})">${icon(vv.icon)}</span></div>
      <div class="fv"><div>Pays for itself<b>${sm.break_even?"Month "+sm.break_even:"Not in "+yrs+" yrs"}</b></div><div>Cash needed<b class="${sm.funding>0?"":""}">${sm.funding>0?money(sm.funding,a,true):"None"}</b></div></div>
      ${spark(r[n].map(x=>x.cash),scColor(n,k),true)}<div class="cap">Cash over ${yrs} years</div></div>`;}).join("");
  $("#p-overview").innerHTML=`<header class="ph"><div class="eyebrow">${esc({explore:"Brainstorm",plan:"Business plan",build:"Build"}[D.stage]||"Venture")}${D.paths.length>1?" · "+esc(p.name):""}</div>
    <h1>${esc(D.venture)}</h1>${D.concept?`<p class="lede">${D.concept}</p>`:""}</header>
    <div class="ov"><div>
      <div class="card verdict"><span class="vicon" style="--c:var(${v.c})">${icon(v.icon)}</span><div><div class="vt">${esc(v.t)}</div><div class="vs">${esc(v.s)}</div>
        <div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap">${unv?`<a class="chip" href="#validation" style="--c:var(--orange);text-decoration:none">${icon("flask")} ${unv} of ${bl.length} assumptions unverified</a>`:`<span class="chip" style="--c:var(--green)">${icon("check")} All assumptions sourced</span>`}
        ${D.paths.length>1?`<a class="chip" href="#paths" style="--c:var(--blue);text-decoration:none">${icon("signpost")} ${D.paths.length} paths compared</a>`:""}</div></div></div>
      <div class="metrics">
        ${metric("calendar","--blueF","Pays for itself",s.break_even?`Month ${s.break_even}`:"Not yet",`first month the business covers its costs`)}
        ${metric("wallet","--orangeF","Cash needed",s.funding>0?money(s.funding,a,true):"None",`beyond your ${money(+val(a,"starting_cash",0),a,true)} starting cash`)}
        ${metric("trend","--greenF","Revenue, year "+yrs,money(last.gross_revenue,a,true)+"<small>/mo</small>","",spark(rows.map(x=>x.gross_revenue),css("--greenF")))}
        ${metric("users","--indigoF",cap1(a.customers.label||"customers"),cnt(last.active),`active at the end of year ${yrs}`)}
        ${metric("clock","--tealF","Payback",ue.payback==null?"Never":ue.payback.toFixed(1)+"<small> mo</small>","to earn back what one customer cost")}
        ${metric("target","--purpleF","Lifetime value",ue.ltv_cac==null?"—":ue.ltv_cac.toFixed(1)+"<small>× cost</small>","what a customer brings vs. what they cost")}
      </div>
      <h2 class="sh">Three futures</h2><div class="row3">${futures}</div>
      ${top.length?`<h2 class="sh">Fix these first</h2><div class="glist">${top.map(g=>`<a class="gitem" href="#gaps" style="text-decoration:none;color:inherit">${tile("alert","--redF","sm")}<span class="gt">${esc(g.title)}</span>${icon("chevron-right")}</a>`).join("")}</div>`:""}
      <h2 class="sh">Next step</h2><div class="card" style="display:flex;gap:14px;align-items:center">${tile("arrow","--blueF","lg")}<div style="font-size:16px">${esc(D.next)}</div></div>
    </div>
    <div>${shot?`<div class="card" style="display:flex;flex-direction:column;align-items:center;gap:14px"><div class="cap" style="align-self:flex-start;font-weight:600">The product</div>
      <div id="ovdev"></div><a class="btn pri" href="#product" style="text-decoration:none">${icon("play")} Open the prototype</a></div>`:
      `<div class="card"><div class="cap" style="font-weight:600;margin-bottom:6px">The product</div><div class="cap">No screens yet. A clickable preview appears here once the plan has a screens file.</div></div>`}</div></div>`;
  if(shot){const host=$("#ovdev");device(host,sc,shot.id,{fitH:560,fitW:300,interactive:false});}}
function metric(ic,c,label,value,caption,extra){return `<div class="metric"><div class="mh">${tile(ic,c,"sm")}${esc(label)}</div><div class="mv num">${value}</div>${extra||""}${caption?`<div class="mc">${esc(caption)}</div>`:""}</div>`;}
const cap1=s=>s.charAt(0).toUpperCase()+s.slice(1);

/* ---------- product (clickable prototype) ---------- */
function sets(){return D.paths.map((p,i)=>p.screens?{i,name:p.name,set:p.screens}:null).filter(Boolean);}
function device(host,set,screenId,opt){const plat=set.platform,size=plat==="web"?[1180,760]:[393,852];
  const scale=Math.min(1,(opt.fitW||size[0])/size[0],(opt.fitH||size[1])/size[1]);const t=set.tokens;
  const vars=`--bg:${t.bg};--surface:${t.surface};--text:${t.text};--muted:${t.muted};--accent:${t.accent};--accent-fg:${t.accent_fg};--border:${t.border};--radius:${parseFloat(t.radius)||12}px;--font:${t.font}`;
  const scr=set.screens.find(s=>s.id===screenId)||set.screens[0];
  const chrome=plat==="web"?`<div class="webbar"><i style="background:#ff5f57"></i><i style="background:#febc2e"></i><i style="background:#28c840"></i><div class="url">${esc(D.venture.toLowerCase().replace(/[^a-z0-9]+/g,""))}.com</div></div>`:
    `${plat==="ios"?'<div class="island"></div>':'<div class="punch"></div>'}`;
  const status=plat==="web"?"":`<div class="status" style="color:${t.text}"><span>9:41</span><span class="ic"><svg class="i" viewBox="0 0 24 24" style="width:17px;height:17px"><path d="${IC.chart}"/></svg><span class="bat"></span></span></div><div class="homebar" style="background:${t.text}"></div>`;
  host.innerHTML=`<div class="dev" style="width:${size[0]*scale}px;height:${size[1]*scale}px"><div class="inner f-${plat}" style="transform:scale(${scale})">
    ${plat==="web"?chrome:""}<div class="scr" style="background:${t.bg}">${plat!=="web"?chrome:""}${status}<div class="vbd ${st.hot&&opt.interactive?"hot":""}" style="${vars}">${scr.html}</div></div></div></div>`;
  host.querySelectorAll("i[data-i]").forEach(el=>{el.outerHTML=icon(el.getAttribute("data-i"));});
  if(opt.interactive){const vbd=$(".vbd",host);vbd.addEventListener("click",ev=>{const g=ev.target.closest("[data-go],[data-back]");if(!g)return;ev.preventDefault();
    if(g.hasAttribute("data-back")){const prev=st.hist.pop();if(prev){st.screen=prev;rProduct();}return;}
    const to=g.getAttribute("data-go");if(set.screens.some(s=>s.id===to)){st.hist.push(st.screen);st.screen=to;if(st.flow){const k=st.flow.steps.indexOf(to);if(k>=0)st.flow.i=k;}rProduct();}});}}
function rProduct(){const all=sets();if(!all.length){$("#p-product").innerHTML=`<header class="ph"><h1>Product</h1></header><div class="card empty">No screens yet.</div>`;return;}
  if(st.set===null||!all.some(x=>x.i===st.set)){st.set=(all.find(x=>x.i===st.sel)||all[0]).i;}
  const set=D.paths[st.set].screens;if(!st.screen||!set.screens.some(s=>s.id===st.screen))st.screen=set.start;
  const scr=set.screens.find(s=>s.id===st.screen),links=[...new Set((scr.html.match(/data-go\s*=\s*["']([^"']+)/g)||[]).map(x=>x.replace(/.*["']/,"")))].filter(x=>set.screens.some(s=>s.id===x));
  const fl=st.flow;
  $("#p-product").innerHTML=`<header class="ph"><div class="eyebrow">Clickable prototype</div><h1>Product</h1>
    <p class="lede">Tap anything that leads somewhere, or play a flow. These are the screens the plan says the product needs, drawn in its design language.</p></header>
    ${all.length>1?`<div class="toolbar"><div class="seg" id="setseg">${all.map(x=>`<button aria-pressed="${x.i===st.set}" data-i="${x.i}">${esc(x.name)}</button>`).join("")}</div></div>`:""}
    <div class="prod"><div class="devwrap">
      <div class="flowbar">${fl?`<button id="fprev" aria-label="Previous step">${icon("chevron-left")}</button><span class="ft">${esc(fl.name)}</span><span class="cap">Step ${fl.i+1} of ${fl.steps.length}</span>
        <span class="pips">${fl.steps.map((_,k)=>`<span class="${k===fl.i?"on":""}"></span>`).join("")}</span><button id="fnext" aria-label="Next step">${icon("chevron-right")}</button><button id="fstop" aria-label="Stop flow">${icon("x")}</button>`:
        `${icon("eye")}<span class="cap">Tap to explore${st.hist.length?"":""}</span>${st.hist.length?`<button id="back" aria-label="Back">${icon("chevron-left")}</button>`:""}<button id="home" aria-label="Start screen">${icon("rotate")}</button>`}</div>
      <div id="dev"></div></div>
    <div>
      <div class="group"><div class="gh">${tile("phone","--pinkF","sm")} This screen</div><div class="glist"><div class="grow">
        <div style="font-size:20px;font-weight:700;letter-spacing:-.015em">${esc(scr.title)}</div>
        ${scr.for?`<div class="cap" style="margin-top:2px">For ${esc(scr.for)}</div>`:""}
        ${scr.notes?`<div style="margin-top:8px;font-size:14.5px">${esc(scr.notes)}</div>`:""}
        ${links.length?`<div class="cap" style="margin-top:10px">Leads to</div><div class="linkchips">${links.map(l=>`<button data-to="${esc(l)}">${esc((set.screens.find(s=>s.id===l)||{}).title||l)} ›</button>`).join("")}</div>`:""}
      </div></div></div>
      ${set.flows.length?`<div class="group"><div class="gh">${tile("play","--blueF","sm")} Flows</div><div class="glist">${set.flows.map((f,k)=>`<button class="gitem" data-flow="${k}">${tile("play",fl&&fl.name===f.name?"--greenF":"--blueF","sm")}<span><span class="gt">${esc(f.name)}</span><br><span class="cap">${f.steps.length} screens</span></span>${icon("chevron-right")}</button>`).join("")}</div></div>`:""}
      <div class="group"><div class="glist"><div class="grow toggle"><span>Show what's tappable</span><input type="checkbox" class="sw" id="hot" ${st.hot?"checked":""} aria-label="Show what's tappable"></div></div></div>
      <div class="cap">${set.screens.length} screens · ${esc(set.platform==="web"?"web":set.platform==="android"?"Android":"iPhone")} · ${esc(D.paths[st.set].name)}</div>
    </div></div>
    <h2 class="sh">All screens</h2><div class="strip" id="strip"></div>`;
  const fit=Math.min(720,window.innerHeight-170);device($("#dev"),set,st.screen,{fitH:fit,fitW:Math.min(set.platform==="web"?760:420,$("#p-product").clientWidth-20),interactive:true});
  const strip=$("#strip");set.screens.forEach(s=>{const b=document.createElement("button");b.className="thumb";b.setAttribute("aria-current",s.id===st.screen);
    b.innerHTML=`<div class="mini"></div><span>${esc(s.title)}</span>`;strip.appendChild(b);device($(".mini",b),set,s.id,{fitH:set.platform==="web"?110:190,interactive:false});
    b.onclick=()=>{st.hist.push(st.screen);st.screen=s.id;st.flow=null;rProduct();};});
  document.querySelectorAll("#setseg button").forEach(b=>b.onclick=()=>{st.set=+b.dataset.i;st.screen=null;st.hist=[];st.flow=null;rProduct();});
  document.querySelectorAll("[data-to]").forEach(b=>b.onclick=()=>{st.hist.push(st.screen);st.screen=b.dataset.to;rProduct();});
  document.querySelectorAll("[data-flow]").forEach(b=>b.onclick=()=>{const f=set.flows[+b.dataset.flow];st.flow={name:f.name,steps:f.steps,i:0};st.hist=[];st.screen=f.steps[0];rProduct();});
  const on=(id,fn)=>{const el=$("#"+id);if(el)el.onclick=fn;};
  on("fprev",()=>{if(fl.i>0){fl.i--;st.screen=fl.steps[fl.i];rProduct();}});on("fnext",()=>{if(fl.i<fl.steps.length-1){fl.i++;st.screen=fl.steps[fl.i];rProduct();}});
  on("fstop",()=>{st.flow=null;rProduct();});on("back",()=>{const p=st.hist.pop();if(p){st.screen=p;rProduct();}});on("home",()=>{st.screen=set.start;st.hist=[];rProduct();});
  $("#hot").onchange=e=>{st.hot=e.target.checked;rProduct();};}

/* ---------- numbers ---------- */
const DRIVERS=[
 {g:"Customers",ic:"users",c:"--blueF",src:"c",items:[
  {k:"new_first_month",label:"New in month 1",max:o=>Math.max(10,Math.ceil(o*4)),step:o=>o<40?1:Math.max(1,Math.round(o/20)),fmt:v=>cnt(v)},
  {k:"new_growth_monthly",label:"Growth in new customers",max:()=>.5,step:()=>.005,fmt:v=>pct(v,1)+" a month"},
  {k:"churn_monthly",label:"Customers lost",max:()=>.3,step:()=>.0025,fmt:v=>pct(v,1)+" a month"}]},
 {g:"Acquisition",ic:"target",c:"--orangeF",src:"c",items:[
  {k:"cac",label:"Cost to win a customer",max:o=>Math.max(100,Math.ceil(o*4)),step:o=>o<200?1:5,fmt:(v,a)=>money(v,a)}]},
 {g:"Pricing",ic:"tag",c:"--greenF",src:"r",items:[
  {k:"price_mult",label:"All prices",min:.5,max:()=>2,step:()=>.05,fmt:v=>v===1?"As planned":(v>1?"+":"−")+Math.round(Math.abs(v-1)*100)+"%"}]},
 {g:"Costs",ic:"receipt",c:"--redF",src:"f",items:[
  {k:"fixed_mult",label:"Fixed costs",min:.5,max:()=>2,step:()=>.05,fmt:v=>v===1?"As planned":(v>1?"+":"−")+Math.round(Math.abs(v-1)*100)+"%"}]},
 {g:"Cash",ic:"wallet",c:"--tealF",src:"s",items:[
  {k:"starting_cash",label:"Starting cash",max:o=>Math.max(50000,Math.ceil(o*4/1000)*1000),step:o=>o>=20000?1000:500,fmt:(v,a)=>money(v,a)}]}];
function shortSrc(s){s=String(s||"").replace(/^UNVERIFIED:\s*/i,"");const cut=s.split(/[;.]/)[0].trim();return cut.length>70?cut.slice(0,68)+"…":cut;}
function groupSource(a,src){if(src==="c")return [srcState(a.customers),a.customers.source||""];
  const list=src==="r"?a.revenue_lines:src==="f"?(a.fixed_costs||[]):[];if(!list.length)return ["ok","Your own figure"];
  const s=list.map(srcState),worst=s.includes("missing")?"missing":s.includes("unverified")?"unverified":"ok",n=s.filter(x=>x!=="ok").length;
  return [worst,n?`${n} of ${list.length} not yet verified`:`All ${list.length} sourced`];}
function series(){const out=[];
  if(st.mode==="scen"){const a=effective(st.sel),r=results(a);Object.keys(r).forEach((n,k)=>out.push({name:scLabel(n),color:scColor(n,k),rows:r[n],a,bold:n==="base"}));}
  else D.paths.forEach((p,i)=>{const a=effective(i),r=results(a),k=r[st.scen]?st.scen:Object.keys(r)[0];out.push({name:p.name,color:css(P_COLOR[i%6]),rows:r[k],a,bold:i===st.sel});});
  return out;}
const METRICS={gross_revenue:["Monthly revenue","Revenue"],net:["Monthly profit or loss","Profit"],cash:["Cash in the bank","Cash"],active:["Active customers","Customers"]};
function rNumbers(){const multi=D.paths.length>1,p=D.paths[st.sel];
  $("#p-numbers").innerHTML=`<header class="ph"><div class="eyebrow">Projections</div><h1>Numbers</h1><p class="lede">Drag a slider and watch every chart move. The grey tick on each slider is where the plan started.</p></header>
    <div class="toolbar">${multi?`<div class="seg" id="psel">${D.paths.map((x,i)=>`<button aria-pressed="${i===st.sel}" data-i="${i}" title="${esc(x.name)}">${esc(x.name.length>26?x.name.slice(0,25)+"…":x.name)}</button>`).join("")}</div>`:""}
      <div class="seg" id="mseg">${Object.entries(METRICS).map(([k,v])=>`<button aria-pressed="${k===st.metric}" data-k="${k}">${v[1]}</button>`).join("")}</div>
      <span class="sp"></span>${multi?`<div class="seg" id="modeseg"><button aria-pressed="${st.mode==="scen"}" data-m="scen">Three futures</button><button aria-pressed="${st.mode==="paths"}" data-m="paths">Compare paths</button></div>`:""}
      ${multi&&st.mode==="paths"?`<div class="seg" id="scseg">${Object.keys(scenariosOf(p.assumptions)).map(n=>`<button aria-pressed="${n===st.scen}" data-s="${n}">${esc(scShort(n))}</button>`).join("")}</div>`:""}</div>
    <div class="nb"><div>
      <div class="card"><div class="ct"><span class="t">${METRICS[st.metric][0]}</span><span class="sp"></span></div><div class="ct"><span class="v num" id="headv"></span><span class="cap" id="heads"></span></div>
        <div class="chart" id="lc"></div><div class="legend" id="lg"></div></div>
      <h2 class="sh">${tile("calendar","--blueF")} Year by year</h2><div class="card"><div id="yb"></div><div class="legend" id="lg2"></div></div>
      <div class="row2" style="margin-top:16px">
        <div><h2 class="sh" style="margin-top:18px">${tile("target","--orangeF")} What matters most</h2><div class="glist sens" id="sens"></div><div class="legend"><span><span class="dot" style="background:var(--redF)"></span>20% worse</span><span><span class="dot" style="background:var(--greenF)"></span>20% better</span><span><span class="dot" style="background:var(--orangeF)"></span>a guess so far</span></div><div class="gf">Effect on cash at the end. Test the top one first.</div></div>
        <div><h2 class="sh" style="margin-top:18px">${tile("chart","--greenF")} At scale</h2><div class="glist scl" id="scl"></div><div class="legend"><span><span class="dot" style="background:var(--redF)"></span>costs</span><span><span class="dot" style="background:var(--greenF)"></span>margin</span></div><div class="gf">Each month, once growth settles.</div></div>
      </div></div>
    <div id="drv"></div></div>`;
  const bind=(sel,fn)=>document.querySelectorAll(sel).forEach(b=>b.onclick=()=>fn(b));
  bind("#psel button",b=>{st.sel=+b.dataset.i;rNumbers();});bind("#mseg button",b=>{st.metric=b.dataset.k;rNumbers();});
  bind("#modeseg button",b=>{st.mode=b.dataset.m;rNumbers();});bind("#scseg button",b=>{st.scen=b.dataset.s;rNumbers();});
  rDrivers();liveNumbers();}
function liveNumbers(){const S=series(),a=S[0].a,key=st.metric,fmt=key==="active"?v=>cnt(v):v=>money(v,a,true);
  const main=S.find(s=>s.bold)||S[0],last=main.rows[main.rows.length-1],N=main.rows.length;
  $("#headv").textContent=fmt(last[key]);$("#heads").textContent=`${main.name}, month ${N}`;
  lineChart($("#lc"),S,key,fmt);yearBars($("#yb"),S,key,fmt);
  const lg=S.map(s=>`<span><span class="dot" style="background:${s.color}"></span>${esc(s.name)}</span>`).join("");$("#lg").innerHTML=lg;$("#lg2").innerHTML=lg+`<span class="cap">${key==="cash"||key==="active"?"at the end of each year":"total for each year"}</span>`;
  rSens();rScale();renderNav();}
function rDrivers(){const i=st.sel,p=D.paths[i],o=defaults(p.assumptions),s=sliders(i),a=p.assumptions;
  $("#drv").innerHTML=DRIVERS.map(G=>{const gs=G.src!=="s"?groupSource(a,G.src):null;
    return `<div class="group"><div class="gh">${tile(G.ic,G.c,"sm")} ${G.g}</div><div class="glist">${G.items.map(d=>{const mn=d.min==null?0:d.min,mx=d.max(o[d.k]),pos=(o[d.k]-mn)/((mx-mn)||1)*100;
      return `<div class="grow"><div class="gline"><span class="gl">${d.label}</span><span class="gv ${s[d.k]!==o[d.k]?"changed":""}" id="v_${d.k}">${d.fmt(s[d.k],a)}</span></div>
        <div class="rng"><span class="tick" style="left:${Math.max(0,Math.min(100,pos))}%"></span><input type="range" id="s_${d.k}" aria-label="${d.label}" min="${mn}" max="${mx}" step="${d.step(o[d.k])}" value="${s[d.k]}"></div>
        <div class="gwas" id="w_${d.k}">${s[d.k]!==o[d.k]?"Plan: "+d.fmt(o[d.k],a):""}</div></div>`;}).join("")}</div>
      ${gs?`<div class="gf" title="${esc(gs[1])}">${badgeFor(gs[0])}<span>${esc(shortSrc(gs[1]))}</span></div>`:""}</div>`;}).join("")+
    `<div class="btns"><button class="btn" id="reset">${icon("rotate")} Reset</button><button class="btn pri" id="copy">${icon("copy")} Copy these assumptions</button></div><textarea class="copy" id="copybox" aria-label="Assumptions JSON"></textarea>
     <div class="gf">To keep a change, paste it over ${esc(p.file)} and rerun model.py.</div>`;
  DRIVERS.forEach(G=>G.items.forEach(d=>{const inp=$("#s_"+d.k);inp.oninput=()=>{s[d.k]=+inp.value;const v=$("#v_"+d.k);v.textContent=d.fmt(s[d.k],a);
    v.classList.toggle("changed",s[d.k]!==o[d.k]);$("#w_"+d.k).textContent=s[d.k]!==o[d.k]?"Plan: "+d.fmt(o[d.k],a):"";liveNumbers();};}));
  $("#reset").onclick=()=>{st.sliders[i]=defaults(a);rNumbers();};
  $("#copy").onclick=()=>{const txt=JSON.stringify(effective(i),null,2),box=$("#copybox"),show=()=>{box.style.display="block";box.value=txt;box.select();};
    if(navigator.clipboard&&window.isSecureContext)navigator.clipboard.writeText(txt).then(()=>{$("#copy").lastChild.textContent=" Copied";setTimeout(()=>{$("#copy").lastChild.textContent=" Copy these assumptions";},1500);},show);else show();};}
const SENS=[{k:"new_first_month",label:"New customers",up:true,src:"c"},{k:"new_growth_monthly",label:"Growth",up:true,src:"c"},{k:"churn_monthly",label:"Churn",up:false,src:"c"},
  {k:"cac",label:"Cost to win",up:false,src:"c"},{k:"price_mult",label:"Prices",up:true,src:"r"},{k:"fixed_mult",label:"Fixed costs",up:false,src:"f"}];
function sensitivity(i){const base=sliders(i),a0=D.paths[i].assumptions,sc=scenariosOf(a0),bk=baseKey(a0);
  const end=sl=>{const r=runModel(effective(i,sl),sc[bk]);return r[r.length-1].cash;},ref=end(base);
  return SENS.map(d=>{const lo=Object.assign({},base),hi=Object.assign({},base);lo[d.k]=base[d.k]*.8;hi[d.k]=base[d.k]*1.2;
    const dl=end(lo)-ref,dh=end(hi)-ref;return {d,worse:d.up?dl:dh,better:d.up?dh:dl,range:Math.abs(dh-dl)};}).sort((x,y)=>y.range-x.range);}
function rSens(){const el=$("#sens");if(!el)return;const a=D.paths[st.sel].assumptions,rs=sensitivity(st.sel),mx=Math.max(1,...rs.map(r=>Math.max(Math.abs(r.worse),Math.abs(r.better))));
  el.innerHTML=rs.map((r,k)=>{const w=Math.abs(r.worse)/mx*50,b=Math.abs(r.better)/mx*50,state=groupSource(a,r.d.src)[0];
    return `<div class="sr ${k===0?"top":""}"><span class="sl"><span>${state==="ok"?"":`<span class="dot" title="${state==="missing"?"No source":"Unverified"}" style="background:var(${state==="missing"?"--redF":"--orangeF"});margin-right:6px"></span>`}${r.d.label}</span></span><div class="track" title="20% worse: ${money(r.worse,a,true)} · 20% better: ${money(r.better,a,true)}"><span class="mid"></span>
      <span class="b" style="right:50%;width:${w}%;background:var(--redF)"></span><span class="b" style="left:50%;width:${b}%;background:var(--greenF)"></span></div></div>`;}).join("");}
function rScale(){const el=$("#scl");if(!el)return;const a=effective(st.sel),pts=a.scale_points||[100,1000,10000,100000];
  el.innerHTML=pts.map(n=>{const r=atScale(a,n),cost=r.fees+r.variable+r.fixed,tot=Math.max(r.revenue,cost)||1,cw=cost/tot*100,mw=Math.max(0,r.margin)/tot*100;
    const lab=r.revenue<=0?"No revenue":cost>=2*r.revenue?`Costs ${cost/r.revenue>=10?Math.round(cost/r.revenue):(cost/r.revenue).toFixed(1)}×`:pct(r.margin_pct);
    return `<div class="sr"><span><b class="num">${cnt(n)}</b><br><span class="cap">${money(r.revenue,a,true)}/mo</span></span><div class="stack" title="Revenue ${money(r.revenue,a)} · costs ${money(cost,a)}">
      <span style="width:${Math.min(100,cw)}%;background:var(--redF);opacity:.85"></span><span style="width:${mw}%;background:var(--greenF)"></span></div>
      <span class="m" style="color:var(${r.margin<0?"--red":"--green"})">${lab}</span></div>`;}).join("");}

/* ---------- paths ---------- */
function rPaths(){const cards=D.paths.map((p,i)=>{const a=effective(i),r=results(a),bk=baseKey(a),rows=r[bk],s=summarize(rows),v=verdict(a,rows),N=rows.length;
    return `<button class="pcard" aria-pressed="${i===st.sel}" data-i="${i}">${p.recommended?`<span class="chip rec" style="--c:var(--blue)">${icon("star")} Recommended</span>`:""}
      <div class="pn">${tile("signpost",P_COLOR[i%6])}${esc(p.name)}</div><div class="ps">${esc(p.summary||p.file)}</div>
      <span class="chip" style="--c:var(${v.c.replace("F","")})">${icon(v.icon)} ${esc(v.t)}</span>
      ${spark(rows.map(x=>x.cash),css(P_COLOR[i%6]),true)}
      <div class="pk"><div>Pays for itself<b>${s.break_even?"M"+s.break_even:"Never"}</b></div><div>Cash needed<b>${s.funding>0?money(s.funding,a,true):"None"}</b></div><div>Year ${Math.round(N/12)} revenue<b>${money(rows[N-1].gross_revenue,a,true)}/mo</b></div></div>
      <div class="legend" style="margin:0">${Object.keys(r).map((n,k)=>{const vv=verdict(a,r[n]);return `<span style="color:var(${vv.c.replace("F","")})">${icon(vv.icon)} ${esc(scShort(n))}</span>`;}).join("")}</div></button>`;}).join("");
  $("#p-paths").innerHTML=`<header class="ph"><div class="eyebrow">Options</div><h1>Paths</h1><p class="lede">Each card is a different way to build the same idea, in the expected case. The marks underneath show how it does in a bad, expected and great future.</p></header>
    <div class="pcards">${cards}</div>
    ${D.paths.length>1?`<h2 class="sh">${tile("wallet","--tealF")} Cash, side by side</h2><div class="card"><div class="chart" id="pc"></div><div class="legend" id="pcl"></div></div>`:""}
    ${D.pathsDoc?`<h2 class="sh">${tile("doc","--blueF")} The reasoning</h2><div class="doc"><nav class="toc">${D.pathsDoc.toc.map(t=>`<a href="#paths" data-sec="${t[0]}">${esc(t[1])}</a>`).join("")}</nav><article class="art">${D.pathsDoc.html}</article></div>`:""}`;
  document.querySelectorAll(".pcard").forEach(b=>b.onclick=()=>{st.sel=+b.dataset.i;st.mode="scen";location.hash="#numbers";});
  tocLinks($("#p-paths"));
  if(D.paths.length>1){const S=D.paths.map((p,i)=>{const a=effective(i),r=results(a);return {name:p.name,color:css(P_COLOR[i%6]),rows:r[baseKey(a)],a,bold:i===st.sel};});
    lineChart($("#pc"),S,"cash",v=>money(v,S[0].a,true));$("#pcl").innerHTML=S.map(s=>`<span><span class="dot" style="background:${s.color}"></span>${esc(s.name)}</span>`).join("")+`<span class="cap">expected case</span>`;}}

/* ---------- documents ---------- */
function tocLinks(root){root.querySelectorAll("[data-sec]").forEach(a=>a.onclick=e=>{e.preventDefault();const t=document.getElementById(a.dataset.sec);if(t)t.scrollIntoView({behavior:"smooth",block:"start"});});}
function rDoc(){const d=D.docs.find(x=>x.id===st.page);if(!d)return;const el=$("#p-"+d.id);
  el.innerHTML=`<header class="ph"><div class="eyebrow">${esc(d.file)}</div><h1>${esc(d.label)}</h1></header>
    ${d.draft?`<div class="chip draft" style="--c:var(--orange)">${icon("alert")} Draft — some sections are not written yet</div>`:""}
    <div class="doc"><nav class="toc">${d.toc.map(t=>`<a href="#${d.id}" data-sec="${t[0]}">${esc(t[1])}</a>`).join("")}</nav><article class="art">${d.html}</article></div>`;
  tocLinks(el);}

/* ---------- gaps ---------- */
function liveGaps(){const i=st.sel,p=D.paths[i],a=effective(i),sc=scenariosOf(a),r=results(a),g=[],N=+val(a,"months",36),bk=baseKey(a),b=summarize(r[bk]);
  if(b.funding>0)g.push({severity:"high",title:`Needs ${money(b.funding,a,true)} more than your starting cash`,detail:`In the expected case cash bottoms out in month ${b.low_month}. Decide now where that money comes from.`,where:p.file});
  Object.keys(r).forEach(n=>{if(summarize(r[n]).break_even===null)g.push({severity:n===bk?"high":"medium",title:`${scLabel(n)}: never pays for itself in ${Math.round(N/12)} years`,detail:"Monthly profit stays below zero for the whole projection.",where:p.file});});
  if(b.break_even&&b.break_even>24)g.push({severity:"medium",title:`Takes ${b.break_even} months to pay for itself`,detail:"Long for a self-funded company. Compare against your runway.",where:p.file});
  const ue=unitEconomics(a,sc[bk]||{});
  if(ue.margin<=0)g.push({severity:"high",title:"Each customer loses money",detail:`Margin per customer is ${money(ue.margin,a)} a month before acquisition costs, so growth makes it worse.`,where:p.file});
  else{if(ue.payback!=null&&ue.payback>12)g.push({severity:"high",title:`Takes ${ue.payback.toFixed(0)} months to earn back a customer`,detail:"Over a year to recover what it cost to win them. Growth will need outside money.",where:p.file});
    if(ue.ltv_cac!=null&&ue.ltv_cac<3)g.push({severity:"medium",title:`A customer is worth only ${ue.ltv_cac.toFixed(1)}× what they cost`,detail:"Below about 3× there's little room for mistakes in price or churn.",where:p.file});}
  const rs=sensitivity(i);if(rs.length){const t=rs[0],state=groupSource(p.assumptions,t.d.src)[0];
    if(state!=="ok")g.push({severity:"high",title:`Everything hinges on ${t.d.label.toLowerCase()}, and it's ${state==="missing"?"unsourced":"a guess"}`,detail:`A 20% miss moves final cash by ${money(Math.abs(t.worse),a,true)}. Test this with real customers before anything else.`,where:p.file});}
  a.revenue_lines.forEach(l=>{if(+val(l,"store_commission",0)>0)g.push({severity:"info",title:`${l.name} gives ${pct(l.store_commission)} to the app store`,detail:"If it's used in the real world, or can be sold on the web, it may not owe this. See traps T01 and T02.",where:p.file});});
  if(!(a.fixed_costs||[]).length)g.push({severity:"medium",title:"No fixed costs at all",detail:"Is nobody paid and nothing bought? Hires and tools from the department plan belong here.",where:p.file});
  const bl=blocks(a),miss=bl.filter(x=>srcState(x)==="missing").length,unv=bl.filter(x=>srcState(x)==="unverified").length;
  if(miss)g.push({severity:"high",title:`${miss} assumption(s) have no source`,detail:"Give each a source, or say UNVERIFIED and why.",where:p.file});
  if(unv)g.push({severity:"low",title:`${unv} of ${bl.length} assumptions are guesses so far`,detail:"Normal while planning. 'What matters most' on Numbers shows which to test first.",where:p.file});
  return g;}
function allGaps(){const o={high:0,medium:1,low:2,info:3};return liveGaps().concat(D.gaps||[]).sort((x,y)=>o[x.severity]-o[y.severity]);}
const SEV={high:["alert","--redF","Fix first"],medium:["alert","--orangeF","Worth fixing"],low:["info","--grayF","Keep in mind"],info:["info","--blueF","Opportunity"]};
function rGaps(){const all=allGaps(),f=st.gfilter,shown=all.filter(g=>f==="all"||g.severity===f),counts=s=>all.filter(g=>g.severity===s).length,p=D.paths[st.sel];
  const groups=["high","medium","low","info"].map(s=>{const items=shown.filter(g=>g.severity===s);if(!items.length)return "";
    return `<div class="group"><div class="gh">${tile(SEV[s][0],SEV[s][1],"sm")} ${SEV[s][2]} · ${items.length}</div><div class="glist">${items.map((g,k)=>{const id=s+k;
      return `<div class="gwrap ${st.open[id]?"open":""}"><button class="gitem" data-g="${id}" aria-expanded="${!!st.open[id]}">${tile(SEV[s][0],SEV[s][1],"sm")}<span class="gt">${esc(g.title)}</span><span class="gw">${esc(g.where||"")} ${icon(st.open[id]?"x":"chevron-right")}</span></button>
        <div class="gdet">${esc(g.detail)}${g.where?`<div class="fix chip" style="--c:var(--blue)">${icon("doc")} Fix in ${esc(g.where)}</div>`:""}</div></div>`;}).join("")}</div></div>`;}).join("");
  $("#p-gaps").innerHTML=`<header class="ph"><div class="eyebrow">What's missing</div><h1>Gaps</h1><p class="lede">Found in the numbers for ${esc(p.name)} and in the plan files. Tap one to see why it matters and where to fix it.</p></header>
    <div class="toolbar"><div class="seg" id="gseg">${[["all","All "+all.length],["high","Fix first "+counts("high")],["medium","Worth fixing "+counts("medium")],["low","Keep in mind "+counts("low")]].map(([k,l])=>`<button aria-pressed="${k===f}" data-f="${k}">${l}</button>`).join("")}</div></div>
    ${groups||`<div class="card empty">${icon("check")} Nothing here.</div>`}`;
  document.querySelectorAll("#gseg button").forEach(b=>b.onclick=()=>{st.gfilter=b.dataset.f;rGaps();});
  document.querySelectorAll("[data-g]").forEach(b=>b.onclick=()=>{st.open[b.dataset.g]=!st.open[b.dataset.g];rGaps();});}

$("#foot").innerHTML=`Generated ${esc(D.generated)} by venture-blueprint from the plan files. Everything is computed in this page — nothing is sent anywhere.`;
window.addEventListener("hashchange",go);
let rt;window.addEventListener("resize",()=>{clearTimeout(rt);rt=setTimeout(render,150);});
if(window.matchMedia)window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change",render);
go();
})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    sys.exit(main())
