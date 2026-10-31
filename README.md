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

At the end of each stage you get `plan/venture.html` — one page in a window, with nothing to install and nothing sent anywhere. It tells the case two ways:

- **Map.** Your idea sits in the centre with the verdict under it; each beat of the case branches out around it, numbered in reading order, with its key number beside it. Moss grows along each branch: green where it's backed by sources, yellow where it's partly backed, grey where it's still a guess, red where it's a risk. You see at a glance what's solid and what's missing. Click any branch for its point, its number, its X → Y → Z and its sources.
- **Story.** The same beats as a presentation, in the order investors expect: one sentence headline that states the point, one big number, the chain behind it, at most three points, the one visual that proves it — a chart, the product, a comparison — and the sources underneath. Arrow keys move through it.

The product appears as polished imagery — three phones or a browser window in the product's own colours — not as a demo. Charts run the same model as the Python scripts and check themselves against it, and numbers in the headlines are filled in from the model, so the words can never disagree with the projections.

The full documents — business plan, paths, departments, validation — are one click away under **Documents**.

## What you get

```
plan/
├── venture.html             the site — open this first
├── business-plan.md         the readable whole
├── paths/                   each path's assumptions, projections and screens
├── paths.md                 the options and your preferences
├── story.json               the case, beat by beat — what the site tells
├── screens.json             the product's screens, shown as imagery
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
