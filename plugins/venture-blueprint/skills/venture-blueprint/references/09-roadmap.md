# Roadmap: steps an agent can execute, and how to run them in parallel overnight

This is where the plan becomes buildable. The test is specific: a build agent with no memory of this conversation should be able to pick any step, do it correctly, prove it worked, and undo it if it didn't. Everything in this phase serves that test.

## 1. The step format

Every step is one commit. One commit per step is what makes any single step revertible without unpicking three others — which is the whole reason the format has a revert field.

```
ID:        W4
Workstream: web
Anchor:    src/app/get/route.js:16-26
Change:    Accept only whitelisted params: ct matching ^[a-z0-9-]{1,40}$, click
           ids ^[\w-]{1,200}$, utm_* capped at 100 chars, city must be in
           cities.json, intent must be a known intent. Build the store URL with
           the W1 helper. Keep the redirect host fixed to the two stores, and
           keep no-store and Vary: User-Agent.
Why:       An open redirect here would let anyone send traffic through our
           domain; the whitelist is the control.
Risk:      A legitimate param we forgot gets dropped. Low — the set is enumerated
           in the Phase 6 contract.
Test:      curl -sI with an iPhone and an Android user agent; assert the Location
           header is the expected store URL and carries ct. Pass: both 302 to the
           correct store host, neither carries an unlisted param.
Revert:    Revert the commit; the previous handler is unchanged behaviour.
Effort:    1h
Depends:   W1
Files:     src/app/get/route.js, src/app/get/route.test.mjs
Human:     no
Irreversible: no
```

Fields that earn their place:

- **Anchor** is the file and line, or the exact console path (`Stripe dashboard → Tax → Registrations`). "Update the checkout" is not an anchor; it is a hope.
- **Risk** names what breaks and how likely. Writing it is also the cheapest way to notice a step is actually three steps.
- **Test** is a command or query plus a pass criterion. "Verify it works" fails the validator. A test nobody can run is not a test.
- **Revert** matters most for the steps where it is hard, because that is where you need to know in advance.
- **Depends** gives the real order, which is what lets the parallel split be computed rather than guessed.
- **Files** is the ownership claim that keeps parallel sessions from colliding. Be exhaustive; an unlisted file is an unprotected file.
- **Human** marks the steps an agent cannot do.
- **Irreversible** marks the ones that change the world permanently.

Keep steps to roughly an hour or two. A step estimated at a day is a workstream that has not been thought through, and the parts you haven't separated are where it will go wrong.

## 2. Workstreams and order

Group steps into workstreams that map to ownership: `contracts`, `api`, `web`, `app-ios`, `app-android`, `design-system`, `infra`, `ops-console`, `growth`, `human`. Then order them by their real dependencies, and deploy in that order.

**Contracts first, always.** Shared types, the API schema, the event taxonomy from Phase 6, the design tokens from Phase 5, the enum vocabularies from Phase 4. These land as their own workstream, with a drift test in every consumer, before any feature workstream starts. This is not tidiness: it is the precondition for everything in §5. Parallel sessions can only work simultaneously if the thing they must agree on is already fixed and mechanically enforced.

Then the order that tends to hold: contracts → data model and migrations → API → clients → growth surfaces → ops console. Human steps with lead times (entity formation, KYC, store enrolment, DMCA agent registration, carrier registration for SMS) go **first in wall-clock time** regardless of where they sit logically, because they are the only steps that cannot be hurried by working harder.

## 3. The cut line

Write, before anything is built, the ordered list of what falls off when time runs out — and why each is safe to drop. Three tiers:

- **Must ship.** The product is incoherent or illegal without it. Usually: the core loop, the compliance steps with a deadline, anything that must be in a binary rather than an update.
- **Should ship.** Real value, safe to follow a week later.
- **Can follow.** Polish, second-order surfaces, the optimizations.

Name specifically anything that must be in a *native binary* rather than shipped as an over-the-air update, because that distinction decides whether a late cut is possible at all. The equivalent for web is anything behind a migration.

The cut line's purpose is to move the decision out of the moment of pressure. A scope choice made calmly in advance is reliably better than the same choice made at 4am with a half-finished branch.

## 4. Gates, rollback, and the human section

**Gates.** The enumerated conditions that must be true before you ship — not a feeling. Each is a command, a query or an observation with a pass criterion: the automated checks are green; the funnel script from Phase 6 passes on a real device; the compliance rows marked `counsel: required` have been reviewed; the asset check finds no missing or fallback images; the three smoke paths work. Write them before the build, because gates written afterwards are written to fit what you built.

**Rollback, per surface.** Each surface reverts differently and at a different speed — a web deploy in minutes, a native binary in days through review, an over-the-air update in minutes, a migration maybe not at all. Write the procedure for each, and then write the list of things that **cannot be rolled back**: sent messages, consent answers, deleted data, published package versions, an activated filter that drops data, a transferred domain. That list is the one people most need and least often have.

**The human section.** Everything an agent cannot do, with exact instructions and lead times: entity and registered agent, bank and KYC, developer program enrolment, DNS, store listing and review notes, carrier registration, legal review, credentials to create and where to put them. Mark which steps block which workstreams. A plan that quietly assumes these are done is a plan that stalls on day two.

## 5. Cutting the plan into a parallel overnight build

The goal: several agent sessions working through the night without overwriting each other, producing a build that integrates in the morning. What makes it work is not parallelism; it is the contract plus disjoint file ownership.

**The rules:**

1. **Contracts land first, in one session, alone.** Nothing else starts until that workstream's commit exists. Every other session reads the contract and may not change it — a session that needs a contract change stops and reports instead of editing, because a contract edited in two places is the failure this whole structure exists to prevent.
2. **File sets must be disjoint.** `scripts/parallel_brief.py` computes this from each step's `Files` and refuses to emit briefs for two concurrent workstreams that claim the same path. If two need the same file, either the split is wrong or one must wait.
3. **One workstream per session.** A session owns its workstream, its branch and its files, commits one commit per step, and does not touch another's.
4. **Every session gets the same spine** and nothing it doesn't need: the wedge in two sentences, the contract artifact, the tokens, its own steps verbatim, the budgets and bar it must respect, its tests and how to run them, and an explicit list of what it must not touch.
5. **Integration is its own step**, with an owner and an order. Merge contracts, then API, then clients, then run the full gate list. Expect conflicts only in integration files; if you get them elsewhere, the ownership split was wrong and that is worth writing down for next time.
6. **A session that gets blocked stops and reports.** It does not improvise a contract change, invent a dependency, or widen its file set. Say this in the brief — it is the difference between a blocked step and a corrupted branch.

**The brief**, one per workstream, is self-contained because the session has none of this conversation:

```
Workstream: web
Branch: build/web
Context: <wedge in 2 sentences> <the one thing this workstream is for>
Contract: <path to the contract artifact> — read it; do not modify it
Tokens: <path> — use tokens only; a hardcoded value is a lint error
Your steps: <the full step blocks, verbatim, in order>
You own: <exact file list>
Do not touch: <contract paths, other workstreams' files>
Tests: <commands> — every step's test must pass before its commit
Budgets: <the Phase 4 budgets that apply here>
When blocked: stop, commit what passes, and report what you need. Do not change
  the contract or take files outside your list.
Done when: <the workstream's own gate>
```

Then size the night honestly: sum the effort estimates per workstream, take the longest chain through the dependency graph, and state what one night actually reaches. "Overnight" is a real constraint, not a wish — it is what the cut line is for, and a plan that claims more than the critical path allows is the plan failing before it starts.

## Output of this phase

Write `plan/09-roadmap.md` with: the workstream list and deploy order; every step in the full format; the contracts workstream marked as the blocking prerequisite; the cut line in three tiers with the binary-only steps named; the gate list; rollback per surface plus the cannot-undo list; the human section with lead times; and the parallel split with the critical-path estimate. Write the same steps into `roadmap.json`, then run `scripts/parallel_brief.py` to generate the briefs and confirm no two concurrent workstreams claim a file.
