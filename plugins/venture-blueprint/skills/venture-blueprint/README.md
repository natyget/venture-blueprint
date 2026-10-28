# Venture blueprint (a Claude skill)

Plans a whole software product or company from one idea — or from no idea at all — down to a build roadmap an agent can execute overnight.

It finds the problem worth solving from real evidence, tears down the competition, sizes the economics from countable units, builds a compliance register across federal, state and app-store rules, chooses the stack against named alternatives, derives a design language and a generated asset system, plans growth and multi-rail monetization, decides what to own in-house, then emits ordered build steps with anchors, risks, tests, gates and parallel session briefs.

It is a method, not a business-plan template. The output is not a pitch deck — it is a plan precise enough that a build agent with no memory of the conversation can pick up any step and do it correctly, and precise enough that a validator can fail it.

## Install (pick one)

- **Claude Code on your computer, for every project:** put this folder at `~/.claude/skills/venture-blueprint/`.
- **For one project (works in cloud sessions too):** put it at `.claude/skills/venture-blueprint/` inside the repository and commit it.
- **Claude app:** upload as a custom skill. The scripts need Python 3 and nothing else, so they run anywhere, but Claude Code is the better home because the plan wants a filesystem.

## Use

Start a session and say any of:

- "Plan out an app that lets neighbours share tools." It runs all eleven phases.
- "Make me millions." Finding the problem is part of the job — it mines evidence and comes back with three scored candidates and a recommendation.
- "Here's my repo / my live product. What's missing?" Same phases, run as a gap analysis.
- "Plan the monetization and payment rails for this, we need Kenya and Ethiopia too."
- "Is this a good idea?" It will try to kill the idea first, in writing, and then tell you whether it survived.

Expect to be shown the wedge and the candidate problems **before** ten documents get written — that redirect costs one message, and skipping it costs a rewrite.

## What you get

A `plan/` directory:

```
plan/
├── 00-brief.md … 10-red-team.md    one document per phase
├── decisions.json                   every choice, its rejected alternatives, and why
├── compliance.csv                   feature → rule → requirement → step → evidence
├── roadmap.json                     ordered steps with anchors, risks, tests, file sets
└── briefs/                          one self-contained build brief per workstream
```

Plus a short note in chat: the wedge in two sentences, the three decisions most worth challenging, what could not be verified and who must verify it, and the first step to run tonight.

## The scripts

No dependencies beyond the Python standard library.

```bash
python3 -I scripts/new_plan.py plan --name "Acme"      # scaffold the documents
python3 -I scripts/check_plan.py plan                  # check it against the bar
python3 -I scripts/parallel_brief.py plan --out plan/briefs
```

`check_plan.py` fails on steps with no runnable test, compliance rows pointing at nothing, decisions with no rejected alternatives, dependency cycles, features with no measurement, concurrent workstreams fighting over a file, and leftover placeholders. It fails on a fresh scaffold by design — it is a worklist before it is a gate.

`parallel_brief.py` refuses to generate briefs when two workstreams that could run at the same time claim the same file, and tells you the critical path in hours, which is what one night actually reaches.

## What's inside

- `SKILL.md`: the phase order, the gates, and the bar.
- `references/`: one file per phase, loaded only when that phase runs — wedge and competition, economics, compliance, architecture, design language, growth, monetization, ecosystem, roadmap, red team.
- `templates/`: the document skeletons and the shape of the three machine-readable artifacts.
- `scripts/`: scaffold, validator, brief generator.
- `examples/`: one real release plan at the resolution to aim for, annotated with the technique each section demonstrates.

## The one idea worth keeping

A plan is a set of claims, and a claim without a dated source is a liability. Prices, platform commissions, legal status and library APIs all move. A plan that states a number confidently and wrongly is worse than one that says "unverified, check here" — because the wrong number gets built on, priced on, and filed on.
