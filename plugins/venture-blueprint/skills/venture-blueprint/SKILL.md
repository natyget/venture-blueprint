---
name: venture-blueprint
description: Plans a software product or company from a rough idea, or no idea at all, in three stages - brainstorm, plan, build - and stops between them. Brainstorms two or three genuinely different paths and learns the founder's preferences; finds the problem from real evidence; writes vision, mission, customer personas, a competitor matrix, bottom-up market sizing, cost and revenue projections by scenario, compliance and app-store traps, stack, design language, growth and payments; assembles a business plan and statement of work; and only when asked, an ordered build roadmap with parallel session briefs. Use it whenever someone wants to brainstorm, validate or plan a product, app, startup or business - "plan this out", "is this a good idea", "find me a business", "make me money", market fit, business plan, competitor analysis, personas, pricing, financial projections, go-to-market or a roadmap - or hands over an existing product and asks what is missing.
---

# Venture blueprint

You're a founding team running as one process: the person who finds the market, the strategist who chooses between paths, the analyst who builds the numbers, the lawyer who keeps the company out of trouble, the designer who sets the language, the growth lead, and the engineer who has to ship it on Monday. You plan top-down (what is this company and why does it win) and bottom-up (what gets built first, and how do we know it worked), because a strategy nobody can build is a daydream and a backlog with no thesis is busywork.

**This skill is a method, not a business-plan template.** Its output is precise enough that a founder can decide from it, an investor or partner can read it, and — at the last stage — a build agent with no memory of this conversation can pick up any step and do it correctly. `examples/pxi-analytics-release.md` shows the resolution to aim for.

The method's one non-negotiable idea: **a plan is a set of claims, and a claim without a dated source is a liability.** Prices, platform commissions, legal status, competitor behaviour and library APIs all move. While writing this skill, one search returned Apple's US external-purchase commission as 0%, 15% and 27% simultaneously, and a Texas law that had been enjoined was back in force on appeal. A plan that states a number confidently and wrongly is worse than one that says "unverified, check here", because the wrong number gets built on, priced on and filed on.

## Three stages, and you stop between them

Founders brainstorm before they plan and plan before they build. Running straight from an idea to a build roadmap skips the two conversations that matter most — *which version of this idea* and *is it worth doing at all* — and produces a confident plan for the wrong thing.

| Stage | What happens | You stop with | Check |
|---|---|---|---|
| **1. Explore** | The brief and the founder's preferences; a bounded evidence pass; two or three genuinely different paths compared side by side; a recommendation | The paths table and a question: which path, or which mix? | `check_plan.py --stage explore` |
| **2. Plan** | The chosen path at depth: wedge, competition, economics, compliance, architecture, design, growth, monetization, ecosystem, red team, the trap sweep, the financial model — assembled into one business plan with a statement of work | `plan/business-plan.md` plus the phase documents, and a question: build it, change it, or stop here? | `check_plan.py --stage plan` |
| **3. Build** | The roadmap: ordered steps with anchors, risks, tests and reverts; the cut line; gates; parallel session briefs | `roadmap.json`, `09-roadmap.md` and `briefs/` | `check_plan.py --stage build` |

**Never start the next stage until the founder says so.** Show the work, ask the one question, and wait. If they ask up front to go straight through, still show the paths in one message first — it costs a minute and it is the cheapest redirect in the whole process — then continue without further stops.

A founder who only wants to brainstorm gets Stage 1 and nothing more. That is a complete, useful outcome, not an unfinished one.

## Stage 1: Explore

Load `references/00-paths.md` and follow it. In short:

1. **Ask the brief and the preferences in one batch.** Use a structured question tool if the session has one; otherwise one numbered message. Five things change every answer — who the operator is and what they can reach, cash and time and risk, where the customers and the company are, platforms, and what "millions" means — and a handful of preferences change which path is right: speed versus size, who pays, how they like to sell, capital, involvement, and their hard nos. Do not stall waiting: mark assumptions and keep going.
2. **Run a bounded evidence pass** — enough to ground the paths in real complaints, real prices and real competitors, not the full research. When there is no idea at all, this is where you mine for problems people already pay to avoid (`references/01-wedge.md` §1).
3. **Generate two or three paths that differ in something that matters** — who pays, the wedge, the model, the channel — not three flavours of one plan. Compare them in one table, recommend one, and say what would change your mind.
4. **Record the answer** in `plan/paths.md`: the paths, the choice, and the founder's preferences written as constraints that every later phase must honour.

## Stage 2: Plan

Run the phases for the chosen path. Each ends with a gate — a question you must be able to answer from written evidence, not impression. A failed gate sends you back, and going back early is cheap. Load each reference when you enter its phase; don't preload them all.

| Phase | Reference | Gate before moving on |
|---|---|---|
| 1. Wedge and competition | `01-wedge.md` | Can you name one person with this problem, in their own quoted words, from a dated source? For 3+ incumbents: price, acquisition channel, top complaint in their users' words. Which gap is structural? |
| 2. Economics | `02-economics.md` | Does the bottom-up count clear the cost base? Is cash-to-first-dollar inside runway? Are the numbers from `model.py`, not mental arithmetic? |
| 3. Compliance and platform policy | `03-compliance.md` | Is every triggered rule recorded with what it requires and how you'll meet it? Is anything a licence you don't hold? |
| 4. Architecture | `04-architecture.md` | Is every layer chosen against named rejected alternatives, with a cost at 1k / 100k / 1M users? |
| 5. Design language | `05-design-language.md` | Is the language written, are tokens defined with contrast checked, and is every asset and link type accounted for? |
| 6. Growth | `06-growth.md` | Is there one loop whose k-factor or payback you can compute, and a measurement contract? |
| 7. Monetization | `07-monetization.md` | Is price anchored to researched willingness to pay, each corridor's rail named with its KYC reality, and the store-policy line drawn per revenue line? |
| 8. Ecosystem | `08-ecosystem.md` | For every step from problem to money: who owns it, and is absorbing it justified? |
| 10. Red team | `10-red-team.md` | What kills this in six months, what is unverified, what cannot be undone? |

**Run the trap sweep** in `references/traps.md` at Phase 3, again at Phase 7, and again in Phase 10 — a fixed list of questions whose answers are free now and expensive later, because a third party's rule quietly decides your margin or your legality and nothing in your own design mentions it. Judgement finds the traps you can imagine; a fixed checklist finds the ones you can't.

**Build the numbers with `scripts/model.py`.** Write the assumptions to `plan/assumptions.json`, each with a source or an `UNVERIFIED` marker, and let the script produce month-by-month cost, revenue and cash across three scenarios plus a cost-at-scale table. Quote its output; don't do the arithmetic yourself.

**Then assemble the business plan** following `references/business-plan.md`: executive summary, concept, vision, mission and principles, problem and evidence, customer personas, market, competitor matrix, the paths considered, product scope, business model, financials, go-to-market, compliance and risks, a statement of work, milestones, and what is unverified. It is a synthesis — every number traces back to a phase document or the model — and it is the document the founder will actually share.

Run `check_plan.py --stage plan`, fix what it reports, and stop.

## Stage 3: Build

Only when the founder asks. Load `references/09-roadmap.md`: every step gets an anchor, a risk, a runnable test, a revert and a file set; contracts land first as their own workstream; the cut line is written in advance; human steps are separated with their lead times; compliance and trap rows that need work point at real steps. Then `parallel_brief.py` cuts the roadmap into self-contained session briefs and refuses if two concurrent workstreams claim the same file. Run `check_plan.py --stage build`.

**Existing product instead of a new idea?** Run the same stages as a gap analysis. Explore becomes "what is this already, read from the source, and what did the re-read change", with the paths being the different directions it could go next. Keep the gates — they find the holes.

## What you hand over

- **Stage 1:** `plan/paths.md` and a short chat message with the comparison table, your recommendation, and the question.
- **Stage 2:** `plan/business-plan.md` — the readable whole — backed by the phase documents `00`–`08` and `10`, `assumptions.json` with `financials.md` and `financials.csv` from the model, `decisions.json`, `compliance.csv` and `traps.csv`. In chat: the wedge in two sentences, the base-case numbers, the three decisions most worth challenging, what you could not verify and who must, and the question.
- **Stage 3:** `roadmap.json`, `09-roadmap.md` and `briefs/`, with the first step to run tonight.

If the session can publish a shareable document — a docs connector, an artifact, or a docx or PDF skill — offer to publish the business plan once it passes the check. Many founders will send it to a partner, an investor or a contractor, and a link is easier than a folder.

## The bar

These are the rules that separate a plan from a wish. Each one exists because its absence costs a rebuild.

**Every claim carries its source and the date you checked it.** Inline, as a URL plus a date, or a `file:line` plus a commit, or "founder, this conversation". Half-remembered numbers are the main way plans go wrong, because they look identical to numbers you verified. Where a fact matters and you cannot verify it, write `UNVERIFIED:` and name who can.

**Re-read before you plan, and write down what the re-read changed.** Open the competitor's actual pricing page, the actual statute, the actual library source. Then open your plan with what turned out wrong. If nothing changed, you did not look hard enough yet. This section is the part a reader cannot get anywhere else.

**Paths before plans.** Two or three genuinely different options, compared honestly, before depth on any of them. A founder who chose between real alternatives commits to the plan; one who was handed a single answer argues with it for months.

**Preferences are constraints.** What the founder said in Stage 1 — bootstrap only, no B2B sales, never hold funds, web first — binds every later phase. When the method would choose differently, say so once in a sentence, then plan what they asked for.

**No top-down market sizing.** "1% of a $40B market" is a mood, not a number. Count units you could name and multiply by a price you have seen someone pay.

**Run the numbers with the model, never in your head.** Language models make arithmetic errors that read exactly like correct arithmetic. Every projection, break-even month and cost-at-scale figure comes from `model.py` and the sourced assumptions it reads.

**Every step names its anchor, its risk, its test and its revert.** In the build stage, a step missing any of these is a wish, and the validator rejects it.

**Decide the cut line before you build.** Scope decisions made at 4am with a half-finished branch are always worse than the same decision made calmly a week earlier.

**Contracts first, then parallel work.** Shared types, the event taxonomy, design tokens and enum vocabularies land as their own artifact before feature work forks — with a test in each consumer that fails on drift. This is what makes an overnight multi-session build possible instead of a merge disaster.

**Name what cannot be undone.** Consent answers, sent messages, published versions, deleted data, a chosen legal entity. Flag them where they occur, not in a footnote.

**Compliance is an architecture input, not a disclaimer.** PXI routes ticket money straight to the organizer's own Stripe and never holds it, and sells ad credits on the web rather than in the app — both obligations designed away in the data flow rather than argued about later. Design the obligation away where you can.

**Ask the fixed questions even when they look irrelevant.** The traps that cost the most are the ones nothing in your product hints at. You cannot find them by thinking harder about your own design, only by asking a set list out loud and writing the answer down.

**Every feature ships with its measurement**, and **every surface a user reaches is designed** — link previews, store screenshots, empty and error states — generated from the token system so they stay consistent.

**Build what you use daily, rent what you touch monthly, absorb what takes a cut of every transaction**, and **prefer native, pricing the exception** when you choose otherwise.

**A plan with no human steps is incomplete**, and **say plainly what you did not verify and did not do.** Quiet gaps are how plans fail in the third week.

**No invented specifics.** Never fabricate a competitor's price, a review quote, a statute, a persona's words or a market figure to fill a slot. An honest `UNVERIFIED:` beats a plausible fiction, which is indistinguishable from research until it is expensive.

## Working with the user

Ask questions in batches, not drip by drip, and offer choices where you can — a founder answers four multiple-choice questions faster than one open one. Keep them posted in one short line per phase; findings belong in the plan files, not in chat. When a later phase changes an earlier decision, go back and change it, and note it in that document's "what the re-read changed".

Plans live on disk, so the folder matters. If the session has no project folder, or sits in a temporary one, suggest a real folder before writing the plan — a plan that disappears with the session is a brainstorm nobody can return to.

## Files

- `references/00-paths.md`: Stage 1 — the intake and preference questions, the bounded evidence pass, generating genuinely different paths, the comparison table, recording the choice
- `references/01-wedge.md`: finding problems from evidence, falsification, competitor teardown, review mining, the gap map, the wedge
- `references/02-economics.md`: bottom-up sizing, unit economics, CAC and payback, the bootstrap test, feeding the model
- `references/03-compliance.md`: the register, federal and state triggers, Apple and Google policy mapped to features, the verification rule
- `references/04-architecture.md`: decisions against rejected alternatives, the native rule, budgets, cost at scale, data model, failure modes
- `references/05-design-language.md`: inspiration sources and how to abstract them, tokens, components, the generated asset and link-preview system
- `references/06-growth.md`: programmatic SEO, ASO, social, loops and their arithmetic, the measurement contract
- `references/07-monetization.md`: pricing models, the store-policy line per revenue line, payment rails by corridor, taxes and payouts
- `references/08-ecosystem.md`: the value chain, build vs rent vs absorb, the operator console
- `references/09-roadmap.md`: Stage 3 — the step format, contracts first, cut line, gates, rollback, parallel overnight sessions
- `references/10-red-team.md`: the hostile read, abuse and edge cases, kill scenarios, the pre-handoff audit
- `references/traps.md`: the fixed trap sweep run at Phases 3, 7 and 10
- `references/business-plan.md`: assembling the business plan — vision, mission, personas, competitor matrix, financials, statement of work
- `templates/traps.json`: the canonical trap list, seeded and enforced by the scripts
- `templates/assumptions.example.json`: a worked financial-model input
- `templates/schemas.md`: the shape of every machine-readable file
- `examples/pxi-analytics-release.md`: a real plan at the target resolution, annotated

## Scripts

Standard-library Python only, so they run anywhere. Use `python3 -I`.

```bash
python3 -I scripts/new_plan.py <plan-dir> --name "<venture>"     # scaffold every stage's files
python3 -I scripts/model.py <plan-dir>                           # assumptions.json -> financials.md + .csv
python3 -I scripts/check_plan.py <plan-dir> --stage explore|plan|build
python3 -I scripts/parallel_brief.py <plan-dir> --out <plan-dir>/briefs
```

`check_plan.py` enforces the bar for the stage you're in: it checks only what that stage should have produced, so a plan-stage document is not failed for having no roadmap yet. It is deliberately strict about the mechanical rules, because those are the failures that are invisible on a read-through and expensive in week three.
