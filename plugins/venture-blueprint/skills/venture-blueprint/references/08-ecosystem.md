# Ecosystem: the value chain, what to own, and the tools you run the company with

Two questions here. Where in the chain between the customer's problem and the money does this company sit, and which neighbouring steps should it absorb? And: what does the operator need in order to run the thing daily without a stack of subscriptions and a spreadsheet?

## 1. Map the value chain

List every step between the customer first having the problem and the money arriving, including the steps you have no intention of touching. Then mark, for each: who owns it today, what it costs (to the customer or to you), and whether it is a place where value leaks.

For an events product the chain runs roughly: the guest decides to go out → finds something → trusts the organizer enough to buy → pays → gets a ticket → gets in the door → experiences the night → the photos exist → the photos get shared → the organizer learns what sold → the organizer sells the next one. An events company that only does the "pays" step is a payment form. PXI's shape comes from absorbing discovery, the door, the camera, the sharing and the organizer's analytics — so the chain closes on itself and the photos from one night sell the next one.

Closing the loop is the point. Ask explicitly: **does the output of the last step feed the first step?** If it does, every cycle makes the product stronger and the data harder to copy. If it doesn't, you own a linear service and growth has to be bought every time.

## 2. Absorb, build, or rent

Absorb a neighbouring step only when one of these is true. Write which one, for each:

- **It takes a cut of your revenue.** A percentage of every transaction, paid forever, for work that is weeks of engineering, is the clearest case there is.
- **It is a dependency that can cut you off.** A single supplier of something essential, with their own strategy, who can change terms, rate-limit you, or become your competitor.
- **It produces data you cannot buy.** The photos from inside the room, the door scans, what actually sold the ticket. This is usually the most valuable reason and the least obvious one at the time.
- **It is the reason customers stay.** If the switching cost lives in a step someone else owns, your retention is rented.

Rent it when it is a commodity you touch monthly, it is somebody's genuine core competency and regulated (payment processing, identity verification, maps, email delivery, error tracking), or building it would not change what a customer experiences. Renting is the default and needs no justification; absorbing is the exception and needs one.

**The crossover math**, for anything over a few hundred dollars a month: build cost in engineering weeks at a loaded rate, plus ongoing maintenance at perhaps 15–20% of the build per year, against the rented cost at your 12-month and 36-month projected volume. Then add the parts that do not appear on either invoice: the dependency risk, the data you gain or forgo, and the integration surface you avoid or acquire. State the crossover month. If it is past 24 months, rent and move on.

Two failure modes to name in the plan. Building a worse version of a mature product to save a small bill is the common one. Renting the step that *is* your differentiation is the expensive one — and it tends to be invisible until a supplier raises prices or launches your product.

## 3. The operator console

The product everyone forgets to plan. Twelve tools with twelve logins, no shared vocabulary and no audit trail is not cheaper than one console; it is just un-budgeted. Decide which of these you need at launch, which at scale, and which you rent — and give the ones you build the same design system and the same measurement contract as the customer-facing product, because you will spend more hours in here than any customer does.

- **Ops console.** Find any user, organization or transaction and see everything about it. Impersonation for support, behind a permission and an audit log. The actions support must take without a developer: refund, resend, correct a typo, unlock, re-issue. Write that list from the support cases you expect, because every missing action becomes an engineer interrupted.
- **Moderation queue.** Required by both app stores for user-generated content, and required by Phase 3's legal obligations. Needs: a report path from every surface where content appears, a queue with triage, actions (hide, remove, warn, suspend, ban, escalate), appeal handling, an audit trail, the reporting pipeline for illegal content, and automated pre-screening for the obvious categories. Build it before launch, not after the first incident — the first incident is always sooner than planned and always worse without the tool.
- **Analytics and the warehouse.** Own the raw event stream. Rented dashboards answer the questions their vendor anticipated; your own warehouse answers the question you have at 2am about one cohort. The measurement contract from Phase 6 is what makes this usable.
- **Support inbox.** Where users reach you, with context from the ops console attached to the conversation. Rent the inbox; own the context.
- **Growth console.** Campaign tokens, custom product pages, the link and preview generator from Phase 5, referral codes and their attribution. Anything you will do weekly should be a form, not a deploy.
- **Content pipeline.** If growth depends on content, the pipeline that produces it is infrastructure. Templates, a render step, a review step, a calendar, and a ledger of what has already gone out so nothing repeats.
- **Feature flags and staged rollout.** The cheapest risk control available: ship behind a flag, enable for yourself, then a percentage, then everyone. It turns a bad release into a toggle instead of a hotfix.
- **Runbooks.** For each failure mode from Phase 4: how it looks, how to confirm, what to do, who to tell. Write them while you still remember why each dependency worries you.
- **CRM for the supply side**, if there is one. For a two-sided product the sellers are a sales pipeline, and tracking them in a spreadsheet stops working at about forty.

Keep each of these as small as its job. The point is to contain the work, not to build a platform — an internal tool that needs its own roadmap has become a liability.

## Output of this phase

Write `plan/08-ecosystem.md` with: the value-chain map with ownership and leaks marked; whether the loop closes; the absorb/build/rent decision per step with the reason and the crossover month; the operator console inventory split into launch / scale / rented; the moderation design; and the runbook list. Every "build" decision becomes a workstream in Phase 9. Record the decisions in `decisions.json`.
