# The trap sweep: the questions that are cheap now and expensive later

This is not a phase. It is a sweep you run three times — at Phase 3 (compliance), at Phase 7 (monetization) and again in Phase 10 (red team) — because the answers change as the product takes shape, and because each one is a question whose cost is near zero while the plan is still text.

## Why a fixed list

Every trap in `templates/traps.json` has the same shape: **a third party's rule quietly decides your margin or your legality, and nothing in your own code tells you about it.** Two worked examples, both real:

- A nightlife app sells event tickets, so it owes no store commission — tickets are consumed in the world. But the same app sells *ad credits* to organizers, and credits spent inside the app have historically been treated as in-app purchases. Nobody notices until a 15–30% cut lands on advertising spend, which is a line whose margin cannot absorb it. The fix costs nothing if you see it early: sell that line on the web only. It costs a re-architecture and a renegotiated price if you see it after launch.
- A state passes a law requiring app stores to verify ages. It reads like a problem for Apple and Google. It also binds *developers* — consume the store's age bracket, honour parental consent, notify stores before significant changes — on staggered per-state deadlines, one of them with no cure period. Nothing in your repo mentions it.

Neither is discoverable by thinking harder about your own product. Both are discoverable by asking a fixed question out loud. That is the whole mechanism: **judgement finds the traps you can imagine, and a checklist finds the ones you can't.** So the list is fixed, and the validator refuses a plan that leaves one unanswered.

## How to run it

Answer every row of `traps.csv`. There are exactly two acceptable answers:

- **`answered`** — with the finding, a primary source, and the date you read it. If it needs work, name the roadmap step that does it.
- **`n/a`** — with the *reason* it does not apply. "We have no mobile app, so no storefront rule attaches" is a real answer. A blank is not, and neither is `n/a` with no reason, because that is indistinguishable from not having looked.

A few rules that keep it honest:

**Answer per revenue line, not per product.** T01 and T02 are the ones people get wrong by answering once. A product with ticket sales, ad credits and a subscription has three classifications, and they differ.

**Re-ask after the product changes.** Adding one feature can flip an answer — a free product that adds a subscription acquires a storefront classification; a product that adds photo tagging acquires T11; a product that adds a second country acquires T08, T15 and T17 at once. That is why the sweep runs three times rather than once.

**Litigation posture is part of the answer.** "In force, but under appeal" is different from "in force". Write which.

**A trap that needs work becomes a step.** An answered row with no step and no "nothing to do" note is a finding you will forget. The register is the memory.

**Date everything.** A trap answer older than about 90 days is re-checked before the build, and `check_plan.py` warns you. Platform rules and statutes move faster than most roadmaps.

## The categories

| Category | What it catches |
|---|---|
| `platform` | Store rules deciding your margin, and deadlines you do not control |
| `users` | Obligations that attach because of *who signs up*, not what you built |
| `money` | Licensing, tax and loss-bearing consequences of the money's shape |
| `dependency` | Suppliers, cliffs, licences and lock-in |
| `identity` | The name, before it is in a store listing and ten thousand links |
| `irreversible` | What cannot be undone once run |
| `measurement` | Spend you cannot attribute, and so cannot scale or cut |

## Extending it

The list is a floor, not a ceiling. When a plan's own research turns up a trap specific to its vertical — a licence you cannot get without a physical premises, a platform whose API terms forbid your core use, a certification with a twelve-month lead time — add a row with a project-specific id (`P01`, `P02`) and treat it exactly the same way. `check_plan.py` checks that every canonical trap is present and every row is complete, so extra rows are welcome and are held to the same standard.

If you find yourself answering the same new trap across several plans, it belongs in `templates/traps.json` permanently.

## Output

`traps.csv`, complete, with every canonical id present and every row either answered-with-source or n/a-with-reason. Summarise the ones that changed a decision in `plan/03-compliance.md` and `plan/07-monetization.md`, and list the ones that became roadmap steps. The rows that turned out to be nothing are still worth keeping, because next quarter someone will ask whether you checked.
