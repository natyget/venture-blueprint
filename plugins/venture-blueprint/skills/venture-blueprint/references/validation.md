# Validation: test the riskiest assumption before you build

A plan is a set of guesses arranged to look like a decision. Most of them are fine to leave as guesses. One or two are carrying the whole business, and if they are wrong, everything built on them is wasted. This phase finds those, and designs the cheapest test that would prove them wrong — run in days, for little or no money, before the first line of production code.

It is the difference between "make me millions" as a wish and as a process: a founder who tests the riskiest assumption first loses a week when the idea is wrong instead of a year.

## 1. Find the riskiest assumptions

Three sources, in this order:

1. **What the numbers depend on most.** The venture site's *What matters most* chart (and `model.py`'s output) ranks the assumptions by how much a 20% miss moves the outcome. The top one or two, if unverified, go straight on the list.
2. **What has to be true** from each path in `paths.md` — the beliefs that, if false, make the path pointless regardless of the numbers. "Residents will borrow from a shared locker rather than buy" is not in the model, but the business dies without it.
3. **The red team's kill scenarios** — the early warning sign for the most likely way this fails.

Rank them by *how much breaks if wrong* × *how unsure you are*. Take the top three to five. Everything else waits.

## 2. Pick the cheapest test that could prove it wrong

Work up this ladder and stop at the first rung that gives a real answer. Cheaper tests that give a weaker signal are still worth running first, because a fail at rung 1 saves the cost of rung 4.

| Rung | Test | Signal strength | Typical cost |
|---|---|---|---|
| 1 | **Problem interviews** — 8–12 conversations with the persona about their past behaviour, not their opinions | Is the pain real and frequent? | Time only |
| 2 | **Prototype test** — put the clickable prototype from the venture site in front of 5 people from the persona and give them the core task | Do they understand it and finish the task? | Time only |
| 3 | **Smoke test** — a landing page with the specific offer and price, and a sign-up or waitlist | Will strangers act, not just agree? | A domain and a small ad budget |
| 4 | **Channel test** — a small budget on the channel you plan to scale, pointed at the smoke test | What does a customer actually cost to reach? | A few hundred dollars |
| 5 | **Concierge / manual MVP** — deliver the outcome by hand for 3–5 customers | Will they use it repeatedly, and does it work? | Founder time |
| 6 | **Pre-sale, deposit or letter of intent** — ask for money or a signed commitment | Will they pay? The only proof of willingness to pay | Refunds if it doesn't ship |

What people *say* they would pay is close to worthless; what they *do* is the evidence. Treat every "I'd definitely use that" as a zero until it is followed by an action that costs them something — time, an email address, a card, a signature.

## 3. Write each experiment before running it

The pass threshold is written down **before** the experiment runs. A threshold chosen after seeing the result is a rationalisation, and it is the most common way founders talk themselves into a dead idea.

For each experiment:

- **Assumption** — the exact belief, and which field in `assumptions.json` or which "has to be true" it tests.
- **Method** — the rung, what you show or ask, and to whom.
- **Who and how many** — the persona, where you'll find them (by name or place, not "online"), and the sample size.
- **Cost and time** — money and days.
- **Pass** — the threshold that means "keep going": "at least 6 of 10 managers have had a tool request from a resident in the last month"; "landing page converts above 8% from targeted ads"; "3 of 5 buildings sign a paid pilot at $149/month".
- **Kill** — the threshold that means stop or switch path. Write it even when it's uncomfortable. Pass and kill should leave a gap between them; results in the gap mean "run a bigger test".
- **If it passes / if it fails** — what changes in the plan either way.

## 4. Interviews that don't lie to you

People are polite, and polite answers are useless. Ask about the past and the specific, never about the future or the hypothetical:

- "Tell me about the last time you needed a tool you didn't own. What did you do?"
- "What did that cost you — in money, in time?"
- "What have you already tried to fix this?" (No attempt usually means no real pain.)
- "Who else deals with this?" (Finds the buyer, who is often not the user.)
- "Can I show you something and get your honest reaction? It's fine if it's not for you."

Never pitch during a problem interview, never ask "would you use…", and never ask what they'd pay — offer a price and watch what they do. Write down their words; the good quotes go straight into the personas.

## 5. Do it honestly

- **Smoke tests and pre-sales must not mislead.** Say plainly that the product is coming, take deposits only with a clear refund promise, and refund promptly if it doesn't ship. Taking money for something that does not exist without saying so is both unfair and, depending on the jurisdiction and platform, illegal.
- **Collect only what you need.** A waitlist needs an email address and maybe a role. It still needs a short privacy notice.
- **Ad platforms have policies** for landing pages and claims; read them before spending.
- **Interview consent** — tell people what you'll do with what they say, and don't quote them by name without asking.

## 6. Feed the results back

Keep a results log in `validation.md`: date, what happened, the numbers, and the decision. Then:

- Update the tested field in `assumptions.json` — replace `UNVERIFIED: …` with what the experiment found and how ("Experiment E2, 2026-11-10: 4 of 5 buildings accepted a paid pilot at $149; n=5").
- Rerun `model.py` and `build_site.py`. The verdict, the futures and *What matters most* all move, and the next riskiest assumption rises to the top.
- If a kill threshold was hit, say so plainly in chat and go back to `paths.md`. A dead path found in a week is the system working.

## Output of this phase

`plan/validation.md` with: the riskiest assumptions and how you ranked them; each experiment in the format above with pass and kill written in advance; the interview script for this persona; the smoke-test or pre-sale offer if one is planned; and an empty results log ready to fill. The validator checks for the riskiest assumptions, the experiments, their pass and kill thresholds, and the results log.
