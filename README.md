# Venture blueprint

A Claude skill that plans a whole software product or company — from one idea, or from no idea at all — down to a build roadmap an agent can execute overnight.

It finds the problem worth solving from real evidence, tears down the competition, sizes the economics from countable units, builds a compliance register across federal, state and app-store rules, chooses the stack against named alternatives, derives a design language and a generated asset system, plans growth and multi-rail monetization, decides what to own in-house, then emits ordered build steps with anchors, risks, tests, gates and parallel session briefs.

It is a method, not a business-plan template. The output is not a pitch deck — it is a plan precise enough that a build agent with no memory of the conversation can pick up any step and do it correctly, and precise enough that a validator can fail it.

## Install

**As a plugin (recommended — you get updates):**

```
/plugin marketplace add natyget/venture-blueprint
/plugin install venture-blueprint
```

**As a skill, for every project on your machine:**

```bash
git clone https://github.com/natyget/venture-blueprint.git
ln -s "$PWD/venture-blueprint/plugins/venture-blueprint/skills/venture-blueprint" ~/.claude/skills/venture-blueprint
```

**As a skill, for one repository** (works in cloud sessions too): copy `plugins/venture-blueprint/skills/venture-blueprint` to `.claude/skills/venture-blueprint/` and commit it.

**In the Claude app:** upload `dist/venture-blueprint.skill` as a custom skill. The scripts need Python 3 and nothing else, so they run anywhere, but Claude Code is the better home because the plan wants a filesystem.

## Use

Start a session and say any of:

- "Plan out an app that lets neighbours share tools." It runs all eleven phases.
- "Make me millions." Finding the problem is part of the job — it mines evidence and comes back with three scored candidates and a recommendation.
- "Here's my repo. What's missing?" Same phases, run as a gap analysis.
- "Plan the monetization and payment rails for this, including Kenya and Ethiopia."
- "Is this a good idea?" It tries to kill the idea first, in writing, then tells you whether it survived.

Expect to be shown the wedge and the candidate problems **before** ten documents get written — that redirect costs one message, and skipping it costs a rewrite.

## What you get

```
plan/
├── 00-brief.md … 10-red-team.md    one document per phase
├── decisions.json                   every choice, its rejected alternatives, and why
├── compliance.csv                   feature → rule → requirement → step → evidence
├── roadmap.json                     ordered steps with anchors, risks, tests, file sets
└── briefs/                          one self-contained build brief per workstream
```

## The scripts

No dependencies beyond the Python standard library.

```bash
python3 -I scripts/new_plan.py plan --name "Acme"      # scaffold the documents
python3 -I scripts/check_plan.py plan                  # check it against the bar
python3 -I scripts/parallel_brief.py plan --out plan/briefs
```

`check_plan.py` fails on steps with no runnable test, compliance rows pointing at nothing, decisions with no rejected alternatives, dependency cycles, user-facing features with no measurement, concurrent workstreams fighting over a file, and leftover placeholders. It fails on a fresh scaffold by design — it is a worklist before it is a gate.

`parallel_brief.py` refuses to generate briefs when two workstreams that could run at the same time claim the same file, and reports the critical path in hours, which is what one night actually reaches.

## The eleven phases

Each ends with a gate — a question you must answer from written evidence, not impression.

| Phase | Gate |
|---|---|
| Intake and problem finding | Can you name one person with this problem, in their own quoted words, from a source with a URL and a date? |
| Competition and the gap | For 3+ incumbents: price, acquisition channel, top complaint in their users' words. Which gap is structural? |
| Economics | Does the bottom-up count clear the cost base? Is cash-to-first-dollar inside runway? |
| Compliance and platform policy | Does every triggered rule have an implementing step and a named evidence artifact? |
| Architecture | Is every layer chosen against named alternatives, with cost at 1k/100k/1M and a performance budget? |
| Design language | Do tokens exist as code, does contrast pass, and does every link type have a generated image? |
| Growth | Is there one loop whose k-factor or payback you can compute, and does every feature have its event? |
| Monetization | Is the price anchored to researched willingness to pay, and is each corridor's rail named with its KYC reality? |
| Ecosystem and in-house tools | For every step from problem to money: who owns it, and is absorbing it justified? |
| Roadmap | Does every step have an anchor, a risk, a test and a revert? Is the cut line written? |
| Red team | What kills this in six months, what is unverified, and what cannot be undone? |

## The trap sweep

Running through every phase is a fixed list of 24 questions whose answers are free now and expensive later — the ones where a third party's rule quietly decides your margin or your legality and nothing in your own code mentions it. Is each revenue line consumed in the app or in the world (because that decides whether a store takes a cut of it)? Does a minor signing up attach duties you did not know about? Do you ever hold someone else's money, even briefly? Does a transitive dependency's licence conflict with how you ship?

Judgement finds the traps you can imagine. A fixed checklist finds the ones you can't — so the list is fixed, `traps.csv` has no blanks, and "not applicable" has to carry a reason.

## The one idea worth keeping

A plan is a set of claims, and a claim without a dated source is a liability. Prices, platform commissions, legal status and library APIs all move. A plan that states a number confidently and wrongly is worse than one that says "unverified, check here" — because the wrong number gets built on, priced on, and filed on.

## Not legal, tax or investment advice

The compliance phase produces a register for a licensed attorney in the relevant jurisdiction to review. It is a research and planning aid, not a substitute for professional advice, and the skill is written to say so in its own output.

## Licence

MIT. See `LICENSE` — set the copyright holder to your own name before publishing.
