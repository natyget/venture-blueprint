# Architecture: choosing the stack, and the budgets that keep it clean

The goal is a stack that one small team can hold in their head, that costs little at 1,000 users and does not collapse at 1,000,000, and whose every choice has a written reason. Software stays clean because budgets are set and enforced, not because anyone intends to keep it clean.

## 1. Decide layer by layer, against named alternatives

For each layer, write a short decision with its rejected options. The rejected list is the valuable part: it is what stops the same debate reopening in month four, and it is what tells a future reader whether the reasoning still holds.

```
Layer:      Mobile client
Chosen:     Native (Swift/SwiftUI + Kotlin/Compose)
Rejected:   React Native — one codebase, but camera, background upload and
            photo pipeline all need native modules anyway, so the saving is
            partly illusory and debugging crosses the bridge
            Flutter — good performance, but platform-review friction on
            camera/photo permissions and a smaller hiring pool here
Because:    The core loop is camera → background upload → gallery. That is the
            part users judge, and it is the part a bridge taxes most
Costs us:   Two codebases; features land ~1.4× slower after the shared API
Revisit if: The roadmap shifts to form-heavy surfaces where the loop doesn't dominate
```

Layers to cover: client(s), API, database, cache, queue and background jobs, file and media storage, search, auth and identity, payments, email and SMS, push, analytics and warehouse, observability, CI/CD and release, feature flags, infrastructure and hosting, model/inference if any, and the admin or operator console (Phase 8 decides its scope; it is a real layer, not an afterthought).

## 2. The native rule

Native is the default for mobile, and the reason is cost, not taste: better performance per battery-hour, fewer platform-review surprises, direct access to new OS capabilities on the day they ship, and no framework upgrade treadmill between you and the OS. It matters most where the user is judging responsiveness — camera, scrolling media, maps, gestures, background work.

Native is a preference, not a rule. Choose otherwise when the work is mostly forms, lists and text, when the team is one person and shipping speed decides whether the company exists, or when the platform surface is genuinely thin. When you do, write what it buys and what it costs, so the trade stays visible and the decision stays reversible.

The same logic applies to the server: prefer the platform's own primitives over a dependency, and a dependency over a service, and a service over building a service. Each step adds something you must understand and cannot fix.

## 3. Budgets

Budgets are what "clean and not bloated" means in practice. Set them now, put them in CI, and let the build fail. A budget nobody enforces is a wish.

- **Dependency budget.** A number for direct dependencies per package, and a rule for adding one: it must save more than a week of work, be maintained, and have a stated removal path. Audit transitive weight, not just the direct count.
- **Bundle and binary budget.** Web: initial JS over the wire. Mobile: download size per platform, which directly affects install conversion.
- **Performance budget.** p95 for the three interactions that define the product — not an average, and not every endpoint. Cold start, the main list render, the core action.
- **Query budget.** Max queries per request and a hard "no N+1 in a list endpoint" rule, checked in tests.
- **Cost budget.** Dollars per 1,000 active users per month, so a regression in cost is as visible as one in latency.
- **Build budget.** CI minutes and wall-clock to green, because a slow pipeline silently stops people running tests.

## 4. Cost and behaviour at three scales

Model 1k, 100k and 1M monthly active users. For each: compute, database, storage and egress, the per-message and per-inference costs, and the total. Egress and media storage are the two that surprise people, and media-heavy products should model them per user per month explicitly.

At each scale, also name **what breaks first** and what the fix is. A plan that says "at 100k, the single Postgres writer is the ceiling; the fix is read replicas for the feed query, then partition the events table by month" is worth more than one claiming it scales. State the ceiling you are deliberately accepting — you should accept one, because building past it early is waste.

## 5. Data model and contracts

Sketch the core entities and their relationships, then write down the parts that are hard to change later, because these are the decisions that calcify:

- **Identity**: what a user is, whether accounts can merge, what a guest can do, how deletion cascades (the compliance register needs this to be real).
- **Tenancy**: whether data is scoped per organization, and whether that boundary is enforced in the database or only in code. Retrofitting tenancy is a rewrite.
- **Money**: integer minor units, currency on every amount, immutable ledger rows rather than mutable balances, idempotency keys on anything that charges.
- **Time**: UTC in storage, the event's own timezone stored alongside when local time matters.
- **Enums and vocabularies**: the actual allowed values for status, category, city, role. Write them once, in one place, as the shared contract — free text where an enum belongs is a reporting problem that compounds forever.
- **IDs**: shape, whether they are guessable, and whether they appear in URLs.

**The shared contract is an artifact, not a convention.** Types, API schema, event taxonomy, enums and tokens live in one place that every consumer imports, and every consumer carries a test that fails when it drifts. This is the mechanism that makes Phase 9's parallel overnight build safe: sessions can work simultaneously because the contract is already fixed and drift is a test failure rather than a merge conflict discovered at the end.

## 6. Failure modes

For each external dependency — payments, push, email, SMS, storage, the model API, the map tiles, each store — write what happens when it is down or slow, and what the user sees. Then write the three cheap protections and whether you are taking them: a timeout with a user-visible fallback, idempotency on retries, and a queue so a failure defers rather than loses. Also write what happens when *you* are down: the status page, the thing users can still do, and how data written during a partial outage reconciles.

## 7. Security and the operational floor

Not a Phase 10 audit — these are architecture decisions:

- Secrets in a manager, never in the repo or a build config, with rotation documented
- Authorization checked at the data layer, not only in the route, so a new endpoint cannot leak by omission
- Rate limits on auth, invite, upload and anything that sends or costs money
- Signed, verifiable tokens for anything a user presents at a door or a gate (PXI signs every ticket so it cannot be edited, and flags one already scanned — the security property is in the token, not in the scanner)
- Encryption at rest and in transit, with the specific fields that need application-level encryption named
- Backups with a stated recovery point and recovery time objective, and one restore actually tested — an untested backup is a belief
- Audit log for anything an operator can do to a user's data, which the compliance register will ask for
- Dependency and secret scanning in CI

## Output of this phase

Write `plan/04-architecture.md` with: the layer decisions and their rejected alternatives; the native-rule statement; the budgets with the CI check that enforces each; the three-scale cost model with what breaks first; the data model with the hard-to-change decisions; the shared-contract artifact and its drift tests; failure modes per dependency; and the security floor. Put every choice in `decisions.json` with its rejected alternatives — the validator checks that each layer has them.
