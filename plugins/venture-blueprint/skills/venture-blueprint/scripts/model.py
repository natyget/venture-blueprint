#!/usr/bin/env python3
"""Turn plan/assumptions.json into cost, revenue and cash projections.

Writes financials.csv (month by month, every scenario) and financials.md
(the summary tables the business plan quotes). The point is that no
projection in a plan is computed by hand: language models make arithmetic
errors that read exactly like correct arithmetic, and a founder will make
decisions on these figures.

Every assumption carries a source. Ones marked UNVERIFIED are listed in the
output; ones with no source at all are reported as problems.

Usage:  python3 -I scripts/model.py <plan-dir>
        python3 -I scripts/model.py <plan-dir> --assumptions other.json
"""

import argparse
import csv
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

KINDS = {
    "subscription": ["price"],
    "per_unit": ["price", "units_per_customer_month"],
    "take_rate": ["rate", "gmv_per_customer_month"],
    "one_time": ["price"],
}
DEFAULT_SCENARIOS = {
    "conservative": {"new_x": 0.6, "growth_x": 0.7, "churn_x": 1.5, "cac_x": 1.4},
    "base": {},
    "optimistic": {"new_x": 1.4, "growth_x": 1.2, "churn_x": 0.75, "cac_x": 0.8},
}
SCENARIO_KEYS = {"new_x", "growth_x", "churn_x", "price_x", "cac_x"}
SUMMARY_MONTHS = [6, 12, 24, 36]


def fail(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def num(block, key, where, default=None, lo=0.0, hi=None):
    val = block.get(key, default)
    if val is None:
        fail(f"{where}: missing {key}")
    if not isinstance(val, (int, float)) or isinstance(val, bool):
        fail(f"{where}: {key} must be a number, got {val!r}")
    if val < lo or (hi is not None and val > hi):
        rng = f"{lo}..{hi}" if hi is not None else f">= {lo}"
        fail(f"{where}: {key} must be {rng}, got {val}")
    return float(val)


def source_state(block):
    """'ok', 'unverified' or 'missing'."""
    src = str(block.get("source") or "").strip()
    if not src or src.upper().startswith("TODO"):
        return "missing"
    if "UNVERIFIED" in src.upper():
        return "unverified"
    return "ok"


def validate(a):
    if not isinstance(a.get("customers"), dict):
        fail("assumptions.json needs a 'customers' object")
    c = a["customers"]
    num(c, "starting", "customers", default=0)
    num(c, "new_first_month", "customers")
    num(c, "new_growth_monthly", "customers", default=0, lo=-0.5, hi=2)
    num(c, "churn_monthly", "customers", hi=1)
    num(c, "cac", "customers", default=0)
    if "new_max_per_month" in c:
        num(c, "new_max_per_month", "customers")

    lines = a.get("revenue_lines") or []
    if not lines:
        fail("assumptions.json needs at least one revenue line")
    for i, line in enumerate(lines):
        where = f"revenue_lines[{i}] ({line.get('name', '?')})"
        kind = line.get("kind")
        if kind not in KINDS:
            fail(f"{where}: kind must be one of {sorted(KINDS)}, got {kind!r}")
        for field in KINDS[kind]:
            num(line, field, where, hi=1 if field == "rate" else None)
        num(line, "attach_rate", where, default=1, hi=1)
        num(line, "store_commission", where, default=0, hi=1)
        num(line, "processing_pct", where, default=0, hi=1)
        num(line, "processing_fixed", where, default=0)

    for i, cost in enumerate(a.get("variable_costs") or []):
        where = f"variable_costs[{i}] ({cost.get('name', '?')})"
        if "per_customer_month" not in cost and "pct_of_revenue" not in cost:
            fail(f"{where}: needs per_customer_month or pct_of_revenue")
        if "per_customer_month" in cost:
            num(cost, "per_customer_month", where)
        if "pct_of_revenue" in cost:
            num(cost, "pct_of_revenue", where, hi=1)

    for i, cost in enumerate(a.get("fixed_costs") or []):
        where = f"fixed_costs[{i}] ({cost.get('name', '?')})"
        num(cost, "monthly", where)
        for j, step in enumerate(cost.get("steps") or []):
            num(step, "at_customers", f"{where}.steps[{j}]")
            num(step, "monthly", f"{where}.steps[{j}]")

    for name, sc in (a.get("scenarios") or {}).items():
        bad = set(sc) - SCENARIO_KEYS
        if bad:
            fail(f"scenario {name!r}: unknown keys {sorted(bad)}; "
                 f"allowed: {sorted(SCENARIO_KEYS)}")
        for k in sc:
            num(sc, k, f"scenario {name!r}", lo=0)


def fixed_at(cost, active, month):
    if month < int(cost.get("start_month", 1)):
        return 0.0
    end = cost.get("end_month")
    if end is not None and month > int(end):
        return 0.0
    monthly = float(cost["monthly"])
    for step in sorted(cost.get("steps") or [], key=lambda s: s["at_customers"]):
        if active >= step["at_customers"]:
            monthly = float(step["monthly"])
    return monthly


def line_revenue(line, active, new, px):
    """Gross revenue, transaction count and paying count for one line."""
    attach = float(line.get("attach_rate", 1))
    kind = line["kind"]
    if kind == "one_time":
        payers = new * attach
        return line["price"] * px * payers, payers, payers
    payers = active * attach
    if kind == "subscription":
        return line["price"] * px * payers, payers, payers
    if kind == "per_unit":
        units = payers * line["units_per_customer_month"]
        return line["price"] * px * units, units, payers
    tx = payers * float(line.get("transactions_per_customer_month", 1))
    return line["rate"] * px * line["gmv_per_customer_month"] * payers, tx, payers


def line_fees(line, gross, tx):
    return (gross * float(line.get("store_commission", 0))
            + gross * float(line.get("processing_pct", 0))
            + tx * float(line.get("processing_fixed", 0)))


def run(a, sc):
    c = a["customers"]
    months = int(a.get("months", 36))
    new_x = sc.get("new_x", 1.0)
    growth_x = sc.get("growth_x", 1.0)
    churn = min(1.0, c["churn_monthly"] * sc.get("churn_x", 1.0))
    px = sc.get("price_x", 1.0)
    cac = c.get("cac", 0) * sc.get("cac_x", 1.0)
    cap = c.get("new_max_per_month")
    growth = c.get("new_growth_monthly", 0) * growth_x

    active = float(c.get("starting", 0))
    cash = float(a.get("starting_cash", 0))
    rows = []
    for m in range(1, months + 1):
        new = c["new_first_month"] * new_x * (1 + growth) ** (m - 1)
        if cap is not None:
            new = min(new, cap)
        churned = active * churn
        active = max(0.0, active + new - churned)

        gross = fees = 0.0
        by_line = {}
        for line in a["revenue_lines"]:
            g, tx, _ = line_revenue(line, active, new, px)
            by_line[line["name"]] = g
            gross += g
            fees += line_fees(line, g, tx)

        variable = 0.0
        for v in a.get("variable_costs") or []:
            variable += float(v.get("per_customer_month", 0)) * active
            variable += float(v.get("pct_of_revenue", 0)) * gross

        fixed = sum(fixed_at(f, active, m) for f in a.get("fixed_costs") or [])
        acquisition = new * cac
        margin = gross - fees - variable
        net = margin - fixed - acquisition
        cash += net
        rows.append({
            "month": m, "new": new, "churned": churned, "active": active,
            "gross_revenue": gross, "fees": fees, "variable_costs": variable,
            "gross_margin": margin, "fixed_costs": fixed,
            "acquisition_spend": acquisition, "net": net, "cash": cash,
            "by_line": by_line,
        })
    return rows


def unit_economics(a, sc):
    """Steady-state economics of one customer, independent of scale."""
    c = a["customers"]
    px = sc.get("price_x", 1.0)
    churn = min(1.0, c["churn_monthly"] * sc.get("churn_x", 1.0))
    cac = c.get("cac", 0) * sc.get("cac_x", 1.0)
    gross = fees = 0.0
    for line in a["revenue_lines"]:
        if line["kind"] == "one_time":
            continue
        g, tx, _ = line_revenue(line, 1.0, 0.0, px)
        gross += g
        fees += line_fees(line, g, tx)
    variable = sum(float(v.get("per_customer_month", 0))
                   + float(v.get("pct_of_revenue", 0)) * gross
                   for v in a.get("variable_costs") or [])
    margin = gross - fees - variable
    payback = cac / margin if margin > 0 else None
    ltv = margin / churn if churn > 0 else None
    return {"revenue": gross, "fees": fees, "variable": variable,
            "margin": margin, "cac": cac, "churn": churn, "payback": payback,
            "ltv": ltv, "ltv_cac": (ltv / cac) if (ltv and cac) else None}


def at_scale(a, n):
    ue = unit_economics(a, {})
    revenue = ue["revenue"] * n
    fees = ue["fees"] * n
    variable = ue["variable"] * n
    fixed = sum(fixed_at(f, n, 10 ** 6) if f.get("end_month") is None
                else 0.0 for f in a.get("fixed_costs") or [])
    margin = revenue - fees - variable - fixed
    return {"customers": n, "revenue": revenue, "fees": fees,
            "variable": variable, "fixed": fixed, "margin": margin,
            "margin_pct": (margin / revenue) if revenue else None}


def money(x, cur):
    if x is None:
        return "—"
    sign = "-" if x < 0 else ""
    x = abs(x)
    sym = "$" if cur == "USD" else f"{cur} "
    if x >= 100:
        return f"{sign}{sym}{x:,.0f}"
    return f"{sign}{sym}{x:,.2f}"


def pct(x):
    return "—" if x is None else f"{x * 100:.0f}%"


def count(x):
    return f"{x:,.0f}"


def write_outputs(plan, a, results, src_hash, out_csv, out_md):
    cur = a.get("currency", "USD")
    names = [l["name"] for l in a["revenue_lines"]]

    with out_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["scenario", "month", "new_customers", "churned", "active",
                    *[f"revenue: {n}" for n in names], "gross_revenue",
                    "store_and_processing_fees", "variable_costs",
                    "gross_margin", "fixed_costs", "acquisition_spend",
                    "net", "cash"])
        for name, rows in results.items():
            for r in rows:
                w.writerow([name, r["month"], round(r["new"], 2),
                            round(r["churned"], 2), round(r["active"], 2),
                            *[round(r["by_line"][n], 2) for n in names],
                            *[round(r[k], 2) for k in
                              ("gross_revenue", "fees", "variable_costs",
                               "gross_margin", "fixed_costs",
                               "acquisition_spend", "net", "cash")]])

    months = int(a.get("months", 36))
    points = [m for m in SUMMARY_MONTHS if m <= months] or [months]
    label = a["customers"].get("label", "customers")
    md = [f"# Financial projections — {a.get('venture', plan.name)}", "",
          f"<!-- assumptions-sha256: {src_hash} -->",
          f"_Generated by `scripts/model.py` on {dt.date.today().isoformat()} "
          "from `assumptions.json`. Do not edit by hand: change the assumptions "
          "and rerun, so every figure in the plan stays consistent._", ""]

    md += ["## Scenarios", "",
           "| Scenario | Month | Active " + label + " | Monthly revenue | "
           "Gross margin | Monthly net | Cash |",
           "|---|---|---|---|---|---|---|"]
    for name, rows in results.items():
        for m in points:
            r = rows[m - 1]
            gm = r["gross_margin"] / r["gross_revenue"] if r["gross_revenue"] else None
            md.append(f"| {name} | {m} | {count(r['active'])} | "
                      f"{money(r['gross_revenue'], cur)} | {pct(gm)} | "
                      f"{money(r['net'], cur)} | {money(r['cash'], cur)} |")
    md.append("")

    md += ["## Break-even and cash", "",
           "| Scenario | First month net ≥ 0 | Cash low point | Low point month | "
           "Funding needed beyond starting cash |", "|---|---|---|---|---|"]
    start = float(a.get("starting_cash", 0))
    for name, rows in results.items():
        be = next((r["month"] for r in rows if r["net"] >= 0), None)
        low = min(rows, key=lambda r: r["cash"])
        need = max(0.0, -low["cash"])
        md.append(f"| {name} | {be if be else f'not within {months} months'} | "
                  f"{money(low['cash'], cur)} | {low['month']} | "
                  f"{money(need, cur) if need else 'none'} |")
    md += ["", f"Starting cash: {money(start, cur)}. The cash low point is how much "
           "money the plan actually requires — for a bootstrapped company it is the "
           "number that decides whether the plan is possible.", ""]

    md += ["## Unit economics (per " + label.rstrip("s") + ", per month)", "",
           "| Scenario | Revenue | Fees | Variable cost | Gross margin | CAC | "
           "Payback | LTV | LTV:CAC |", "|---|---|---|---|---|---|---|---|---|"]
    for name in results:
        sc = (a.get("scenarios") or DEFAULT_SCENARIOS).get(name, {})
        ue = unit_economics(a, sc)
        pb = f"{ue['payback']:.1f} mo" if ue["payback"] else "never"
        lc = f"{ue['ltv_cac']:.1f}×" if ue["ltv_cac"] else "—"
        md.append(f"| {name} | {money(ue['revenue'], cur)} | {money(ue['fees'], cur)} | "
                  f"{money(ue['variable'], cur)} | {money(ue['margin'], cur)} | "
                  f"{money(ue['cac'], cur)} | {pb} | {money(ue['ltv'], cur)} | {lc} |")
    md += ["", "LTV uses gross margin, not revenue. One-time revenue lines are "
           "excluded from the recurring per-customer figures.", ""]

    scale_points = a.get("scale_points") or [100, 1000, 10000, 100000]
    md += ["## How cost and revenue scale", "",
           "Steady state at each size, base assumptions, before acquisition spend. "
           "Step costs switch on at their thresholds.", "",
           f"| Active {label} | Monthly revenue | Fees | Variable cost | Fixed cost | "
           "Monthly margin | Margin % |", "|---|---|---|---|---|---|---|"]
    for n in scale_points:
        s = at_scale(a, n)
        md.append(f"| {count(n)} | {money(s['revenue'], cur)} | {money(s['fees'], cur)} | "
                  f"{money(s['variable'], cur)} | {money(s['fixed'], cur)} | "
                  f"{money(s['margin'], cur)} | {pct(s['margin_pct'])} |")
    steps = [(f["name"], s["at_customers"], s["monthly"])
             for f in a.get("fixed_costs") or [] for s in f.get("steps") or []]
    if steps:
        md += ["", "**Cost steps (cliffs):**", ""]
        for nm, at, mo in sorted(steps, key=lambda t: t[1]):
            md.append(f"- {nm} becomes {money(mo, cur)}/month at {count(at)} {label}")
    md.append("")

    base = results.get("base") or next(iter(results.values()))
    md += ["## Revenue mix (base)", "", "| Line | " +
           " | ".join(f"Month {m}" for m in points) + " |",
           "|---" * (len(points) + 1) + "|"]
    for n in names:
        md.append(f"| {n} | " + " | ".join(
            money(base[m - 1]["by_line"][n], cur) for m in points) + " |")
    md.append("")

    md += ["## Assumptions and sources", "",
           "| Assumption | Value | Source |", "|---|---|---|"]
    c = a["customers"]
    md.append(f"| New {label}, month 1 | {c['new_first_month']:g} | {c.get('source', '')} |")
    md.append(f"| Growth in new {label}/month | {pct(c.get('new_growth_monthly', 0))} | {c.get('source', '')} |")
    md.append(f"| Monthly churn | {c['churn_monthly'] * 100:.1f}% | {c.get('source', '')} |")
    md.append(f"| CAC | {money(c.get('cac', 0), cur)} | {c.get('source', '')} |")
    for l in a["revenue_lines"]:
        val = (money(l.get("price"), cur) if "price" in l
               else f"{l['rate'] * 100:.1f}% of {money(l['gmv_per_customer_month'], cur)}")
        if l["kind"] == "per_unit":
            val += f" × {l['units_per_customer_month']:g}/mo"
        if l.get("attach_rate", 1) != 1:
            val += f", {pct(l['attach_rate'])} attach"
        if l.get("store_commission"):
            val += f", {pct(l['store_commission'])} store"
        md.append(f"| {l['name']} ({l['kind']}) | {val} | {l.get('source', '')} |")
    for v in a.get("variable_costs") or []:
        val = (money(v["per_customer_month"], cur) + "/customer/mo"
               if "per_customer_month" in v else f"{pct(v['pct_of_revenue'])} of revenue")
        md.append(f"| {v['name']} | {val} | {v.get('source', '')} |")
    for f in a.get("fixed_costs") or []:
        md.append(f"| {f['name']} | {money(f['monthly'], cur)}/mo | {f.get('source', '')} |")
    md.append("")

    unverified, missing = [], []
    for nm, blk in ([("customers", a["customers"])]
                    + [(l["name"], l) for l in a["revenue_lines"]]
                    + [(v["name"], v) for v in a.get("variable_costs") or []]
                    + [(f["name"], f) for f in a.get("fixed_costs") or []]):
        st = source_state(blk)
        if st == "unverified":
            unverified.append(nm)
        elif st == "missing":
            missing.append(nm)
    if unverified or missing:
        md += ["## Not yet verified", ""]
        md += [f"- **{n}** — marked UNVERIFIED" for n in unverified]
        md += [f"- **{n}** — no source" for n in missing]
        md.append("")

    md += ["## Method", "",
           "New customers grow at a compounding monthly rate from month 1, capped "
           "where a cap is set. Churn applies to the active base each month. "
           "Recurring revenue is earned on the active base at month end; one-time "
           "revenue on that month's new customers. Fees are store commission plus "
           "payment processing per line. Gross margin is revenue minus fees and "
           "variable costs; net subtracts fixed costs and acquisition spend. "
           "Scenarios scale new-customer volume, growth, churn, price and CAC.", ""]
    out_md.write_text("\n".join(md), encoding="utf-8")
    return unverified, missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan_dir")
    ap.add_argument("--assumptions", help="default: <plan-dir>/assumptions.json")
    args = ap.parse_args()

    plan = Path(args.plan_dir)
    src = Path(args.assumptions) if args.assumptions else plan / "assumptions.json"
    if not src.exists():
        fail(f"{src} not found — copy templates/assumptions.example.json and edit it")
    raw = src.read_bytes()
    try:
        a = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"{src} is not valid JSON: {exc}")
    validate(a)

    scenarios = a.get("scenarios") or DEFAULT_SCENARIOS
    results = {name: run(a, sc) for name, sc in scenarios.items()}
    if args.assumptions and src.resolve() != (plan / "assumptions.json").resolve():
        # A path file from Stage 1: write its results beside it, not over the plan's.
        out_csv = src.with_name(f"{src.stem}-financials.csv")
        out_md = src.with_name(f"{src.stem}-financials.md")
    else:
        out_csv, out_md = plan / "financials.csv", plan / "financials.md"
    unverified, missing = write_outputs(plan, a, results,
                                        hashlib.sha256(raw).hexdigest()[:16],
                                        out_csv, out_md)

    cur = a.get("currency", "USD")
    print(f"Wrote {out_md} and {out_csv}\n")
    for name, rows in results.items():
        be = next((r["month"] for r in rows if r["net"] >= 0), None)
        low = min(rows, key=lambda r: r["cash"])
        last = rows[-1]
        print(f"  {name:<13} break-even: {('month ' + str(be)) if be else 'not reached':<14}"
              f" cash low: {money(low['cash'], cur):>11} (month {low['month']})"
              f"   month {last['month']}: {count(last['active'])} active, "
              f"{money(last['gross_revenue'], cur)}/mo")
    if unverified:
        print(f"\n  {len(unverified)} assumption(s) marked UNVERIFIED: {', '.join(unverified)}")
    if missing:
        print(f"\n  {len(missing)} assumption(s) with NO SOURCE: {', '.join(missing)}")
        print("  check_plan.py --stage plan will fail until each has a source "
              "or an explicit UNVERIFIED marker.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
