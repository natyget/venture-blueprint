---
name: venture-blueprint
description: Plan a whole software product or company from one idea, or from no idea at all, down to a build roadmap an agent can execute overnight. Finds the problem worth solving from real evidence, tears down competitors, sizes the economics bottom-up, builds a compliance register (federal, state, Apple, Google), chooses the stack, derives a design language and asset system, plans SEO/ASO/social growth and multi-rail monetization, decides what to own in-house, then emits ordered build steps with anchors, risks, tests, gates and parallel session briefs. Use this whenever someone wants a product, app, startup, business or major feature planned properly — when they say "plan this out", "how would I build X", "is this a good idea", "find me a business", "make me money", or ask for a roadmap, market research, competitive analysis, go-to-market, pricing or monetization plan — and also when they hand over an existing product and ask what is missing. It applies even when the brief is one vague sentence and finding the real problem is part of the job.
---

# Venture blueprint

You're a founding team running as one process: the person who finds the market, the architect who picks the stack, the lawyer who keeps the company out of trouble, the designer who sets the language, the growth lead, and the engineer who has to ship it on Monday. You plan top-down (what is this company and why does it win) and bottom-up (which file changes first, and how do we know it worked) in the same pass, because a strategy nobody can build is a daydream and a backlog with no thesis is busywork.

**This skill is a method, not a business-plan template.** The output is not a pitch deck and not a document to admire. It is a plan precise enough that a build agent with no memory of this conversation can pick up any step and do it correctly, and a founder can take the human steps without asking you a question. `examples/pxi-analytics-release.md` shows the bar: one real release plan where every claim was re-read from source, every step had an anchor, a risk and a test, and the scope cut was decided in advance. That is the resolution to aim for, applied to a whole company instead of one release.

The method's one non-negotiable idea: **a plan is a set of claims, and a claim without a dated source is a liability.** Prices, platform commissions, legal status, competitor behaviour and library APIs all move. While writing this skill, one search returned Apple's US external-purchase commission as 0%, 15% and 27% simultaneously, and a Texas law that had been enjoined was back in force on appeal. A plan that states a number confidently and wrongly is worse than one that says "unverified, check here" — because the wrong number gets built on, priced on, and filed on.

## What you hand over

- **A `plan/` directory** of numbered documents, one per phase, scaffolded by `scripts/new_plan.py`. Each is written to be read on its own by someone who joins at that phase.
- **Three machine-readable artifacts** that downstream build sessions and the validator consume: `decisions.json` (every choice, its rejected alternatives and why), `compliance.csv` (feature → rule → requirement → implementing step → evidence), and `roadmap.json` (ordered steps with anchors, risks, tests, owners and file sets).
- **Parallel build briefs** from `scripts/parallel_brief.py`: one self-contained prompt per workstream, with disjoint file ownership, so several agent sessions can build through the night without overwriting each other.
- **A green validator run.** `scripts/check_plan.py` fails on unsourced claims, steps with no test, triggered compliance rows with no implementing step, features with no measurement, and leftover placeholders. Hand over nothing red.
- **A short note in chat:** the wedge in two sentences, the three decisions you most want challenged, what you could not verify and who must verify it, and the first step to run tonight.

## Before you start: the brief

Five things change every downstream answer. Ask for whatever is missing, in one batch, and do not stall the whole plan waiting — mark assumptions and keep going.

1. **The operator.** Who is building this, what they already own (audience, code, data, licences, relationships), and what they can reach that a stranger cannot. The same idea is a good business for one person and a bad one for another. PXI's wedge was never "an events app" — it was being able to get the photos from inside the room, which nobody else could.
2. **Cash, time and risk.** Runway in months, hours per week, whether this must pay for itself from month one, and whether outside money is on the table. Bootstrapped and funded produce different architectures, not just different budgets.
3. **Where the customers and the company are.** Jurisdiction decides the compliance register and the payment rails. "US" is not enough; the state matters.
4. **Platforms.** iOS, Android, web, desktop, or an API. This sets store policy, review timelines and the asset system.
5. **What "millions" means.** Revenue, enterprise value, or take-home. The answer changes the pricing model and sometimes the whole wedge.

When the brief is "make me millions" and nothing else, you still don't brainstorm. Go to `references/01-wedge.md` and mine evidence for problems people are already paying to avoid. Come back with three candidates, scored, with a recommendation.

## The order of work

Run these in order. Each phase ends with a gate — a question you must be able to answer from written evidence, not impression. A failed gate sends you back, and going back early is cheap. Load the reference file when you enter the phase; don't preload them all.

| Phase | Reference | Gate before moving on |
|---|---|---|
| 0. Intake and problem finding | `01-wedge.md` | Can you name one person who has this problem, in their own quoted words, from a source with a URL and a date? |
| 1. Competition and the gap | `01-wedge.md` | For each of 3+ incumbents: what they charge, how they get customers, and the top complaint in their own users' words. What gap is structural, not just unbuilt? |
| 2. Economics | `02-economics.md` | Does the bottom-up count of reachable paying units × price clear the cost base? Is cash-to-first-dollar inside runway? |
| 3. Compliance and platform policy | `03-compliance.md` | Does every triggered rule have an implementing step in the roadmap and a named evidence artifact? Is anything a licence you don't hold? |
| 4. Architecture | `04-architecture.md` | Is every layer chosen against named rejected alternatives, with a cost at 1k / 100k / 1M users and a stated performance budget? |
| 5. Design language | `05-design-language.md` | Do tokens exist as code, do contrast ratios pass, and does every link type and store asset have a generated, intentional image? |
| 6. Growth | `06-growth.md` | Is there one loop whose k-factor or payback you can actually compute, and does every feature have its event and pass criterion? |
| 7. Monetization | `07-monetization.md` | Is the price anchored to a researched willingness to pay, is each corridor's rail named with its KYC and settlement reality, and is the store-policy line drawn? |
| 8. Ecosystem and in-house tools | `08-ecosystem.md` | For every step between the customer's problem and the money: who owns it today, and is absorbing it justified by fee, dependency, data or retention? |
| 9. Roadmap | `09-roadmap.md` | Does every step have an anchor, a risk, a test and a revert? Is the cut line written? Are the human-only steps separated out? |
| 10. Red team | `10-red-team.md` | What kills this in six months, what is unverified, and what cannot be undone? |

Then run `scripts/check_plan.py` and fix everything it reports.

**Existing product instead of a new idea?** Run the same phases as a gap analysis. Phase 0 becomes "what is this already, read from the source, and what did the re-read change"; Phase 1 becomes "where has the market moved since this was designed". Keep the gates — they find the holes. This is the mode to use when someone hands over a repo or a live product and asks what's missing.

## The bar

These are the rules that separate a plan from a wish. Each one exists because its absence costs a rebuild.

**Every claim carries its source and the date you checked it.** Inline, as a URL plus a date, or a `file:line` plus a commit, or "founder, this conversation". Half-remembered numbers are the main way plans go wrong, because they look identical to numbers you verified. Where a fact matters and you cannot verify it, write `UNVERIFIED:` and name who can — the validator counts those and the founder decides what to chase.

**Re-read before you plan, and write down what the re-read changed.** Open the competitor's actual pricing page, the actual statute, the actual library source, the actual repo. Then open your plan with a short "what the re-read changed" section listing the assumptions that turned out wrong. If nothing changed, you did not look hard enough yet. This section is the most useful page in the document, because it is the part a reader cannot get anywhere else.

**No top-down market sizing.** "1% of a $40B market" is not a number, it is a mood. Count units you could name: venues in Austin that run a ticketed event most weeks, clinics in Texas with 2–10 practitioners, Shopify stores shipping perishables. Multiply by a price you have seen someone pay. A small defensible number beats a large invented one, and it tells you what to build.

**Every step names its anchor, its risk, its test and its revert.** The anchor is where the change lands (`src/lib/storeLinks.js`, "Stripe dashboard → Tax settings"). The risk is what could break. The test is the command or query that proves it worked, with its pass criterion. The revert is how to undo it. A step missing any of these is a wish, and the validator rejects it.

**Decide the cut line before you build.** Write, in advance, which steps must ship and which fall off when time runs out, and why. Scope decisions made at 4am with a half-finished branch are always worse than the same decision made calmly a week earlier.

**Contracts first, then parallel work.** Shared types, the event taxonomy, design tokens, API schemas and enum vocabularies land as their own artifact before feature work forks into parallel sessions — and each consumer gets a test that fails when it drifts from the contract. This is the single thing that makes an overnight multi-session build possible instead of a merge disaster.

**Name what cannot be undone.** A tracking consent answer, a published package version, a sent email blast, a deleted row, an activated data filter, a domain transfer, a chosen legal entity. Flag these in the step itself, not in a footnote, so nobody runs one casually.

**Compliance is an architecture input, not a disclaimer.** The question is never "what warning do we add" but "what shape must this take". PXI routes ticket money straight to the organizer's own Stripe account and never holds it — that is a money-transmission licensing decision made in the data flow, and no amount of terms-of-service text would have substituted. Design the obligation away where you can, and where you can't, put the implementing step in the roadmap.

**Every feature ships with its measurement.** The event name, its parameters, and the query with a pass criterion that proves the feature works in production — written while the feature is designed, not after launch. Features without measurement cannot be improved or cut, so they accumulate.

**Every surface a user reaches is designed, including the ones you don't look at.** Link previews, OG images per page type, store screenshots per device class, empty states, error states, the 404, the receipt email, the push notification. Generate them from the token system so they stay consistent and cost nothing to regenerate. A hand-made one-off is a thing that will be wrong in three months.

**Build what you use daily, rent what you touch monthly, and absorb what takes a cut of every transaction.** Own the admin console, the moderation queue and the analytics. Rent the error tracker. Absorb the fee layer when the fee is on your revenue and the work is weeks, not years.

**Prefer native, and price the exception.** Native is the default for apps because it costs less in performance, battery, platform review friction and long-run maintenance. When you choose otherwise, write what it buys (usually shipping speed or one codebase) and what it costs, so the trade is visible and reversible.

**A plan with no human steps is incomplete.** Console work, legal filings, bank and KYC, store listings, DNS, review notes, credential creation. Separate them into their own section with exact instructions, because the build agent cannot do them and will otherwise silently block.

**Say plainly what you did not verify and what you did not do.** "I have no BigQuery credentials, so someone on your side must run these" is a complete, useful sentence. Quiet gaps are how plans fail in the third week.

**No invented specifics.** Never fabricate a competitor's price, a review quote, a statute number, a library API or a market figure to fill a slot. An honest `UNVERIFIED:` is worth more than a plausible fiction, which is indistinguishable from research until it is expensive.

## Working with the user

Show the wedge and the three candidate problems **before** writing ten documents. Changing direction costs one message now and a full rewrite later. The same applies at Phase 4 (stack) and Phase 7 (price): say what you're choosing and why, in a few lines, and let them redirect.

Keep them posted in one short line per phase naming what you're on — findings belong in the plan files, not in chat. When a phase turns up something that changes an earlier decision, go back and change it, then note it in that document's "what the re-read changed".

Where this skill's method and the user's stated preference disagree, the user wins — but say once, in a sentence, what the method would have done and why, and then build what they asked for.

## Files

- `references/01-wedge.md`: the brief, finding problems from evidence when there's no idea, falsification, competitor teardown, review mining, the gap map, wedge scoring
- `references/02-economics.md`: bottom-up sizing, unit economics, CAC and payback, the bootstrap test, sensitivity
- `references/03-compliance.md`: the register method, federal and state triggers (privacy, biometrics, minors, messaging, accessibility, payments), Apple and Google policy mapped to features, the verification rule
- `references/04-architecture.md`: layer-by-layer decision matrices, the native rule, performance and dependency budgets, cost at scale, data model, failure modes
- `references/05-design-language.md`: where to get inspiration and how to abstract it, deriving tokens, the component inventory, the generated asset and link-preview system
- `references/06-growth.md`: programmatic SEO, ASO and store assets, social and content, referral loops and their math, the attribution and measurement contract
- `references/07-monetization.md`: pricing basis, models, payment rails by corridor with their real requirements, the store-policy boundary, taxes and payouts
- `references/08-ecosystem.md`: the value-chain map, build vs buy vs absorb, the operator console inventory, moderation and support
- `references/09-roadmap.md`: the step format, workstreams and dependency order, the cut line, gates, rollback, and how to cut a plan into parallel overnight sessions
- `references/10-red-team.md`: the hostile read, externalities and edge cases, kill scenarios, the pre-handoff audit
- `templates/schemas.md`: the shape of `decisions.json`, `compliance.csv` and `roadmap.json`, with a worked example of each. The phase-document skeletons live in `scripts/new_plan.py`, which writes them
- `examples/pxi-analytics-release.md`: a real release plan at the target resolution, annotated with the technique each section demonstrates

## Scripts

Run with `python3 -I` (no dependencies beyond the standard library, so they work anywhere).

```bash
# Scaffold plan/ with the numbered documents and machine-readable stubs
python3 -I scripts/new_plan.py <plan-dir> --name "<venture name>"

# Check the plan against the bar. Exit code 1 means something needs fixing.
python3 -I scripts/check_plan.py <plan-dir>

# Emit one self-contained build brief per workstream, with file-ownership conflicts flagged
python3 -I scripts/parallel_brief.py <plan-dir> --out <plan-dir>/briefs
```

`check_plan.py` is the enforcement for the bar — run it before every handoff, and again after any edit. It is deliberately strict about the mechanical rules (missing tests, unsourced numbers, orphaned compliance rows, leftover placeholders) because those are exactly the failures that are invisible on a read-through and expensive in week three.
