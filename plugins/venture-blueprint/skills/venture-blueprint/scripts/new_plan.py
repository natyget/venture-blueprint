#!/usr/bin/env python3
"""Scaffold a venture-blueprint plan directory.

Writes the eleven phase documents with their required sections, plus the three
machine-readable artifacts. Every section carries a TODO marker, so
check_plan.py fails on a fresh scaffold and tells you exactly what is unfilled.
That is the intended behaviour — the validator is a worklist before it is a gate.

Usage:  python3 -I scripts/new_plan.py <plan-dir> --name "<venture>"
        python3 -I scripts/new_plan.py <plan-dir> --name "<venture>" --force
"""

import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path

DOCS = [
    ("00-brief.md", "The brief", [
        ("The operator", "Who is building this, what they already own, and what they can reach that a stranger cannot."),
        ("Cash, time and risk", "Runway in months, hours per week, whether this must pay for itself, outside money or not."),
        ("Where the customers and the company are", "Jurisdictions, which decide the compliance register and the payment rails."),
        ("Platforms", "iOS, Android, web, desktop, API."),
        ("What success means", "Revenue, enterprise value or take-home, and the number."),
        ("Assumptions made in place of answers", "Anything the brief did not settle, so it can be corrected cheaply."),
    ]),
    ("paths.md", "Paths", [
        ("The brief in one paragraph", "Who the operator is, cash and time, where, platforms, what success means. Assumptions marked."),
        ("Founder preferences", "Speed or size, who pays, how they like to sell, capital, involvement, geography, platform taste, hard nos, products they admire. See references/00-paths.md section 1."),
        ("Paths compared", "Two or three paths that differ in who pays, the wedge, the model or the channel. Same rows for every path — references/00-paths.md section 4."),
        ("Recommendation", "Which path or mix, and the one or two reasons that decide it. Where a path conflicts with a stated preference, say so."),
        ("What would change the recommendation", "The fact that, if it turned out differently, would make you recommend another path. Once the founder answers, record their decision as described in references/00-paths.md section 5."),
    ]),
    ("01-wedge.md", "Wedge and competition", [
        ("What the re-read changed", "The assumptions that turned out wrong once you read the real sources. If this is empty, you have not looked hard enough yet."),
        ("Candidates", "Only when the brief had no idea: the scored table, with sources."),
        ("Falsification pass", "Does it exist, has it died before, why doesn't the incumbent do it, what has to be true, who loses."),
        ("Competitor teardown", "3+ competitors with price, acquisition channel, top complaints quoted, and structural weakness. Cite every cell."),
        ("The gap map", "Where the field is empty, and whether that is because it is hard, small, or unreached."),
        ("The wedge", "For <narrow who>, we do <the one job> so much better that they switch, because <structural reason the incumbent cannot follow>."),
        ("The expansion", "What the wedge earns that you cannot buy, and the next two adjacent jobs."),
        ("The first fifty", "Named, not channels."),
        ("Assumptions ranked by what breaks if wrong", ""),
        ("The strongest case against", ""),
    ]),
    ("02-economics.md", "Economics", [
        ("What the re-read changed", ""),
        ("Bottom-up sizing", "The chain from a countable universe to year-one revenue, one multiplier per line, each sourced."),
        ("The ceiling", "If this wedge worked perfectly, what is the revenue?"),
        ("Unit economics", "The unit, revenue, gross margin, retention, LTV, CAC per channel, payback — with a sensitivity row at half conversion, double CAC, 1.5x churn."),
        ("Cost base", "Fixed monthly costs, then totals at 1k / 100k / 1M users, with cliffs flagged."),
        ("The bootstrap test", "Cash to first dollar, time to first dollar, months to cover the cost base, whether it fits runway, and which fix you took."),
        ("Pricing band", "Floor, reference price, value basis, ceiling."),
    ]),
    ("03-compliance.md", "Compliance and platform policy", [
        ("This is not legal advice", "State plainly that a licensed attorney in the jurisdiction must review before launch, and name the roadmap step that schedules it."),
        ("What the re-read changed", ""),
        ("The register", "See compliance.csv. Summarise here what applies and what is designed away."),
        ("Obligations designed away", "Don't collect it, don't hold it, keep it on the device, take the signal not the proof."),
        ("Evidence artifacts", "What must exist before launch to prove each obligation is met."),
        ("Store review notes", "Drafted now, so a reviewer cannot misread the product."),
        ("Rows needing a lawyer", ""),
    ]),
    ("04-architecture.md", "Architecture", [
        ("What the re-read changed", ""),
        ("Layer decisions", "Each layer: chosen, rejected alternatives with reasons, what it costs us, and when to revisit. Also in decisions.json."),
        ("The native rule", "Where native won, and where it did not, with what the exception buys and costs."),
        ("Budgets", "Dependency, bundle, performance, query, cost and build budgets — each with the CI check that enforces it."),
        ("Cost and behaviour at scale", "1k / 100k / 1M, with what breaks first at each and the accepted ceiling."),
        ("Data model", "Core entities, plus the hard-to-change decisions: identity, tenancy, money, time, enums, ids."),
        ("The shared contract", "The one artifact every consumer imports, and the drift test in each."),
        ("Failure modes", "Per dependency: what happens when it is down or slow, and what the user sees."),
        ("Security floor", "Secrets, authorization at the data layer, rate limits, signed tokens, encryption, tested backups, audit log."),
    ]),
    ("05-design-language.md", "Design language", [
        ("References and what mechanism each gave", "15-25 screens, each with the mechanism taken, not the skin."),
        ("The language", "Three or four sentences a designer and a developer would act on identically."),
        ("The anti-list", "What this product never does."),
        ("Tokens", "Colour with contrast results, type, space, radius, elevation, motion, icons — and the lint rule that forbids hardcoded values."),
        ("Component inventory", "Every component with its states, including focus, loading, empty, error and long content."),
        ("Screen states", "First-run empty, empty-after-filter, offline, slow, permission denied, signed out, server error, deleted-while-viewing."),
        ("Asset pipeline", "Every generated output: icon sizes, store screenshots per device class, link previews per page type, favicons, email and push assets — plus the coverage check that fails on a missing or fallback image."),
        ("Accessibility decisions", "Contrast, dynamic type, touch targets, focus, labels, reduced motion."),
    ]),
    ("06-growth.md", "Growth and measurement", [
        ("The chosen channel", "And why it fits this product's shape; the others as later bets."),
        ("Page-type matrix", "URL pattern, intent, page count, content source, title and description patterns, schema type, internal links, conversion action, thin-page threshold."),
        ("App store optimization", "Keywords, screenshots as narrative, custom product pages, campaign token format, deferred deep link behaviour per platform."),
        ("The loop", "Written as steps with a number on each, k computed, and the factor you would improve first."),
        ("The measurement contract", "The one event list: every event, who sends it, when, parameters. Plus conventions, screen and page names, internal traffic marking."),
        ("The funnel script", "Numbered steps from first touch to the core action, with the expected event and parameter values at each."),
        ("Baselines and pre-written decision branches", "What to measure before the change, and what you will do for each outcome."),
        ("Launch sequence", ""),
    ]),
    ("07-monetization.md", "Monetization", [
        ("The model", "With its unit, and why that unit matches how the customer gets value."),
        ("Free tier", "Exact limits and what it costs you."),
        ("Price list", ""),
        ("The store-policy line", "What must use in-app purchase and what may not, with a dated citation, plus what changes if the rule moves."),
        ("Rails by corridor", "Per corridor: who may sign up, KYC and how long it really takes, settlement currency, payout timing, fees including FX, dispute semantics, sandbox, whether an aggregator covers it. Then the launch order."),
        ("Entity and KYC lead times", "The human steps that block everything downstream."),
        ("Taxes and payouts", "Sales tax and VAT, marketplace facilitator, payout schedule, failed-KYC sellers, reporting."),
        ("Refunds, disputes and dunning", ""),
    ]),
    ("08-ecosystem.md", "Ecosystem and in-house tools", [
        ("The value chain", "Every step from problem to money, who owns it today, what it costs, where value leaks."),
        ("Does the loop close?", "Does the output of the last step feed the first?"),
        ("Absorb, build or rent", "Per step, with the reason and the crossover month."),
        ("The operator console", "Launch / scale / rented, per tool."),
        ("Moderation", "Report paths, queue, actions, appeals, audit trail, illegal-content pipeline."),
        ("Runbooks", "One per failure mode from Phase 4."),
    ]),
    ("09-roadmap.md", "Roadmap", [
        ("Workstreams and deploy order", "With contracts marked as the blocking prerequisite."),
        ("Steps", "Every step in the full format. Also in roadmap.json."),
        ("The cut line", "Must ship / should ship / can follow, with the binary-only steps named."),
        ("Gates", "Each a command, query or observation with a pass criterion."),
        ("Rollback", "Per surface, plus the list of what cannot be undone."),
        ("Human steps", "With lead times, and what each blocks."),
        ("The parallel split", "One workstream per session, disjoint file ownership, and the critical-path estimate."),
    ]),
    ("10-red-team.md", "Red team", [
        ("The four hostile readers", "Competitor, investor looking to pass, regulator, and the user who wants to hurt someone."),
        ("Abuse surface and externalities", "With a step for each, not a note."),
        ("Boundary conditions", "Zero state, one, many, long names, timezones, offline, duplicate submits, deleted accounts, supplier outages."),
        ("Concentration risk", "One platform, channel, supplier, customer, person."),
        ("Kill scenarios", "Dies in six months, dies at scale, succeeds and is competed away — each with its leading indicator."),
        ("What I did not verify", "Every UNVERIFIED claim and who can settle it, what you could not test and who must, the three decisions you most want challenged, and what is out of scope."),
    ]),
    ("business-plan.md", "Business plan", [
        ("Executive summary", "One page, written last. Problem, product, why now, why you, how it makes money, base-case numbers from financials.md, what happens next."),
        ("Concept", "One paragraph a stranger understands on first read."),
        ("Vision", "What is true in five to ten years if this works. Concrete enough to be wrong."),
        ("Mission", "What you do, for whom, and how. It should rule things out."),
        ("Principles", "Three to six commitments you would keep even when they cost you."),
        ("Problem and evidence", "Pain in customers' own words, quoted, sourced and dated. Why now."),
        ("Customer personas", "Two to four, built from evidence, each changing a decision. See references/business-plan.md section 5."),
        ("Anti-persona", "Who you deliberately do not serve, and why."),
        ("Market", "Bottom-up sizing from 02-economics.md; why now; the ceiling."),
        ("Competitor matrix", "One table read across: competitors including do-nothing, attributes that decide the purchase, cost at a typical volume, sourced and dated. Then the positioning map."),
        ("Paths considered", "The options from paths.md, the one taken and why."),
        ("Product", "MVP in and out of scope, the core loop, what makes it defensible, the expansion."),
        ("Business model and pricing", "Model, unit, prices, free tier, rails and their order, the store-policy line per revenue line."),
        ("Financials", "From financials.md only: scenarios, how cost and revenue scale, break-even and cash low point, unit economics, drivers, assumptions."),
        ("Go-to-market", "The first fifty customers, the channel that scales, the loop and its arithmetic, launch sequence."),
        ("Organization", "From departments.md: who does what at launch, the hiring sequence and triggers, the team's monthly cost by stage."),
        ("Compliance and risk", "Obligations and how each is met or designed away, trap findings, rows for a lawyer, kill scenarios. Not legal advice."),
        ("Statement of work", "Scope in and out, deliverables with acceptance criteria, milestones, roles, dependencies and lead times, budget, assumptions, change control."),
        ("Milestones and metrics", "Per company stage, the falsifiable target that means move on."),
        ("Long-term path", "The expansion sequence, the moat at each stage, and how this ends — and what that implies now."),
        ("What is unverified and what is next", "Every UNVERIFIED claim and who can settle it, the decisions most worth challenging, the next action."),
        ("Appendix", "Links to the phase documents and data files."),
    ]),
]


def doc_body(title, sections, name, today):
    out = [f"# {title} — {name}", "",
           f"_Phase document. Last updated {today}._", ""]
    for heading, hint in sections:
        out.append(f"## {heading}")
        out.append("")
        if hint:
            out.append(f"<!-- {hint} -->")
            out.append("")
        out.append("TODO: fill this in.")
        out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan_dir")
    ap.add_argument("--name", required=True, help="the venture's name")
    ap.add_argument("--force", action="store_true",
                    help="overwrite existing files")
    args = ap.parse_args()

    plan = Path(args.plan_dir)
    today = dt.date.today().isoformat()
    plan.mkdir(parents=True, exist_ok=True)

    written, skipped = [], []
    for filename, title, sections in DOCS:
        path = plan / filename
        if path.exists() and not args.force:
            skipped.append(filename)
            continue
        path.write_text(doc_body(title, sections, args.name, today),
                        encoding="utf-8")
        written.append(filename)

    artifacts = {
        "decisions.json": {
            "venture": args.name,
            "updated": today,
            "decisions": [],
        },
        "roadmap.json": {
            "venture": args.name,
            "updated": today,
            "workstreams": [
                {"id": "contracts", "branch": "build/contracts",
                 "blocking": True, "paths": []},
                {"id": "human", "branch": None, "blocking": False},
            ],
            "steps": [],
            "gates": [],
            "cannot_undo": [],
        },
    }
    for filename, payload in artifacts.items():
        path = plan / filename
        if path.exists() and not args.force:
            skipped.append(filename)
            continue
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        written.append(filename)

    csv_path = plan / "compliance.csv"
    if csv_path.exists() and not args.force:
        skipped.append("compliance.csv")
    else:
        csv_path.write_text(
            "feature,regime,requirement,posture,approach,step,evidence,"
            "source,verified,counsel\n", encoding="utf-8")
        written.append("compliance.csv")

    assumptions_path = plan / "assumptions.json"
    if assumptions_path.exists() and not args.force:
        skipped.append("assumptions.json")
    else:
        example = Path(__file__).resolve().parent.parent / "templates" / "assumptions.example.json"
        try:
            seeded = json.loads(example.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"  warning: could not read {example}: {exc}")
            seeded = {}

        def blank_sources(node):
            if isinstance(node, dict):
                for key in list(node):
                    if key == "source":
                        node[key] = "TODO: give a source, or say UNVERIFIED and why"
                    elif key == "verified":
                        node.pop(key)
                    else:
                        blank_sources(node[key])
            elif isinstance(node, list):
                for item in node:
                    blank_sources(item)

        blank_sources(seeded)
        seeded = {"_note": "Seeded from the worked example in templates/. Replace every "
                           "number and every source with this venture's own, then run "
                           "scripts/model.py.", **seeded, "venture": args.name}
        assumptions_path.write_text(json.dumps(seeded, indent=2) + "\n", encoding="utf-8")
        written.append("assumptions.json")

    traps_path = plan / "traps.csv"
    if traps_path.exists() and not args.force:
        skipped.append("traps.csv")
    else:
        canon = Path(__file__).resolve().parent.parent / "templates" / "traps.json"
        with traps_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["id", "category", "question", "status", "answer",
                             "source", "verified", "step"])
            try:
                traps = json.loads(canon.read_text(encoding="utf-8"))["traps"]
            except (OSError, json.JSONDecodeError, KeyError) as exc:
                print(f"  warning: could not read {canon}: {exc}")
                traps = []
            for trap in traps:
                writer.writerow([trap["id"], trap["category"], trap["question"],
                                 "", "", "", "", ""])
        written.append("traps.csv")

    (plan / "paths").mkdir(exist_ok=True)

    dept_path = plan / "departments.md"
    if dept_path.exists() and not args.force:
        skipped.append("departments.md")
    else:
        roster = Path(__file__).resolve().parent.parent / "templates" / "departments.json"
        try:
            depts = json.loads(roster.read_text(encoding="utf-8"))["departments"]
        except (OSError, json.JSONDecodeError, KeyError) as exc:
            print(f"  warning: could not read {roster}: {exc}")
            depts = []
        out = [f"# Departments — {args.name}", "", f"_Phase document. Last updated {today}._", "",
               "<!-- Take the seat of each department's head two stages from now: what do they wish "
               "had been decided on day one, and what was a waste to set up early? See "
               "references/departments.md. A whole department may be marked Not applicable, with "
               "the reason and the trigger to revisit. -->", ""]
        for d in depts:
            out += [f"## {d['id']} {d['name']}", "",
                    f"<!-- {d['lens']} Ask: " + " / ".join(d["asks"]) + " -->", ""]
            for label in ("What breaks first", "Day one", "Stack", "Who, by stage",
                          "Agents can run", "KPIs"):
                out += [f"**{label}:** TODO: fill this in.", ""]
        out += ["## Cross-functional review", "",
                "<!-- The real tensions between departments in this plan, and how each is resolved. -->",
                "", "TODO: fill this in.", ""]
        dept_path.write_text("\n".join(out), encoding="utf-8")
        written.append("departments.md")

    val_path = plan / "validation.md"
    if val_path.exists() and not args.force:
        skipped.append("validation.md")
    else:
        val_path.write_text("\n".join([
            f"# Validation — {args.name}", "", f"_Phase document. Last updated {today}._", "",
            "## Riskiest assumptions", "",
            "<!-- From What matters most on the venture site, the paths' what-has-to-be-true, and "
            "the red team. Ranked by how much breaks if wrong times how unsure you are. -->", "",
            "TODO: fill this in.", "",
            "## Experiments", "",
            "<!-- One per assumption: assumption, method, who and how many, cost and time, the "
            "threshold to keep going, the threshold to stop, and what changes either way. Written "
            "before running. -->", "", "TODO: fill this in.", "",
            "## Interview script", "", "TODO: fill this in.", "",
            "## Results log", "",
            "| Date | Experiment | What happened | Numbers | Decision |",
            "|---|---|---|---|---|", ""]), encoding="utf-8")
        written.append("validation.md")

    print(f"Scaffolded {plan} for {args.name!r}")
    if written:
        print(f"  wrote   {len(written)}: {', '.join(written)}")
    if skipped:
        print(f"  kept    {len(skipped)} existing: {', '.join(skipped)}")
    print("\nFill the documents phase by phase. Run check_plan.py at any point "
          "to see what is still unfilled — it fails on a fresh scaffold by design.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
