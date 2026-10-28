# Economics: bottom-up sizing, unit economics, and whether this can bootstrap

The purpose of this phase is not a number to put in a deck. It is to find out what the business must charge, how many customers it needs, and whether it reaches that before the money runs out — early enough that the answer can still change the product.

## 1. Size from the bottom up

Top-down sizing ("the market is $40B, we'll take 1%") is unfalsifiable and therefore useless. It also tells you nothing about what to build. Build the number from units you could list by name.

Write the chain explicitly, one line per step, each with a source:

```
Countable universe:   4,100 licensed venues in TX, NY, MA          [source, date]
  × qualifies:        ~35% run a ticketed event most weeks          [how you know — sample, survey, or UNVERIFIED]
  = addressable:      ~1,435
  × reachable year 1: 3 cities, walk-in + organizer referral        → ~180 within reach
  × conversion:       20% of reached, from the first 20 conversations
  = customers:        ~36
  × revenue each:     $0.99/paid ticket × ~900 tickets/yr = ~$890
  = year 1 revenue:   ~$32,000
```

Each multiplier is an assumption with a name, which means each can be challenged, measured and improved. Mark any you cannot source as `UNVERIFIED:` and say how it could be tested cheaply — usually by counting a sample of 20 by hand.

Then state the **ceiling**: if this wedge worked perfectly in its narrow market, what is the revenue? If the honest ceiling is below what the operator needs, say so now. That is not a reason to abandon the idea — it is the reason to plan the expansion from Phase 1 as part of the thesis, or to pick a different wedge.

## 2. Unit economics

Define the unit first and write it down, because most arguments about these numbers are actually disagreements about the unit. For a marketplace, decide whether the unit is the buyer, the seller or the transaction — and if the seller brings the buyers, the seller is the unit.

For one unit, over its life:

- **Revenue per unit per month**, and what makes it go up (usage, seats, tiers, take rate on growing volume)
- **Gross margin**: revenue minus the costs that scale with the unit — payment processing, infrastructure per user, model inference, storage and egress, SMS and email, support time, store commission. Store commission is a cost of goods, not a marketing expense, and plans routinely forget it
- **Retention**: monthly logo and revenue retention, with the basis for the estimate. Where there is no data, use the closest public benchmark, cite it, and mark it `UNVERIFIED`
- **Lifetime value**: gross-margin dollars per month ÷ monthly churn. Do not use revenue LTV; it flatters everything
- **CAC**, per channel, including the channels that are not ads: content production cost, sales time at a loaded hourly rate, referral payouts, app store ad cost
- **Payback period**: CAC ÷ monthly gross-margin dollars. For a bootstrapped business this is the number that matters most, because it is the speed limit on growth without outside money. Under 3 months you can grow from revenue; past 12 you need capital or a different channel

Present it as a table with a **sensitivity row**: recompute at half the conversion rate, double the CAC and 1.5× the churn. If the business only works in the optimistic column, say that in one sentence — it is the most important sentence in the document.

## 3. The cost base

List fixed monthly costs that exist whether or not anyone signs up: infrastructure floor, developer program fees, domains, email and SMS minimums, model API floors, legal and accounting, entity and registered-agent fees, insurance, the operator's own minimum draw. Then state three cost points — at 1k, 100k and 1M users — alongside the architecture's numbers from Phase 4, so the two stay consistent. If they disagree, one is wrong, and it is usually this one.

Flag anything with a **cliff**: a free tier that ends, a per-seat tool that steps at 10 users, a platform fee band, a compliance obligation that attaches above a revenue or user threshold (several state privacy laws work this way). Cliffs are the costs that surprise people, because they are invisible until crossed.

## 4. The bootstrap test

For a business that must pay for itself, answer these four in writing:

1. **Cash to first dollar.** What must be spent before the first paying customer — entity, developer accounts, design, hosting, any licence or deposit. A number, with the line items.
2. **Time to first dollar.** Working weeks until a customer could pay, given the operator's real hours per week. Measure from the roadmap in Phase 9, not from optimism.
3. **Months to cover the cost base.** At the modelled growth rate, when does revenue exceed fixed costs?
4. **Does (1) + (3) fit inside runway?** If not, the plan changes now, not later. The usual fixes, in order of preference: narrow the wedge so it ships sooner; charge earlier (presell, deposits, annual up front); take a higher-margin adjacent job first to fund the main one; cut the fixed cost base; or accept that this needs outside money and plan for that instead.

State which fix you took.

## 5. Pricing inputs

This phase produces the *constraints* on price; Phase 7 sets the actual model.

- **Floor**: unit cost ÷ target gross margin.
- **Reference price**: what they pay today for the alternative, quoted with a source. This anchors the customer's judgement far more than your cost does.
- **Value basis**: the money or time the customer saves or earns, computed from their numbers, not yours. If you can state it as "you keep $690 more on a 400-ticket event", you have a price.
- **Ceiling**: the point where they would rather keep doing it manually.

Price inside that band, closer to the value basis than to the floor. Note the switching cost you must overcome — data migration, retraining, contract timing — because that is paid in product work or in discount, and it belongs in the roadmap either way.

## Run the numbers through the model

Write every assumption from this phase into `plan/assumptions.json` — customers, each revenue line, variable and fixed costs, with a source or an `UNVERIFIED` marker on each — and run `scripts/model.py`. It produces the scenarios, break-even month, cash low point, unit economics and the cost-at-scale table in `financials.md`. Quote those figures; do not compute them yourself. If a number here and a number in `financials.md` disagree, the model is right and the prose is stale. `templates/assumptions.example.json` shows the shape, including step costs for the cliffs in §3.

## Output of this phase

Write `plan/02-economics.md` with: the bottom-up chain with sources; the unit economics table with its sensitivity row; the cost base at three scales with cliffs flagged; the bootstrap test and the fix you chose; and the pricing band. Put the key numbers in `decisions.json` so later phases and the validator can see them.
