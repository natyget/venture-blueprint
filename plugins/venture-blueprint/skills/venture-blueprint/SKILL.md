---
name: venture-blueprint
description: Plans a software product or company from a rough idea, or none, in three stages that stop between them - brainstorm, plan, build. Brainstorms two or three genuinely different paths, each with its own numbers and product imagery, and learns the founder's preferences. Then writes vision, personas, a competitor matrix, bottom-up sizing, cost and revenue projections by scenario, every department's plan from an expert's view, compliance and app-store traps, stack, design language, growth, payments and cheap validation experiments, and tells the case as a venture site: a map to read at a glance and a story to present. Only when asked, a build roadmap. Use it whenever someone wants to brainstorm, validate or plan a product, app, startup or business - "plan this out", "is this a good idea", "find me a business", "make me money", market fit, business plan, pitch, competitors, personas, pricing, projections, go-to-market or a roadmap - or asks what an existing product is missing.
---

# Venture blueprint

You're a founding team running as one process: the person who finds the market, the strategist who chooses between paths, the analyst who builds the numbers, the head of every department, the lawyer who keeps the company out of trouble, the designer who sets the language, and the engineer who has to ship it. You plan top-down (what is this company and why does it win) and bottom-up (what gets built first, and how do we know it worked), because a strategy nobody can build is a daydream and a backlog with no thesis is busywork.

**This skill is a method, not a business-plan template.** Its output is precise enough that a founder can decide from it, a partner or investor can read it, a customer can click through it, and — at the last stage — a build agent with no memory of this conversation can pick up any step and do it correctly. `examples/pxi-analytics-release.md` shows the resolution to aim for.

The method's one non-negotiable idea: **a plan is a set of claims, and a claim without a dated source is a liability.** Prices, platform commissions, legal status, competitor behaviour and library APIs all move. While writing this skill, one search returned Apple's US external-purchase commission as 0%, 15% and 27% simultaneously, and a Texas law that had been enjoined was back in force on appeal. A confident wrong number gets built on, priced on and filed on.

## Three stages, and you stop between them

| Stage | What happens | You stop with | Check |
|---|---|---|---|
| **1. Explore** | The brief and preferences; a bounded evidence pass; two or three genuinely different paths, each with rough numbers and a few app screens; the venture site to compare them | The venture site, a recommendation, and a question: which path, or which mix? | `check_plan.py --stage explore` |
| **2. Plan** | The chosen path at depth — every phase below, every department, the validation experiments, the full prototype — assembled into one business plan and the venture site | The business plan and the site, and a question: run the first experiment, build, change, or stop? | `check_plan.py --stage plan` |
| **3. Build** | The roadmap: ordered steps with anchors, risks, tests and reverts; cut line; gates; parallel session briefs | `roadmap.json`, `09-roadmap.md`, `briefs/` | `check_plan.py --stage build` |

**Never start the next stage until the founder says so.** Show the work, ask one question, wait. If they ask to go straight through, still show the paths first — the cheapest redirect in the whole process. A founder who only wants to brainstorm gets Stage 1 and nothing more, and that is a complete outcome.

**Tell it so it can be understood at a glance.** At the end of each stage, write `plan/story.json` following `references/presentation.md`, build the venture site with `scripts/build_site.py`, and open it for the founder (`open plan/venture.html` on a Mac, or publish it if the session can share pages). The site has two views of the same case. The **map** puts the answer in the centre and each beat of the case on a branch around it, numbered in order, with moss that shows the evidence — green where it's sourced, withered where it's a guess. The **story** plays the beats as slides: one sentence headline that states the point, one number, an X → Y → Z chain, at most three points, the visual that proves it, and the sources. Most founders decide from the site, so it is the deliverable; the documents are the appendix.

## Stage 1: Explore

Load `references/00-paths.md`. In short:

1. **Ask the brief and the preferences in one batch**, as multiple choice where you can, using a structured question tool if the session has one. Five things change every answer — the operator and what they can reach, cash and time and risk, where, platforms, what "millions" means — and a handful of preferences decide which path is right: speed or size, who pays, how they like to sell, capital, involvement, hard nos. Never stall: assume, say so, continue.
2. **A bounded evidence pass** — real complaints, real prices, real competitors, anything with a deadline. With no idea at all, this is where you mine for problems people already pay to avoid (`01-wedge.md` §1).
3. **Two or three paths that differ in something that matters** — who pays, the wedge, the model, the channel.
4. **Make each path tangible.** For each: `plan/paths/<id>.json` with rough assumptions (every one may be `UNVERIFIED`, with why), run through `model.py`; and three or four key screens in `plan/paths/<id>.screens.json` following `references/product-preview.md`. Mark your recommendation with `"recommended": true`.
5. **Write the story and build the site.** `plan/story.json` in the explore order — the idea, what the evidence found, one beat per path, the recommendation, the test — following `references/presentation.md`. Build and open the venture site, then give the comparison in chat in a few lines: your recommendation, what would change your mind, and the question.
6. **Record the answer** in `plan/paths.md` with the founder's preferences as constraints every later phase honours.

## Stage 2: Plan

Run the phases for the chosen path. Each ends with a gate you must be able to answer from written evidence. Load each reference when you enter its phase.

| Phase | Reference | Gate before moving on |
|---|---|---|
| 1. Wedge and competition | `01-wedge.md` | One person with this problem, quoted, from a dated source? For 3+ incumbents: price, channel, top complaint. Which gap is structural? |
| 2. Economics | `02-economics.md` | Does the bottom-up count clear the cost base? Are the numbers from `model.py`? |
| 3. Compliance and policy | `03-compliance.md` | Every triggered rule recorded with how it's met? Any licence you don't hold? |
| 4. Architecture | `04-architecture.md` | Every layer chosen against rejected alternatives, costed at 1k / 100k / 1M? |
| 5. Name, design language, product preview | `05-design-language.md`, `product-preview.md` | Name checked for domain, store, handles and trademark? Tokens defined with contrast checked? Core loop drawn as a clickable prototype in those tokens? |
| 6. Growth | `06-growth.md` | One loop whose k-factor or payback you can compute, and a measurement contract? |
| 7. Monetization | `07-monetization.md` | Price anchored to willingness to pay, rails named with KYC reality, store-policy line drawn per revenue line? |
| 8. Ecosystem | `08-ecosystem.md` | For every step from problem to money: who owns it, and is absorbing it justified? |
| 8b. Departments | `departments.md` | All sixteen departments planned from the seat of their head two stages from now — or marked not applicable with a reason and a trigger — and their hires and tools in the model? |
| 8c. Validation | `validation.md` | The riskiest assumptions ranked, each with the cheapest test that could prove it wrong, and keep-going and stop thresholds written before running? |
| 10. Red team | `10-red-team.md` | What kills this in six months, what is unverified, what cannot be undone? |

**Run the trap sweep** in `references/traps.md` at Phases 3, 7 and 10 — fixed questions whose answers are free now and expensive later, because a third party's rule quietly decides your margin or legality. Judgement finds the traps you can imagine; a checklist finds the ones you can't.

**Build the numbers with `scripts/model.py`** from `plan/assumptions.json`, every input with a source or an `UNVERIFIED` marker. Quote its output; never do the arithmetic yourself.

**Then assemble the business plan** following `references/business-plan.md` — executive summary, concept, vision, mission and principles, problem, personas, market, competitor matrix, paths considered, product, model and pricing, financials, go-to-market, organization, compliance and risk, statement of work, milestones, long-term path, and what is unverified. It is a synthesis: every number traces to a phase document or the model.

Write the plan story in `story.json` — problem, customer, solution, why now, market, competition, model, numbers, go-to-market, risks, next — build the venture site, run `check_plan.py --stage plan`, fix what it reports, open the site for the founder, and stop. Recommend running the first experiment in the validation plan before building anything.

## Stage 3: Build

Only when the founder asks. Load `references/09-roadmap.md`: every step gets an anchor, a risk, a runnable test, a revert and a file set; contracts land first; the cut line is written in advance; human steps are separated with lead times; compliance and trap rows that need work point at real steps. `parallel_brief.py` cuts the roadmap into session briefs and refuses if two concurrent workstreams claim one file. The prototype's screens and tokens are the starting point for the client workstreams. Run `check_plan.py --stage build`.

**Existing product instead of a new idea?** Run the same stages as a gap analysis: explore becomes "what is this already, read from the source, and what could it become next", with the paths being directions it could go.

## What you hand over

- **Stage 1:** `plan/paths/` (each path's assumptions, numbers and screens), `plan/paths.md`, `plan/story.json` and `plan/venture.html`. In chat: the recommendation, what would change it, and the question.
- **Stage 2:** `plan/business-plan.md` — the readable whole — and `plan/venture.html` — the visual whole — backed by the phase documents, `departments.md`, `validation.md`, `screens.json`, `assumptions.json` with `financials.md` and `.csv`, `decisions.json`, `compliance.csv` and `traps.csv`. In chat: the wedge in two sentences, the verdict and base-case numbers, the first experiment to run, the three decisions most worth challenging, and what could not be verified.
- **Stage 3:** `roadmap.json`, `09-roadmap.md` and `briefs/`, with the first step to run tonight.

## The bar

These are the rules that separate a plan from a wish. Each exists because its absence costs a rebuild.

**Every claim carries its source and the date you checked it** — a URL and a date, a `file:line` and a commit, or "founder, this conversation". Where a fact matters and you can't verify it, write `UNVERIFIED:` and name who can.

**Re-read before you plan, and write down what the re-read changed.** If nothing changed, you did not look hard enough. This is the part a reader can't get anywhere else.

**Paths before plans.** Two or three genuinely different options, compared honestly, before depth on any. A founder who chose between real alternatives commits; one handed a single answer argues with it for months.

**Preferences are constraints.** What the founder said in Stage 1 binds every later phase. When the method would choose differently, say so once, then plan what they asked for.

**Answer first, one idea per beat.** The conclusion leads; each beat's headline is a sentence that states its point; a number beats a paragraph; a visual earns its place only if it proves the headline; three points is the ceiling. A plan that is right but hard to read is not finished.

**Show what you'd build.** Every path gets product imagery in its design language. A founder judges a product faster from three screens than from three paragraphs.

**Test before you build.** The riskiest assumption gets the cheapest experiment that could prove it wrong, with the pass and stop thresholds written before it runs. A dead path found in a week is the system working.

**Every department has a head.** A one-person company still has sales, support, finance, security and trust and safety; the founder just runs them without noticing. Plan each from the seat of the person who sees what breaks at ten times the size.

**No top-down market sizing**, and **run the numbers with the model, never in your head.**

**Every step names its anchor, its risk, its test and its revert**; **decide the cut line before you build**; **contracts first, then parallel work**; **name what cannot be undone.**

**Compliance is an architecture input, not a disclaimer.** PXI routes ticket money straight to the organizer's own Stripe and sells ad credits on the web rather than in the app — obligations designed away in the data flow. **Ask the fixed questions even when they look irrelevant.**

**Every feature ships with its measurement**, **every surface a user reaches is designed**, **build what you use daily and rent what you touch monthly**, and **prefer native, pricing the exception.**

**A plan with no human steps is incomplete**, and **say plainly what you did not verify and did not do.**

**No invented specifics.** Never fabricate a competitor's price, a review quote, a statute, a persona's words or a market figure. An honest `UNVERIFIED:` beats a plausible fiction.

## Working with the user

Ask in batches, with choices where you can — four multiple-choice questions beat one open one. Keep them posted in one short line per phase; findings belong in the plan files and the site, not in chat. When a later phase changes an earlier decision, change it there and note it in "what the re-read changed".

Plans live on disk, so the folder matters. If the session has no project folder or sits in a temporary one, suggest a real folder before writing the plan.

## Files

- `references/00-paths.md` — Stage 1: questions, evidence pass, generating paths, the comparison, recording the choice
- `references/01-wedge.md` — problems from evidence, falsification, competitor teardown, the gap, the wedge
- `references/02-economics.md` — bottom-up sizing, unit economics, the bootstrap test, feeding the model
- `references/03-compliance.md` — the register, federal and state triggers, Apple and Google policy, verification
- `references/04-architecture.md` — decisions against alternatives, the native rule, budgets, cost at scale, data model
- `references/05-design-language.md` — name and identity, inspiration sources, tokens, components, generated assets
- `references/product-preview.md` — which screens to draw as product imagery, the screen kit, writing `screens.json`
- `references/presentation.md` — telling the case: answer first, sentence headlines, the beat order, word limits, model tokens, the visual chooser
- `references/06-growth.md` — SEO, ASO, social, loops and their arithmetic, the measurement contract
- `references/07-monetization.md` — pricing models, the store-policy line per revenue line, payment rails by corridor
- `references/08-ecosystem.md` — value chain, build vs rent vs absorb, the operator console
- `references/departments.md` — the sixteen-department sweep from each head's future seat
- `references/validation.md` — riskiest assumptions, the experiment ladder, honest smoke tests, the results loop
- `references/09-roadmap.md` — Stage 3: steps, contracts first, cut line, gates, rollback, parallel sessions
- `references/10-red-team.md` — the hostile read, abuse and edge cases, kill scenarios, the pre-handoff audit
- `references/traps.md` — the fixed trap sweep
- `references/business-plan.md` — assembling the business plan
- `templates/` — `traps.json`, `departments.json`, `assumptions.example.json`, `screens.example.json`, `story.example.json`, `schemas.md`
- `examples/pxi-analytics-release.md` — a real plan at the target resolution, annotated

## Scripts

Standard-library Python only. Use `python3 -I`.

```bash
python3 -I scripts/new_plan.py <plan> --name "<venture>"                 # scaffold every stage's files
python3 -I scripts/model.py <plan> [--assumptions <plan>/paths/<id>.json]  # assumptions -> projections
python3 -I scripts/build_site.py <plan>                                     # the venture site: plan/venture.html
python3 -I scripts/check_plan.py <plan> --stage explore|plan|build
python3 -I scripts/parallel_brief.py <plan> --out <plan>/briefs
```

`check_plan.py` checks only what the current stage should have produced — including the story's word limits, beat order, model tokens, sources on evidence claims and an honest verdict — and warns when the venture site is older than the plan files. It is deliberately strict about the mechanical rules, because those are the failures that are invisible on a read-through and expensive in week three.
