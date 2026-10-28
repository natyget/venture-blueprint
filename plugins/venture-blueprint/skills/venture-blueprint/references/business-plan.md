# The business plan: assembling one readable document

Write this last in Stage 2, after the phase documents and the financial model exist. It is a synthesis, not new research: every number in it traces to a phase document or to `financials.md`, and every claim keeps the source it had there. If writing a section reveals a gap, go back and fill the phase document first — the business plan should never be the only place a fact lives.

It is the document the founder will actually send to a partner, an investor, an early hire or a contractor. So it has to work for someone with three minutes (the summary) and for someone with an hour (the rest), and it has to read as written by a person who knows the business — not as a template with the blanks filled in.

## Structure

Use these sections in this order. `check_plan.py --stage plan` checks that each is present.

### 1. Executive summary

One page. Someone who reads only this should be able to repeat the business back accurately. Cover: the problem and who has it, what you're building, why now, why you, how it makes money, the base-case numbers (from the model), what you're asking for or deciding next. Write it last.

### 2. Concept

One paragraph a stranger understands on first read. What it is, who it's for, and the one thing it does better than what they use today. No slogans.

### 3. Vision, mission and principles

These three are the most cliché-prone sections in any business document, so hold them to a specific standard.

- **Vision**: what is true about the world in five to ten years if this works. Concrete enough to be wrong. "Every independent organizer in North America keeps the audience they built, instead of renting it from a ticketing platform" can be wrong; "empowering creators everywhere" cannot, which is why it says nothing.
- **Mission**: what you do, for whom, and how — the daily work in one sentence. It should rule things out. If a competitor could paste their own name into it unchanged, rewrite it.
- **Principles**: the commitments that shape decisions, written as rules you'd actually follow even when they cost you. These are usually the hard nos from `paths.md` and the obligations you designed away: "We never hold customer money." "Credits are sold on the web, not in the app." "We don't sell or rent user data." Three to six is plenty.

Test every line against the banned list: no *elevate, seamless, unlock, game-changer, revolutionize, effortless, empower, next-generation, cutting-edge, world-class, best-in-class*, no "the X, the Y, the Z" triads, no "not just X, it's Y". `check_plan.py` warns when it finds them. They are the words that make a reader stop trusting the rest.

### 4. Problem and evidence

The pain in customers' own words, quoted, with sources and dates. What they do today instead and what it costs them. Why the current options fail them — structurally, not just "they're bad". Why now.

### 5. Customer personas

Two to four, built from the evidence you gathered, not imagined. A persona is useful only if it changes a decision — what you build, how you price, where you find them, what you say. If two personas would lead to the same decisions, merge them.

For each:

| Field | What goes in it |
|---|---|
| Label | A role, not an invented name: "Independent organizer running 2–6 events a month". A first name is fine if it helps, but never a made-up full identity |
| Situation | Their context, numbers where you have them (events a month, team size, revenue band) |
| Job to be done | What they're trying to get done, in their terms |
| Today's alternative | What they use now, and what it costs in money and time |
| Trigger to switch | The moment they start looking — a price rise, a bad night, a new law, growth past a threshold |
| Objections | What stops them buying, in their words |
| What they'd pay | And the evidence for it |
| Where to reach them | Specific places, not "social media" |
| In their words | One or two real quotes, with source and date |

Then an **anti-persona**: who you deliberately do not serve, and why. It saves the team from building for the wrong customer, and it's often more decision-useful than another persona.

Never fabricate quotes. A persona with no real quote is marked as a hypothesis to test, with the test.

### 6. Market

Bottom-up sizing from `02-economics.md`: the chain from a countable universe to reachable customers to revenue, each multiplier sourced. If you include TAM/SAM/SOM, build each one bottom-up and label how. Then the forces making this the right moment, and the ceiling of the wedge alone versus with the expansion.

### 7. Competitor matrix

A single table, read across, so the gap is visible at a glance.

- **Rows**: each competitor, *including* "do nothing / spreadsheet / group chat" — often the real competitor — and your product as the last row.
- **Columns**: the attributes that decide the persona's purchase, not a generic feature list. Usually: pricing model, total cost at a typical customer's volume (computed the same way for every row, with the formula noted), the capabilities that matter to this persona, how they acquire customers, their top complaint in users' words, and their structural weakness.
- Prefer facts and numbers over ✓ and ✗. A ✓ hides whether the feature is good; "$1,086 on a 400-ticket night" does not.
- Source every cell, or mark it `UNVERIFIED`. Date the table — competitor pricing changes.

Then the **positioning map** on the two axes from `01-wedge.md` that actually matter in this market, with each competitor placed and the empty region named — and one sentence on why that region is empty (hard, small, or unreached).

Naming competitors is fine in this internal document. If the plan will be shared publicly, or any of it reused in marketing, describe them by how they work instead.

### 8. Paths considered

A short version of `paths.md`: the options, the one chosen, why, and the founder preferences that shaped it. Readers trust a decision more when they can see what it beat.

### 9. Product

The MVP: what's in it, and explicitly what isn't and why. The core loop in a few steps. What makes it defensible (the data, the network, the closed loop from `08-ecosystem.md`). The expansion after the wedge.

### 10. Business model and pricing

The model and its unit, the price list, the free tier and its cost, the payment rails by corridor and their order, and the store-policy line per revenue line from `07-monetization.md`.

### 11. Financials

From `financials.md`, which `scripts/model.py` produces. Do not compute any figure by hand.

- **Scenarios**: conservative, base and optimistic — customers, monthly revenue, gross margin, monthly net and cash at months 6, 12, 24 and 36.
- **How cost scales and how revenue scales**: the cost-at-scale table — revenue, cost and margin per month at several customer counts — with the step costs (cliffs) called out.
- **Break-even month and cash low point** for each scenario. The cash low point is the number a bootstrapped founder needs most, because it is how much money the plan actually requires.
- **Unit economics**: revenue and gross margin per customer, CAC, payback, LTV and LTV:CAC.
- **The drivers**: the two or three assumptions the outcome depends on most, and what happens if each is wrong.
- **Assumptions**: every input with its source, and the unverified ones listed.

### 12. Go-to-market

The first fifty customers by name or place, then the channel that scales, the loop and its arithmetic, and the launch sequence from `06-growth.md`.

### 13. Compliance and risk

The obligations that apply and how each is met or designed away, the trap-sweep findings that changed a decision, the rows needing a lawyer, the concentration risks and the kill scenarios from `10-red-team.md`. State plainly that this is not legal advice.

### 14. Statement of work

What will be built, by whom, by when, and how you'll know it's done. Useful whether the builder is the founder, a set of Claude sessions, or a contractor — and if it's a contractor, this section is what you'd hand them.

- **Scope**: in scope, and explicitly out of scope.
- **Deliverables**: each with an acceptance criterion someone could check without asking you ("Organizers can create a paid event and receive payouts to their own account; verified by a test purchase in production").
- **Milestones and timeline**: stage-gated, with the metric that unlocks the next milestone. Relative dates (week 1–2, week 3–6) unless the founder has fixed ones.
- **Roles**: who does what — founder, agent sessions, contractors, counsel, accountant.
- **Dependencies and human steps**: entity, bank, KYC, store accounts, legal review — with their lead times, because these gate everything.
- **Budget**: from the model — cash to first dollar and the cash low point.
- **Assumptions and exclusions**: what the plan takes as given, and what it deliberately doesn't cover.
- **Change control**: how scope changes get decided, so the plan doesn't drift by accretion.

### 15. Milestones and metrics

For each stage of the company — validation, launch, traction, scale — the one or two metrics that matter and the target that means "move to the next stage". Make them falsifiable: "20 organizers with at least one paid event in 60 days", not "strong early traction".

### 16. What is unverified and what's next

Every `UNVERIFIED` claim and who can settle it; what you could not test and why; the three decisions most worth challenging; and the next action.

### Appendix

Links to the phase documents and the data files.

## Writing it

- **Write for a reader who doesn't know the founder.** Define nothing as obvious.
- **Keep the numbers identical everywhere.** The summary, the financials and the statement of work must quote the same figures — all from `financials.md`. A reader who finds two different break-even months stops trusting the document.
- **Plain words over impressive ones.** Use the same plain-language standard as the rest of the skill.
- **Length follows substance.** A simple business can have a short plan. Don't pad sections to look complete; a short honest section beats a long generic one.
- **Offer to publish it** once `check_plan.py --stage plan` passes, if the session can produce a shareable document.
