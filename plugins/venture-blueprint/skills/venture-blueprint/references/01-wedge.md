# Wedge: finding the problem, reading the competition, choosing where to enter

This is the phase that decides whether the other nine matter. A beautiful build on a problem nobody pays to solve is the most expensive mistake available.

## 1. When there is no idea

"Make me millions", "find me a business", "what should I build" — this is a research task, not a creativity task. Ideas invented in a chair are untested by definition. Problems people already pay to avoid leave evidence, and evidence is searchable.

### Where the evidence is

Work through these until you have 15–30 raw complaints with sources. Quote people in their own words and keep the URL and date.

- **One- and two-star reviews of incumbents**, on the App Store, Google Play, G2, Capterra, Trustpilot and Amazon. This is the highest-yield source in existence: a labelled dataset of what people hate about a product they chose and paid for. Sort by recent, read 30+, and tally the complaint *categories*, not individual gripes.
- **"Switching from X" and "alternative to X" threads** on Reddit, Hacker News, industry forums and Discord servers. People explain their reasoning in public when they leave.
- **Pricing-page outrage.** Search the incumbent's name with "pricing", "fees", "expensive", "raised prices", "per seat". Price resentment is the most reliably monetizable emotion in software, because it means the budget already exists.
- **Regulatory change.** A new statute or platform policy creates a compliance obligation on a deadline, which is a product with a forced buying date. The Texas App Store Accountability Act putting age-signal duties on developers is exactly this shape. Search for laws effective in the next 6–18 months in your jurisdiction and vertical.
- **Job postings.** A company hiring three people to do something manually is describing software that doesn't exist yet. Ops and "analyst" roles are the richest.
- **Spreadsheets and manual process.** Ask practitioners what they keep in a spreadsheet, what they re-type between two systems, and what they do on Sunday night. Integration and re-typing pain is boring, specific and fundable.
- **The operator's own advantage.** What can this person reach that others can't — an audience, a dataset, a licence, a venue relationship, a skill, a city? Score every candidate against it. An idea that doesn't use the operator's advantage is a strictly harder business.

### From complaints to candidates

Group the complaints into themes. For each theme worth pursuing, write a candidate as five lines:

```
Candidate: <short name>
Who: <the narrowest group that has this badly> — not "SMBs", but "independent event organizers running 2+ ticketed events a month"
Pain: <the complaint, quoted, with source + date>
Paid alternative today: <what they currently buy or do instead, with its price>
Why now: <what changed — a law, a platform shift, a price rise, a new capability>
Operator fit: <which of this operator's advantages it uses>
```

If you cannot fill "paid alternative today", the pain is probably real but unfunded — people will agree it is annoying and not buy. Say so explicitly; it is a common and fatal trap.

### Score and recommend

Score each candidate 0–2 on each, and present the table:

| Question | Why it matters |
|---|---|
| Is there a quoted, sourced complaint from a real person? | Separates evidence from imagination |
| Is money already being spent on this problem? | Budget exists; you are redirecting, not creating it |
| Can the narrowest viable version ship in weeks, not quarters? | Bootstrapping requires revenue before runway ends |
| Does it use this operator's unfair advantage? | Decides whether they beat a better-funded team |
| Is there a reason the incumbent structurally can't copy it? | See §3; without this you are a feature, not a company |
| Does it get better with scale (data, network, content)? | Decides whether it sustains the scale it reaches |
| Can one person reach the first 50 customers without ad spend? | Tests distribution before you depend on it |

Keep the top three. Recommend one, in two sentences, and say what would change your mind. Show this to the user before going further — this is the cheapest redirect in the whole process.

## 2. When there is an idea: try to kill it first

An idea arrives with its owner's enthusiasm attached, which is exactly the wrong lens. Spend one pass actively trying to falsify it, and write the results down even when they're inconvenient.

Answer each in writing, with sources:

- **Does it already exist?** Search the App Store, Google Play, Product Hunt, GitHub, G2 and plain Google. Finding competitors is good news — it proves budget. Finding *nothing* usually means you've mis-specified the market, not found a vacuum.
- **Has it been tried and died?** Search "`<idea>` shut down", "`<idea>` postmortem", "why `<idea>` failed". Read the postmortems. A dead predecessor tells you the actual constraint, which is usually distribution cost or a regulatory wall, not the feature set.
- **Why doesn't the obvious incumbent do this already?** There are only a few good answers: it cannibalizes their revenue, their data model can't express it, it's too small for their cost structure, they're structurally blocked (a partner agreement, a licence, a platform rule), or they are simply slow. "Nobody thought of it" is almost never the answer, and if that's your answer, keep looking.
- **What has to be true?** List the assumptions the business rests on, then mark each as verified, testable this week, or unfalsifiable. Rank them by how much breaks if they're wrong. Test the top one before Phase 4.
- **Who loses if this works?** They will respond. Name the response.

Write the strongest honest case *against* the idea in a paragraph. If you can't, you haven't researched enough. Then say whether it survives.

## 3. Competitor teardown

Pick 3–6 real competitors, including the one most customers actually use today — which is often a spreadsheet, a group chat, an agency, or doing nothing. Do not skip the incumbent you find boring; it has the customers.

For each, fill in a row and cite each cell:

| Field | How to get it |
|---|---|
| What it is, in one line | Their own homepage words, quoted |
| Price, all tiers, and what gates each | Their pricing page, with the date you read it. Note per-seat vs usage vs transaction, minimums, annual-only discounts, and the enterprise "contact us" floor |
| Real fee load | Add processing, service and platform fees. Headline price is rarely the bill |
| How they acquire customers | Which channel dominates: ads (check their ad library), SEO (look at what ranks and their page-type structure), sales team (check job postings), app store, partnerships, community |
| Who they're for, and who they refuse | Signup flow, docs, the "not for you" signals |
| Top complaints | 20+ recent 1–2 star reviews and switching threads, grouped, quoted |
| What they do well | Be honest. This is what you must match or route around |
| Stack and constraints | Job postings, `/robots.txt`, response headers, bundle analysis, status page, changelog cadence, app bundle size |
| Structural weakness | What their business model, data model or contracts prevent them from fixing |

Never put a competitor's name in customer-facing output. Describe them by how they work and keep the numbers exact, with the source in fine print — "the large US ticketing site that lists 3.7% + $1.79 per ticket for organizers". This holds in marketing, in the app, and in the plan's own comparison tables.

### The gap map

Lay the field out on the two axes that actually matter for this market (not price vs quality — something real, like "self-serve ↔ sales-led" against "single-venue ↔ multi-city"). Mark each competitor. Mark the empty regions. Then, for each empty region, ask the only question that counts: **is it empty because it's hard, because it's small, or because nobody got there?** Only the third is an opportunity, and only if you can say why you'll get there first.

Write the wedge as one sentence of the form: *for `<narrow who>`, we do `<the one job>` so much better that they switch, because `<structural reason the incumbent can't follow>`.*

## 4. The wedge, and the second move

A wedge is deliberately too small to be a company. That's the point: it's narrow enough to win completely and to be reached without a budget. Write both halves:

- **The wedge.** One job, one audience, shippable in weeks. The test is whether a stranger in that audience would switch on seeing one screen.
- **The expansion.** What the wedge earns you that you can't buy — a dataset, a distribution channel, a habit, a relationship, a piece of the transaction — and the next two adjacent jobs it opens. PXI's camera wedge produced photos that made the next event sell, which is why discovery, ticketing and organizer CRM all became reachable from it.

If the wedge earns nothing the next move needs, it's a feature. Keep looking.

## 5. Market entry when you have no audience

Name, concretely, how the first 50 customers hear about this — with names, not channels. "SEO" is not a plan at this stage; "the 40 organizers already running events in these three venues, reached by walking in" is. Then say how 50 becomes 500, and only then which channel scales. Phase 6 builds that out, but the first 50 must be nameable now, because a wedge that can't be reached by hand is unproven.

## Output of this phase

Write `plan/01-wedge.md` with: what the re-read changed; the candidates table (or the falsification pass); the competitor teardown with sources; the gap map; the wedge sentence; the expansion; the first-50 plan; the assumptions ranked by what breaks if wrong; and the strongest case against. Record every choice in `decisions.json`.
