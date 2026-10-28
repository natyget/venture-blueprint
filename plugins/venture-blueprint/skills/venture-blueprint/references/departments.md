# Departments: planning the company, not just the product

A product plan answers "what do we build". A company also has to sell it, support it, keep it safe, keep the books, hire, and survive its own growth — and each of those is a department with its own expertise. A one-person company still has every department; the founder just runs all of them, usually without noticing which hat is on, and usually discovers a missing one when it fails.

This phase walks through all sixteen departments in `templates/departments.json`, once, in Stage 2 — after the ecosystem phase (which decides what you build versus rent) and before the red team. It produces `plan/departments.md`, and it feeds the hires and tools it finds into `assumptions.json`, so the financial model includes the real cost of running the company rather than only the cost of building the product.

## What an expert actually adds: foresight

The value of a seasoned head of support, finance or security is rarely knowledge you couldn't look up. It's that they have watched companies grow and know **what breaks at 1,000 customers that looked fine at 10** — the support inbox nobody owns, the sales tax nobody registered for, the production database everyone can read, the contractor who never signed over the code.

So for each department, take the seat deliberately:

> You are the head of this department at this company two stages from now — at roughly ten times today's customers. Looking back at how it was set up, what do you wish had been decided on day one, and what was a waste of time to set up early?

Write from that seat. Both halves of the question matter. The first finds the things that are cheap now and expensive later. The second stops the plan from building enterprise process for a company of one — which is its own failure, and the one experts are best at spotting.

Then work through that department's `asks` from `departments.json` as that expert would: specifically, for this business, with its preferences from `paths.md` as constraints.

## What to write for each department

One section per department, headed with its id and name. Each section has these parts — `check_plan.py` checks for each label:

- **What breaks first** — the specific failure this expert foresees for *this* company, and roughly when (at what customer count, revenue or date). Not "support will get busy" but "at around 300 organizers the founder is answering 40 payout questions a week, all about the same two-day delay".
- **Day one** — what to set up before launch so it is not a retrofit, and what to deliberately *not* set up yet. Keep it short; most departments need very little on day one.
- **Stack** — the concrete tools or services, each with: build, rent or absorb (consistent with `08-ecosystem.md`); the tier you start on and its monthly cost; the tier at scale and its cost; whether you can export your data (trap T21); and a source with the date you read the pricing page. Name real products — this is the "for real" part — and give the rejected alternative for anything that costs more than a small monthly amount. Never quote a price from memory.
- **Who, by stage** — who does the work at launch, and what triggers the next change: founder → agent → contractor → part-time → full-time hire, each with its trigger (a customer count, revenue, or volume of work) and its monthly cost. These triggers become step costs in `assumptions.json`.
- **Agents can run** — the recurring work in this department that an AI agent can do today, and the human check on its output. For a bootstrapped company this is often the difference between needing a hire at 300 customers and at 3,000. Be honest about what is not ready to automate.
- **KPIs** — one to three numbers this department is judged on, each with a target. Fewer is better.

**Not applicable** is a valid answer for a whole department — Sales for a purely self-serve consumer product, International for a single-city launch — but it needs a reason, and it needs a trigger: "Not applicable until we sell to businesses; revisit if any customer asks for an invoice or a contract." A department marked not applicable with no trigger is how a gap stays hidden.

## Cross-functional review

Departments disagree, and the disagreements are where plans fail quietly. After all sixteen sections, write a **Cross-functional review**: a short table of the real tensions in this plan and how each is resolved. Typical ones:

| Tension | Between | Resolution |
|---|---|---|
| More tracking for attribution vs data minimisation | Marketing, Legal | Collect click IDs only with consent, keep them only in store links |
| Fast releases vs app-store review time | Engineering, Product | Ship logic over the air where allowed; keep native changes to a monthly train |
| Discounts to close deals vs margin | Sales, Finance | Discount ceiling of X%, founder approval above it |
| Open signup for growth vs abuse | Marketing, Trust and safety | Rate limits by account age; verification before the first payout |

Each resolution should either become a decision in `decisions.json` or a constraint other phases respect.

## Feed it back

- Every tool cost and every hire becomes a line in `assumptions.json` — hires as fixed costs with `steps` at their trigger, tools as fixed costs with their tier steps. Then rerun `model.py`. If the plan only works without the hires the departments say it needs, that is the most important finding in the document, and the business plan has to say so.
- Every day-one item that is real work becomes a step in the build stage.
- The business plan gets an **Organization** section built from this: who does what at launch, the hiring sequence and its triggers, and the monthly cost of the team at each stage.

## Depth and cost

Sixteen departments sounds like a lot, and for a small company most sections are short — a few lines each, several marked not applicable with a trigger. The depth should follow the business: a marketplace needs real work in Operations and Trust and safety; a B2B tool in Sales and Security; a consumer social app in Trust and safety and Support.

If the session can run subagents and the founder wants more depth on particular departments, those departments can be researched in parallel — each with the plan, the preferences and its own section of `departments.json` as its brief — and their sections merged afterwards. Do this only when the founder asks for the depth; done inline, the sweep costs far less.

## Output of this phase

`plan/departments.md` with all sixteen sections and the cross-functional review; new fixed costs and step costs in `assumptions.json`, with `model.py` rerun; and the Organization section of the business plan. Check with `check_plan.py --stage plan`.
