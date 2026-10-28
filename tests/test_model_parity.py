#!/usr/bin/env python3
"""The venture site's JavaScript model must match model.py exactly.

Builds a venture site, pulls the model script out of it, runs it under Node on
the same inputs as model.py, and compares every field of every month for
every scenario. Covers each revenue kind, growth caps, step costs, start and
end months, store commission and processing fees, and default scenarios.

Needs Node. Skips (exit 0) if Node is not installed.

Usage:  python3 -I tests/test_model_parity.py
"""

import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "plugins/venture-blueprint/skills/venture-blueprint/scripts"
TEMPLATES = SCRIPTS.parent / "templates"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


EDGE = {
    "venture": "Edge cases",
    "months": 30,
    "starting_cash": 5000,
    "customers": {"starting": 12, "new_first_month": 3.5, "new_growth_monthly": 0.3,
                  "new_max_per_month": 40, "churn_monthly": 0.09, "cac": 75,
                  "source": "test"},
    "revenue_lines": [
        {"name": "Sub", "kind": "subscription", "price": 19, "attach_rate": 0.4,
         "store_commission": 0.15, "processing_pct": 0.029, "processing_fixed": 0.3,
         "source": "test"},
        {"name": "Take", "kind": "take_rate", "rate": 0.08, "gmv_per_customer_month": 900,
         "transactions_per_customer_month": 6, "processing_fixed": 0.1, "source": "test"},
        {"name": "Setup", "kind": "one_time", "price": 250, "attach_rate": 0.5,
         "processing_pct": 0.03, "source": "test"},
        {"name": "Units", "kind": "per_unit", "price": 0.4, "units_per_customer_month": 55,
         "source": "test"},
    ],
    "variable_costs": [{"name": "Infra", "per_customer_month": 2.2, "source": "test"},
                       {"name": "Support", "pct_of_revenue": 0.05, "source": "test"},
                       {"name": "Both", "per_customer_month": 0.5, "pct_of_revenue": 0.01,
                        "source": "test"}],
    "fixed_costs": [{"name": "Base", "monthly": 300,
                     "steps": [{"at_customers": 60, "monthly": 900},
                               {"at_customers": 25, "monthly": 500}], "source": "test"},
                    {"name": "Late", "monthly": 2000, "start_month": 7, "source": "test"},
                    {"name": "Early", "monthly": 1500, "end_month": 5, "source": "test"}],
}

HARNESS = r"""
const fs = require("fs"), vm = require("vm");
const code = fs.readFileSync(process.argv[2], "utf8");
const cases = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
const ctx = {}; vm.createContext(ctx); vm.runInContext(code, ctx);
const out = cases.map(a => {
  const sc = ctx.scenariosOf(a), res = {};
  for (const n of Object.keys(sc)) res[n] = ctx.runModel(a, sc[n]);
  const ue = {}; for (const n of Object.keys(sc)) ue[n] = ctx.unitEconomics(a, sc[n]);
  const scale = (a.scale_points || [100, 1000, 10000]).map(n => ctx.atScale(a, n));
  return {res, ue, scale};
});
process.stdout.write(JSON.stringify(out));
"""


def close(x, y):
    if x is None or y is None:
        return x is None and y is None
    return abs(x - y) <= max(1e-6, abs(y) * 1e-9)


def main():
    node = shutil.which("node")
    if not node:
        print("SKIP: node not installed")
        return 0
    model, build_site = load("model"), load("build_site")

    example = json.loads((TEMPLATES / "assumptions.example.json").read_text())
    no_scen = json.loads(json.dumps(EDGE)); no_scen.pop("scenarios", None)
    empty_scen = json.loads(json.dumps(EDGE)); empty_scen["scenarios"] = {}
    custom = json.loads(json.dumps(EDGE))
    custom["scenarios"] = {"downside": {"churn_x": 2, "price_x": 0.8}, "base": {},
                           "upside": {"new_x": 1.5, "growth_x": 1.3, "cac_x": 0.5, "price_x": 1.2}}
    cases = [example, no_scen, empty_scen, custom]
    for a in cases:
        model.validate(a)

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "plan").mkdir()
        (td / "plan" / "assumptions.json").write_text(json.dumps(example))
        sys.argv = ["build_site.py", str(td / "plan")]
        assert build_site.main() == 0
        html = (td / "plan" / "venture.html").read_text()
        code = re.search(r'<script id="vb-model">(.*?)</script>', html, re.S).group(1)
        (td / "model.js").write_text(code)
        (td / "cases.json").write_text(json.dumps(cases))
        (td / "harness.js").write_text(HARNESS)
        raw = subprocess.run([node, str(td / "harness.js"), str(td / "model.js"),
                              str(td / "cases.json")], capture_output=True, text=True, check=True)
        js = json.loads(raw.stdout)

    fields = ["new", "churned", "active", "gross_revenue", "fees", "variable_costs",
              "gross_margin", "fixed_costs", "acquisition_spend", "net", "cash"]
    checked, problems = 0, []
    for ci, a in enumerate(cases):
        scen = a.get("scenarios") or model.DEFAULT_SCENARIOS
        for name, sc in scen.items():
            py_rows = model.run(a, sc)
            js_rows = js[ci]["res"][name]
            if len(py_rows) != len(js_rows):
                problems.append(f"case {ci} {name}: {len(py_rows)} vs {len(js_rows)} months")
                continue
            for pr, jr in zip(py_rows, js_rows):
                for f in fields:
                    checked += 1
                    if not close(jr[f], pr[f]):
                        problems.append(f"case {ci} {name} month {pr['month']} {f}: "
                                        f"py {pr[f]!r} js {jr[f]!r}")
                for ln, v in pr["by_line"].items():
                    checked += 1
                    if not close(jr["by_line"][ln], v):
                        problems.append(f"case {ci} {name} month {pr['month']} line {ln}")
            pu, ju = model.unit_economics(a, sc), js[ci]["ue"][name]
            for f in ("revenue", "fees", "variable", "margin", "cac", "payback", "ltv", "ltv_cac"):
                checked += 1
                if not close(ju[f], pu[f]):
                    problems.append(f"case {ci} {name} unit economics {f}: py {pu[f]} js {ju[f]}")
        for n, js_s in zip(a.get("scale_points") or [100, 1000, 10000], js[ci]["scale"]):
            ps = model.at_scale(a, n)
            for f in ("revenue", "fees", "variable", "fixed", "margin"):
                checked += 1
                if not close(js_s[f], ps[f]):
                    problems.append(f"case {ci} scale {n} {f}: py {ps[f]} js {js_s[f]}")

    if problems:
        print(f"FAIL: {len(problems)} mismatch(es) out of {checked} values")
        for p in problems[:25]:
            print("  " + p)
        return 1
    print(f"PASS: JavaScript and Python models agree on all {checked} values "
          f"across {len(cases)} input files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
