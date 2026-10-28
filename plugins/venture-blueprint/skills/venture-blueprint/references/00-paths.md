# Stage 1: Explore — the brief, the founder's preferences, and two or three real paths

This stage exists because the most expensive planning mistake is a thorough plan for the wrong version of the idea. Every idea is really several businesses — the same neighbourhood tool-sharing concept can be a consumer app, software sold to property managers, or a marketplace that takes a cut of rentals — and they differ in who pays, how fast money arrives, how big it can get, and what the founder has to be good at. Choosing between them is the founder's decision, and they can only make it if they see the options side by side.

The deliverable is small on purpose: a comparison, a recommendation, and a question. It should take a fraction of the effort of Stage 2.

## 1. Ask once, in one batch

Ask everything you need in a single round, and offer choices wherever you can. A founder answers four multiple-choice questions faster and more honestly than one open question, and a drip of questions across ten messages feels like an interrogation. If the session has a structured question tool, use it; otherwise send one numbered message. Never stall waiting: if something is unanswered, assume, say what you assumed, and continue.

**The brief — five things that change every answer:**

1. **The operator.** Who is building this, what they already own — audience, code, data, licences, relationships, a skill — and what they can reach that a stranger cannot. The same idea is a good business for one person and a bad one for another.
2. **Cash, time and risk.** Runway in months, hours per week, and whether this must pay for itself from month one.
3. **Where.** Where the customers are and where the company is. State matters, not just country — it decides tax, privacy law and payment rails.
4. **Platforms.** iOS, Android, web, desktop, API.
5. **What success means.** Revenue, enterprise value, or take-home; and by when.

**The preferences — what decides which path is right for *this* founder:**

| Preference | Typical choices | Why it changes the path |
|---|---|---|
| Speed or size | Revenue in weeks / a bigger business in years | Sets wedge width and whether a slow-compounding channel like SEO is acceptable |
| Who pays | Consumers / businesses / both sides of a marketplace | Changes price, sales motion, compliance and support load completely |
| How they like to sell | Founder-led sales / self-serve product / community | A founder who hates calls should not pick a path that needs 50 of them |
| Capital | Bootstrap only / open to angels / venture-scale | Decides the acceptable payback period and how much can be built before revenue |
| Involvement | Side project / full-time / build-to-sell | Changes how much operating work the business can carry |
| Geography | One city first / national / international | Decides launch density, rails and the regulatory surface |
| Platform taste | Native app / web first / both | Affects cost, speed, store exposure and the fee line |
| Hard nos | e.g. never hold customer money, no ads, no selling data, no regulated verticals, no B2G | These are constraints, not preferences. Treat them as absolute |
| Products they admire | Two or three, with why | Feeds design language and tells you what "good" means to them |

If the founder has done this before, look for a `founder-profile.md` from an earlier plan and confirm it rather than re-asking. At the end of this stage, write or update one in the plan folder so the next venture starts from it.

## 2. A bounded evidence pass

Enough to ground the paths, not the full research — roughly six to twelve searches or page reads, aimed at:

- **Real pain**, quoted with a source and a date: one- and two-star reviews of the obvious incumbents, switching threads, pricing complaints.
- **Real prices** for the alternatives people use today, including doing nothing or a spreadsheet.
- **The two or three incumbents** a customer would name first.
- **Anything with a deadline**: a law, a platform change, a price rise — "why now".

When there is no idea at all, this pass *is* problem-finding: follow `01-wedge.md` §1, and the candidate problems become the paths.

Mark everything you could not verify. Stage 2 goes deep; this pass only has to stop the paths from being imaginary.

## 3. Generate paths that genuinely differ

Two or three. More than three and the founder can't hold them in mind; one is not a choice. Each path must differ from the others in **at least one of the things that change the business**:

- **Who pays** — consumer, business, or one side of a marketplace
- **The wedge** — the narrow first job and audience
- **The model** — subscription, per transaction, take rate, freemium, services-first
- **The channel** — how the first fifty customers arrive
- **The platform** — app, web, API, or something embedded in another product

Three versions of one plan with different feature lists are not paths. A useful test: if you described each path to a stranger in one sentence, would they think they were different companies?

Good path sets usually include:

- **The fastest path to revenue**, often narrower or more manual than the founder imagines — services-first, a single city, one customer type, sold by hand.
- **The biggest-ceiling path**, often slower and more capital-hungry.
- **The path that uses the founder's unfair advantage most directly** — which is frequently the right one, and often not the one they walked in with.

For an existing product, the paths are directions it could go next: deepen the core, expand to an adjacent customer, change the model, or move up or down the value chain.

## 4. Compare them in one table

Use the same rows for every path so they can be read across. Mark rough figures as rough — this is triage, not the financial model.

| | Path A | Path B | Path C |
|---|---|---|---|
| In one sentence | | | |
| Who pays, and for what | | | |
| The wedge (first customer and first job) | | | |
| How it makes money | | | |
| First fifty customers come from | | | |
| Rough cash before first dollar | | | |
| Rough time to first dollar | | | |
| Ceiling if it works | | | |
| Biggest risk | | | |
| Uses the founder's advantage? | | | |
| Fits their stated preferences? | | | |
| What you'd have to believe | | | |

Then, in plain sentences:

- **Your recommendation**, and the one or two reasons that decide it.
- **What would change your mind** — the fact that, if it turned out differently, would make you recommend another path.
- **Mixes worth considering** — sometimes the right answer is Path A's wedge with Path C's model, or doing A first to fund B. Say so if it's true.
- **Where a path conflicts with a stated preference**, say it plainly rather than quietly dropping the path. Founders sometimes revise a preference once they see what it costs.

Then ask the one question — which path, or which mix — and stop.

## 5. Record the choice

When the founder answers, write `plan/paths.md` with:

- **The paths** — the comparison table and your recommendation, as shown.
- **The choice** — which path or mix, in the founder's words, and the date.
- **The preferences as constraints** — one line each, phrased so a later phase can check against it ("Bootstrap only: no plan that needs outside capital before month 12"; "Never hold customer funds"; "Web first; native app only after 500 paying customers").
- **The rejected paths, and why** — so that in month four, when someone says "what if we did B instead", the reasoning is still there.

Record the choice in `decisions.json` too, with the rejected paths as rejected alternatives. Then write or update `founder-profile.md`.

The preferences recorded here bind every later phase. When Stage 2's research suggests a different direction, raise it with the founder rather than drifting into it.

## Output of this stage

`plan/00-brief.md` (the brief, with assumptions marked), `plan/paths.md`, a `decisions.json` entry for the choice, and `founder-profile.md`. In chat: the table, the recommendation, and the question. Check with `check_plan.py --stage explore`.
