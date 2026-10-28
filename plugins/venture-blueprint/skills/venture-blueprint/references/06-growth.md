# Growth: distribution, and the measurement contract that proves it works

Most products die of distribution, not of quality. This phase names the channels, builds the loop, and — the part usually skipped — defines the measurement before the build, so that six weeks later you can tell which channel worked instead of arguing about it.

## 1. Pick one channel to be good at

Three channels done adequately beat none done well. Choose the one that fits the product's shape, write why, and name the others as later bets.

- **Programmatic SEO** suits products with an inherent dimension to enumerate: cities, categories, genres, integrations, comparisons, job titles. Needs real content per page and real time.
- **App store search** suits consumer mobile with existing demand. Cheap, slow, compounding.
- **Marketplace supply-side sales** suits two-sided products: get the sellers, who bring the buyers. Usually hand-to-hand at first, and usually right.
- **Community and content** suits products whose users already gather somewhere.
- **Paid** is for validating a message or pouring fuel on a loop with known payback. Not for finding product-market fit, and not before Phase 2's payback number exists.
- **Partnerships and integrations** suit products that sit inside someone else's workflow.

## 2. Programmatic SEO, if it fits

Decide the **page-type matrix** first, because it determines the routing, the templates, the link graph, the sitemaps and the link-preview templates from Phase 5 — all at once.

For each page type write: the URL pattern, the intent it serves, how many pages it yields, where the content comes from, the `title`/`description` pattern, the schema.org type, which pages link into it, and the one conversion action. For example: `/discover/<city>` serves "things to do in `<city>` this weekend", yields one per launch city, draws from live event data, carries `ItemList` + `Event` structured data, is linked from the home page and every event page, and converts to an app install.

Then the mechanics that decide whether it ranks at all:

- **Thin pages are a liability.** A page type that can't carry genuine content at the thin end of its range should not exist at that end. Set a minimum (enough items, enough text) and `noindex` below it rather than publishing thousands of near-empty pages — that is the single most common way a programmatic site gets buried.
- **Canonicals** on every page, self-referencing, with filter and sort parameters pointing at the clean URL.
- **Sitemaps** generated, split by type, under the per-file limits, with `lastmod` that is actually true.
- **Structured data** per page type, validated in CI.
- **Internal linking** as a deliberate graph, not a footer dump: each page links to its siblings and its parent, and the hubs are reachable from the home page in two clicks.
- **Rendering**: server-rendered HTML for anything meant to rank.
- **Core Web Vitals** as a build budget, from Phase 4.
- **Aliases and redirects**: one canonical slug per entity with the known variants redirecting (`nyc` → `new-york`), decided once, in the shared vocabulary from Phase 4.

## 3. App store optimization

- **Keywords**: the title carries the most weight, then the subtitle, then the keyword field. Research actual search terms rather than guessing; the store's own suggest and search-ads tools are the honest source.
- **Screenshots** are the conversion lever, not the icon. The first two matter most. Phase 5 generates them.
- **Custom product pages** per campaign or intent, each with its own URL — this is what lets a paid or content campaign land somewhere that matches the ad, and it measurably lifts conversion.
- **Campaign tokens.** Put a provider campaign token on every store link so installs attribute back to the source. Define the token's format as an enum in the shared vocabulary (lowercase, hyphenated, length-capped) and generate it in one function used everywhere, so that the token in an email, a web button and an ad are built identically. This is small, dull work that silently decides whether your acquisition data means anything.
- **Deferred deep linking.** Decide what happens when someone taps a link to a specific item, installs, and opens the app: they should land on that item. On Android the install referrer carries it; on iOS there is no equivalent for an organic store install, so plan the fallback rather than assuming parity — and say so in the plan, because this asymmetry surprises people.
- **Ratings prompts** at a moment of success, rate-limited, and never blocking.
- **Store review latency** is a schedule dependency. Budget it in Phase 9.

## 4. Loops, with the arithmetic

A loop is a mechanism where using the product creates the next user. Write it as explicit steps with a number on each, and the honest version is usually sobering:

```
A guest attends an event and uploads photos      → 38% of attendees upload
Their photos tag other attendees                 → avg 4.1 people per album
A tagged person gets a notification              → 61% open
They install to see the photo                    → 22% of opens install
k = 0.38 × 4.1 × 0.61 × 0.22 ≈ 0.21
```

k below 1 means the loop lowers your effective CAC but does not grow the product by itself — which is fine and normal, as long as you say it instead of implying virality. State which factor you'd improve first and what it would take. For non-viral loops, measure the equivalent: content indexed per user, seller-brought buyers, integrations per account.

Also design the **invite** properly, because it is where loops leak: what the sender sees, what the recipient receives (it must make sense to someone who has never heard of the product), where it lands, and what the recipient gets before signing up. A link that demands an account before showing anything kills the loop.

## 5. The measurement contract

Define this before the build, as a shared artifact, and give every consumer a test that fails when it drifts. This is the single highest-leverage thing in the phase: without it, three clients each invent their own event names and the funnel cannot be assembled afterwards at any price.

Write the contract with:

- **One event list.** Every event, who sends it, exactly when, and its parameters. One name per concept — if the web client and the app send the same user action under two names, you have no funnel. Decide who is authoritative for each event: anything involving money should come from the server, which knows the truth, and the client should not also send it. Duplicate client-and-server events for one action are a recurring, silent cause of double-counted conversions.
- **Conventions, written down.** Booleans as a consistent type. IDs as join keys rather than registered dimensions. Slugs, not display names, for anything you will group by. Money in minor units with a currency. One canonical vocabulary for cities, categories and roles, shared with Phase 4's enums.
- **Screen and page names**, one per route, enumerated — with a test that fails when a route exists with no name, because auto-generated screen names produce unusable reports and the gaps are invisible until you query.
- **Internal traffic** marked by a parameter from the environment, so your own testing doesn't pollute the funnel. Do not activate a filter that drops data until you have confirmed the tagging works; dropped data does not come back.
- **The funnel script**: the full path from first touch to the core action, written as numbered steps with the expected event *and its expected parameter values* at each one. This is what you run on a real device before shipping. It is also the best specification of the product's happy path that will exist.
- **A pass criterion per query.** Not "check analytics" but "this query returns zero rows", "these two counts are within 5%".
- **A baseline.** Run the queries before the change, so that after it you can tell a fix from a regression. Where a decision depends on what the baseline shows, write both branches in advance: *if the server count ≈ the client count, remove the client event; if the server count is near zero, keep it and open a ticket instead.* Pre-writing both branches is what stops the decision being made hastily under deploy pressure.
- **Cutover notes.** When a name or an enum changes, reports before and after are not comparable. Write the date and what changed, so a future reader doesn't chase a phantom drop.

## 6. Launch sequence

Name the order, with what each is for: the hand-reached first 50 from Phase 1; the content or SEO pages that take weeks to rank, so they go up early; the store listing with its review buffer; the loop, which needs enough density to work at all (a loop in an empty product looks broken); then paid, once payback is known. Say what you are deliberately not doing yet.

## Output of this phase

Write `plan/06-growth.md` with: the chosen channel and why; the page-type matrix with thin-page thresholds; the ASO plan with the campaign-token format; the loop with its arithmetic and the factor to improve; the full measurement contract including the funnel script with expected values; the baselines to capture and any pre-written decision branches; and the launch sequence. Every feature in the roadmap must appear in the event list — the validator checks this.
