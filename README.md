# Venture blueprint

A Claude skill that plans a software product or company — from one idea, or from none — through brainstorm, plan and build, and shows you the result as an interactive site you can click through.

Say "make me millions" and it goes looking for problems people already pay to avoid. Give it an idea and it lays out two or three genuinely different ways to build it — each with its own numbers and app screens — so you can choose. Then it plans the chosen path the way a full founding team would: market, competitors, personas, projections in good and bad years, every department from sales to security, legal and app-store traps, design, growth, payments, and the cheapest experiments to test it before building. Only when you ask does it produce a build roadmap a fleet of Claude sessions can execute overnight.

It is a method, not a template. Every claim carries a source and a date or is flagged as unverified, every number comes from a calculator rather than mental arithmetic, and a checker refuses a plan that skips the hard parts.

**New to this? [INSTALL.md](INSTALL.md) walks through it in plain language.**

See a finished example first: [examples/toolshare-demo](examples/toolshare-demo) — download `venture.html` and open it.

## Install

**Claude Code, as a plugin** — recommended; you get updates. Type these in Claude Code, one at a time:

```
/plugin marketplace add natyget/venture-blueprint
```

```
/plugin install venture-blueprint@naty-skills
```

**Claude Code, by cloning.** Clone the repo and open Claude Code inside the folder — the skill is linked at `.claude/skills/` so it loads straight away. Plans you make there go in `ventures/`, which git ignores.

```bash
git clone https://github.com/natyget/venture-blueprint.git
cd venture-blueprint
claude
```

To have it in every project instead, link it into your personal skills:

```bash
ln -s "$PWD/plugins/venture-blueprint/skills/venture-blueprint" ~/.claude/skills/venture-blueprint
```

**Claude app.** Upload `dist/venture-blueprint.skill` in Settings → Capabilities → Skills.

## Use

Just describe what you want. The skill switches itself on for planning requests, so there's no command to remember. To call it explicitly, type `/venture` and pick it from the menu — it's `/venture-blueprint` when installed as a skill, or `/venture-blueprint:venture-blueprint` as a plugin.

- "I want to test an idea for market fit: an app where neighbours lend each other tools."
- "Make me millions."
- "Here's my product. What's missing?"

It works in three stages and **stops between them**:

1. **Explore.** A batch of questions about you and your preferences, a short research pass, then two or three paths side by side — each with rough numbers and a few app screens — and a recommendation. A brainstorm can end here.
2. **Plan.** The path you picked, in depth: a business plan with vision, mission, personas, competitor matrix, projections and a statement of work; every department's plan; the experiments to run first; the full clickable prototype.
3. **Build.** Only when you ask: the step-by-step roadmap and the briefs for parallel build sessions.

## The venture site

At the end of each stage you get `plan/venture.html` — one page that opens in any browser, with nothing to install and nothing sent anywhere:

- **Overview** — the verdict at a glance, the key numbers as tiles, three futures (bad, expected, great) and the app.
- **Product** — a clickable prototype in an iPhone, Android or browser frame. Tap through it, or play a flow step by step.
- **Numbers** — drag sliders for customers, churn, prices, costs and cash and watch every chart move; good and bad years as bars; which assumption the result depends on most; how cost and revenue scale.
- **Paths** — the options side by side, each with its verdict.
- **Plan, Company, Validation** — the documents, readable.
- **Gaps** — everything unverified, unanswered or worrying, by severity.

The page runs the same model as the Python scripts and checks itself against them when it opens.

## What you get

```
plan/
├── venture.html             the site — open this first
├── business-plan.md         the readable whole
├── paths/                   each path's assumptions, projections and screens
├── paths.md                 the options and your preferences
├── screens.json             the chosen product's clickable prototype
├── departments.md           sixteen departments, each planned from its head's view
├── validation.md            the riskiest assumptions and how to test them cheaply
├── 00-brief.md … 10-red-team.md   the phase documents behind it all
├── assumptions.json         every input to the numbers, each with a source
├── financials.md / .csv     projections, never hand-computed
├── traps.csv                24 fixed questions about rules that can sink you
├── compliance.csv, decisions.json
└── roadmap.json, briefs/    only after the build stage
```

## The scripts

Standard-library Python only.

```bash
python3 -I scripts/new_plan.py plan --name "Acme"     # scaffold every stage's files
python3 -I scripts/model.py plan                       # assumptions -> projections
python3 -I scripts/build_site.py plan                  # the venture site
python3 -I scripts/check_plan.py plan --stage plan     # check the plan for that stage
python3 -I scripts/parallel_brief.py plan --out plan/briefs
```

`check_plan.py` checks only what the current stage should have produced. It fails on unanswered traps, departments left blank, experiments without thresholds, broken prototype links, unsourced assumptions, financials stale against their inputs, untestable build steps, and two parallel sessions claiming one file.

For contributors: `python3 -I tests/test_model_parity.py` checks the site's JavaScript model against `model.py`, value by value (needs Node).

## Not legal, tax or investment advice

The compliance work produces a register for a licensed attorney to review, and the skill says so in its own output.

## Licence

MIT.
