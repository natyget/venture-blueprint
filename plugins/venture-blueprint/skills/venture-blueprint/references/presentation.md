# Presentation: telling the case so it can be understood at a glance

The venture site is where the founder — and anyone they share it with — decides. A thorough plan presented badly is a thorough plan nobody understands. This reference sets how the case is told; `scripts/build_site.py` turns it into a map and a story; `check_plan.py` enforces the limits.

Write `plan/story.json` at the end of each stage, after the research and the numbers exist. It is a distillation: nothing in it is new, and everything in it traces to a phase document, a source or the model.

## The principles, and where they come from

**Answer first.** Lead with the conclusion, then the few reasons that support it, then the evidence for each — Barbara Minto's *Pyramid Principle*. The centre of the map is the answer; the first slide is the answer. A reader who stops after one screen should still know what this is and whether it works.

**Every beat states its point as a sentence.** A headline is an assertion with a verb — "Selling to buildings pays for itself by month 5" — not a label like "Market" or "Path B". Below it, visual evidence that proves the assertion. This is the assertion-evidence structure from Michael Alley's research at Penn State, which found audiences understand and remember technical content better this way than from topic-and-bullet slides.

**Tell it in the order investors expect.** Purpose, problem, solution, why now, market, competition, business model, numbers, team, the ask — the business-plan outline associated with Sequoia's guidance and repeated in most pitch-deck advice since. A reader who has seen a hundred decks follows this order without effort; a novel order costs them attention.

**Every visual must prove the headline.** If removing a chart loses nothing, remove it — the data-ink principle from Edward Tufte. A visual that is merely pretty is decoration, and decoration competes with the point.

**Fewer words, more numbers.** A number replaces a paragraph. An X → Y → Z chain replaces an argument. Three short points are the ceiling, not the target.

**Show confidence honestly.** A plan full of guesses must look like a plan full of guesses. The map's moss and the verdict both show it; the story never says "works" when it means "might work if the guesses hold".

## The shape of a beat

One beat is one idea. It becomes one branch on the map and one slide in the story.

| Field | Rule | Why |
|---|---|---|
| `kind` | From the stage's list below | Fixes the order a reader expects |
| `kicker` | ≤ 3 words — the topic | Label on the map; small caps above the headline |
| `title` | ≤ 14 words, a full sentence with a verb, stating the takeaway | The reader gets the point even if they read nothing else |
| `status` | `strong`, `partial`, `guess` or `risk` | Colours the moss: how far the reader should trust it |
| `kpi` | One number, `label` ≤ 6 words, optional `note` | The single figure that carries the point |
| `chain` | 2–4 steps of `{value, label}`, labels ≤ 6 words | The X → Y → Z behind the number: funnel, cause and effect, cost to margin to payback |
| `points` | ≤ 3, each ≤ 14 words, each a fact | What the number and chain can't say |
| `visual` | One, from the chooser below | The evidence for the headline |
| `sources` | `{label, url, date}` for every external claim | Due diligence the reader can check |
| `facts` | ≤ 6 short leaves for the map, each with a status | The specific findings that grow from this branch |

Every beat should have at least one of `kpi`, `chain` or `visual`. A beat that is only words is a paragraph pretending to be a slide.

### Status, honestly

- `strong` — backed by sources the reader can open, or by a test you ran. Needs at least one source with a URL and a date.
- `partial` — some evidence, some inference.
- `guess` — reasoning without evidence yet. Most of Stage 1 is this, and that is fine.
- `risk` — the point *is* a danger: a path that loses money, a rule that blocks you, a missing licence.

### Numbers from the model are tokens

Never type a figure the model produces. Write a token and `build_site.py` fills it in from `model.py`, so a headline can never disagree with the projections:

```
{{<path-id>.<scenario>.<metric>}}
```

- `path-id` is a file stem in `plan/paths/`, or `plan` for the chosen plan.
- `scenario` is `bad`, `base` or `great` (or the scenario's own name).
- `metric` is one of: `break_even` (e.g. "month 18"), `funding` (cash needed beyond starting cash, or "none"), `revenue_end` (monthly revenue at the end), `customers_end`, `cash_end`, `cash_low`, `payback`, `ltv_cac`, `margin` (gross margin per customer per month), `price` (revenue per customer per month), `cac`, `churn`.

Inputs you chose yourself ("$149 per building") are fine as plain text. Research figures ("15–30% store commission") need a source.

## The verdict

```json
"verdict": { "tone": "promising", "label": "Promising, not yet proven", "reason": "≤ 20 words on why" }
```

`tone` is `go`, `promising`, `caution` or `stop`. Use `go` only when the assumptions the result depends on most have been tested — `check_plan.py` refuses `go` while most model inputs are unverified. In Stage 1 the honest verdict is almost always `promising` or `caution`.

`oneliner` is what this is and for whom, in ≤ 16 words, with no adjectives doing the work: "Shared tool libraries for apartment buildings, booked from a phone."

`next` is the one action that should happen next, in ≤ 16 words.

## The order

**Stage 1 — explore.** The question is which path.

1. `question` — the idea and the pain, in the customer's terms.
2. `evidence` — one to three beats: the findings that decide between the paths (a platform rule, a price, a behaviour). These are where Stage 1's due diligence shows.
3. `path` — one beat per path, each headline its verdict in numbers ("loses more the faster it grows"; "pays for itself by month 5"), each with its numbers or its screens.
4. `recommendation` — which path and why, with the `compare` visual.
5. `test` — the cheapest test of the assumption everything depends on, with keep-going and stop thresholds as a chain and the `sensitivity` visual.

**Stage 2 — plan.** The question is whether to build it.

1. `problem` — who hurts, how often, what it costs them. A `quote` from real evidence is strong here.
2. `customer` — the persona the wedge serves, and what they pay today.
3. `solution` — the product, shown with the `screens` visual.
4. `why-now` — what changed that makes this possible or necessary.
5. `market` — the bottom-up chain from a countable universe to year-one customers, as a `chain` or `bars`.
6. `competition` — the `matrix`, with your row highlighted, and the gap in one sentence.
7. `model` — how money comes in, per unit, and the store-policy line.
8. `numbers` — the projections, with the `numbers` visual; headline the cash needed or the break-even month.
9. `go-to-market` — the first fifty customers and the channel that scales, as a `timeline` or `chain`.
10. `team` — optional: who does what, from the department plan.
11. `risks` — the two or three that could kill it, and what you'll do about each.
12. `next` — the first experiment from `validation.md`, with its thresholds.

Optional kinds, placed where they fit after `market`: `team`, `departments`, `compliance`, `traction`, `evidence`.

A "What's missing" branch is added automatically from the gaps — unanswered traps, unsourced assumptions, broken screens — so the reader always sees what's still open.

## The visual chooser

| Type | Use it when the point is… | Fields |
|---|---|---|
| `numbers` | how money or customers move over three years, in bad, expected and great cases | `path`, `metric`: `cash`, `revenue` or `customers` |
| `compare` | which path wins | optional `paths`: list of ids |
| `sensitivity` | which assumption the result hinges on | `path` |
| `screens` | what the product is | `path` (or `plan`), optional `ids`: up to three screen ids, the first shown in the middle |
| `bars` | the relative size of a few things | `items`: `{label, value, display}`, optional `highlight` index |
| `matrix` | how you compare with the alternatives | `cols`, `rows`: `{name, cells, us}` — cells are short text, `true` or `false` |
| `timeline` | what happens in what order | `items`: `{when, what}` |
| `quote` | a customer's own words prove the problem | `text`, `who`, `url` |

Choose the one that proves the headline. If none does, leave it out — the KPI and chain stand on their own.

## Before you build the site, read every beat as a stranger

- Read only the headlines, in order. Do they tell the whole case? If not, a headline is a label.
- For each beat: if the reader saw only the number, would they know what it means? If not, fix the label.
- Does the visual prove the headline, or just decorate the slide?
- Count the words. Cut every adjective a number could replace.
- Is every external claim sourced, and does every `strong` status have a link?
- Is the verdict as confident as the evidence, and no more?

Then run `build_site.py`, open the site, click the centre, click every branch, play the story through once, and fix what reads badly. `check_plan.py` enforces the word limits, the order, the tokens, the sources on strong beats and the honesty of the verdict; the reading is still yours.

## Example

`templates/story.example.json` is a complete Stage 1 story for the ToolShare example, and `examples/toolshare-demo/venture.html` is what it builds.
