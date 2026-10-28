# Monetization: the model, the rails, and the store-policy line

Two separate questions, usually conflated. *What do we charge for, and how much* is a product and pricing decision. *How does the money physically arrive, from a customer in this country, on this platform* is an infrastructure and licensing decision — and it is the one that blocks launches, because a rail you cannot sign up for is not a rail.

## 1. Choose the model

Pick the one whose unit matches how the customer gets value, because that is what makes a price feel fair rather than arbitrary.

| Model | Fits when | Watch for |
|---|---|---|
| Subscription per seat | Value scales with team size; usage is steady | Seat-counting games; customers sharing logins |
| Subscription per workspace/tier | Value is access, not volume | Tier boundaries that punish your best users |
| Usage-based | Costs scale with usage and usage varies hugely | Bill shock; set caps and alerts, and show spend live |
| Per transaction, flat fee | You sit inside a payment the customer already makes | Low-value transactions where the flat fee dominates |
| Take rate (%) | Marketplace where your value scales with order value | Sellers with high-value items will route around you |
| Freemium | The free tier produces something you need — content, network density, data | The free tier must have a real cost ceiling |
| Free, monetized adjacently | The core loop needs volume to work at all | Name the adjacent revenue now, or this is a hobby |

A flat per-transaction fee instead of a percentage is worth considering whenever transaction values vary widely: it is radically cheaper for the customer's best sales, which is exactly where percentage pricing feels most punitive. PXI charges $0.99 per paid ticket at any price, so a $100 ticket costs the same as a $10 one — the pitch is a sentence, and the customers with the most to lose are the ones it wins. The trade is that you give up upside on high-value volume, so check the math against your Phase 2 numbers rather than copying the shape.

Then decide: the free tier's exact limits and what it costs you; whether there is an annual discount and what it does to cash (annual up front is the cheapest capital a bootstrapped company can get); who gets grandfathered when prices change; and the one thing a customer must never hit a paywall on, because it is load-bearing for the loop.

## 2. The store-policy line

Before choosing rails, draw this line, because it constrains everything after it.

Digital goods and services consumed in an app generally must use the platform's in-app purchase. Physical goods, real-world services and person-to-person payments generally may use your own processor. The carve-outs — external purchase links, alternative billing, reader apps, regional programmes — differ by storefront, change by court order and regulation, and are mid-transition on both platforms as of late 2026. Apple's US external-link position and Google's billing-choice programme have both moved within the last year, and secondary sources contradict each other on the current rate.

**First, work out which side of the line you are on**, because most products never owe a store commission at all and plans routinely budget for one they don't owe — or, worse, miss one they do.

The test is where the thing being bought is consumed. A ticket to a real event, a haircut appointment, a delivered meal, a ride, a physical product, or money sent to another person is consumed in the world, so the store takes nothing and you use your own processor. A subscription, a feature unlock, extra storage, credits, cosmetics, a boost, or anything that only exists inside the app is consumed in the app, so in-app purchase applies with its commission.

The grey cases are where the money actually gets lost, so resolve each one explicitly against the current guidelines rather than by analogy:

- **Credits or balances spent inside the app**, even when they ultimately buy something real. Ad credits, message or email credits, and promotional spend bought in-app have historically been treated as in-app purchases on iOS, and a platform fee on top of advertising spend changes the margin on that line completely.
- **Promoting or boosting your own content** from inside the app.
- **A paid membership or subscription that unlocks in-app features**, even on a product whose main revenue is real-world.
- **B2B purchases made by a business user** inside a consumer app binary — being a professional tool does not by itself move you across the line.
- **Hybrid flows**, where a free real-world transaction is the hook and the subscription is the revenue.

Note that the line is about the *commission*, not about whether you may take payment at all; and that a product can sit on both sides at once, with ticket sales outside in-app purchase and a premium tier inside it. Write the classification per revenue line, not per product.

So: **look up the rule for your category, your platform and your storefront, write the citation and the date, and model the economics with the commission included at the rate you verified.** Mark it as a number to re-verify before launch, and have the plan say what changes if it moves — a business whose margin only works at 0% commission has a single point of failure in someone else's legal department.

Whatever the rule permits, the web checkout is usually the better-margin path, so plan it regardless and decide separately how, or whether, the app may point at it.

## 3. Rails, by corridor

The pattern across every non-card rail is the same, and it is the thing plans get wrong: **most local payment methods require a locally registered business entity, a local bank account and local KYC.** Not an API key. This is a company-formation question wearing an integration costume, and it is why "we'll add mobile money" slips by months.

For each corridor you intend to serve, answer these before committing, from the provider's own docs:

1. Who may sign up — local entity required, or can a foreign company onboard?
2. What KYC documents, and how long does approval actually take?
3. Settlement currency, and can you hold or must you convert?
4. Payout timing and minimum, and to which kind of account?
5. Fees, including FX spread, which is often larger than the headline rate
6. Refunds, chargebacks and disputes — mobile money often has no chargeback, which shifts fraud risk onto you
7. Sandbox availability, and what going live additionally requires
8. Whether an aggregator covers it well enough to skip direct integration

**Cards and wallets, US and EU.** A mainstream processor with a connected-account model is the default: it keeps you out of money transmission (Phase 3), handles 3-D Secure and SCA, and brings Apple Pay and Google Pay, which materially lift mobile conversion and should be on from day one. Add the local bank rails that matter per market (ACH in the US; SEPA and iDEAL in Europe) for high-value or recurring payments, where card fees hurt. PayPal is worth adding where its brand trust converts an audience that will not enter a card; Cash App Pay reaches a US demographic that skews younger and is a genuine conversion add in consumer contexts. Verify current availability and terms per provider.

**Africa.** Treat each country as its own project, because the rails are national.
- *Kenya:* M-Pesa dominates, integrated through Safaricom's Daraja API — developer portal account, sandbox credentials, then a live Paybill or Till number for production, which requires the business registration step that is the real gate. Expect the document list to have changed; read Safaricom's current page.
- *Ethiopia:* Telebirr is the dominant wallet. Access runs through Ethio Telecom's merchant process and effectively assumes a locally registered business and a local bank relationship. Verify directly; third-party summaries of this one are thin and often out of date.
- *Nigeria, Ghana, South Africa:* Paystack and Flutterwave are the practical aggregators, each with dashboard signup followed by business KYC before live transactions, and each covering several countries including mobile money. An aggregator is usually the right first move: one integration, several corridors, and they have already solved the local licensing you have not.
- Across the region: mobile money is the primary method, not a fallback; design the checkout for it rather than bolting it on. Plan for no-chargeback semantics, for payment confirmation arriving asynchronously by webhook or callback, and for users who abandon and retry — idempotency matters more here, not less.

**Elsewhere.** UPI in India, PIX in Brazil, Mercado Pago across LatAm, and regional wallets in Southeast Asia each follow the same local-entity pattern. Check whether your primary processor already supports the ones you need before adding a second provider: each additional provider is a reconciliation surface, a webhook handler, a dispute flow and a set of edge cases, and two rails you support properly beat five you support badly.

**Sequence the rails.** Launch with the one that covers the most of your Phase 2 revenue, add the second when the first is clean, and let a corridor's volume justify its integration. Write that order in the roadmap, with the entity or KYC work as a human step — because that step has a lead time and nothing downstream of it can start.

## 4. Taxes, payouts and the unglamorous parts

- **Sales tax, VAT and GST.** Digital services are taxable in many places, with registration thresholds; SaaS is treated unusually in some US states, Texas among them, so verify your own state rather than assuming. Use the processor's tax product unless you have a reason not to — the alternative is a compliance project.
- **Marketplace facilitator rules** may make you responsible for collecting on sellers' behalf. This follows from the Phase 3 decision about whether you hold funds.
- **Payouts.** Schedule, minimum, instant-payout fees, and what happens to a seller who fails KYC after making sales. Write that last case down; it will happen, and without a plan it becomes a support emergency with someone else's money in the middle.
- **Reporting.** 1099-K or local equivalents if you pay people.
- **Refunds, chargebacks, fraud.** Policy, who absorbs the loss, the dispute evidence you keep automatically, and the rate at which you would intervene. Set velocity limits on anything that moves money.
- **Dunning.** Failed-payment retry schedule, the emails, and the grace period before access is cut. Involuntary churn is the cheapest churn to fix and the most often ignored.
- **Presentation.** Show currency explicitly, round to local conventions, state whether tax is included, and make the fee breakdown visible before the final step. Surprise fees at the last screen are among the largest measurable sources of checkout abandonment.

## Output of this phase

Write `plan/07-monetization.md` with: the model with its unit and why; the free-tier limits and their cost; the full price list; the store-policy line with its dated citation and what changes if it moves; the rails table, per corridor, with the eight questions answered and the launch order; the entity and KYC lead-time steps; tax and payout decisions; and the dunning and dispute policies. Record the price and the rail order in `decisions.json`.
