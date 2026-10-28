# Red team: the hostile read, the edge cases, and what you did not verify

A plan written by one process, in one sitting, agrees with itself. That is not evidence that it is right. This phase attacks it deliberately, because the cheapest version of every objection is the one you raise yourself.

## 1. Read it as four hostile readers

Write a short, honest answer to each. If an answer is weak, fix the plan rather than the answer.

**The competitor who has your plan.** They have money, engineers and customers. Which part of this do they copy in a quarter? What is left that they cannot copy — and is it the data, the relationships, the switching cost, or genuinely nothing? If the honest answer is "nothing", the wedge from Phase 1 is a feature, and this is the moment to say so.

**The investor looking for a reason to pass.** Which number is the softest? Which assumption is doing the most work? They will find the weakest multiplier in the Phase 2 chain, so find it first and either source it or mark it as the thing to test in week one.

**The regulator or plaintiff's lawyer.** Pick the most sensitive data the product touches and trace it: collected where, stored how long, shared with whom, deleted when, consented how, and what the evidence of that consent is. Then ask what the worst good-faith reading of the strictest applicable rule says. Biometrics, minors, messaging consent and money are where this bites.

**The user who wants to hurt someone with it.** The most under-planned reader, and the one who shows up first. See §2.

## 2. Abuse, externalities and the edges

Every product with users, content or money has an abuse surface. Name it and say what the product does about it — in the roadmap, not in the terms of service.

Work through the ones that apply:

- **Content about people who did not sign up.** Shared cameras, tagging, face matching and guest lists all capture people who never agreed. What is the removal path, who can trigger it, and how fast? This is both a legal exposure and the thing that gets a consumer app written about badly.
- **Stalking and unwanted contact.** Any feature that tells one person where another is, was, or will be. Location, check-ins, "who's going", face match, mutual-friend hints. Blocking must actually block — across search, notifications, suggestions and shared surfaces, not just the message thread. Decide the default: visible or hidden.
- **Spam through your invite system.** Invites are a growth loop and a spam vector in the same code path. Rate limits per sender, per recipient and per account age, and the loop metric from Phase 6 watched for the shape that means abuse rather than growth.
- **Harassment and pile-ons** in any comment, chat or reaction surface.
- **Fraud and chargebacks** in anything that takes money; resale, scalping and ticket forgery in anything that grants entry. Signed, single-use tokens and a door that flags a re-scan are the structural answer, not a policy.
- **Minors** in an adult context, which is both a legal trigger and a moderation problem.
- **Scrapers and competitors** taking your data through your own API or public pages. Decide what is public on purpose.
- **The journalist case.** Pick the worst true headline this product could generate, write it as a sentence, and then write the design decision that prevents it. This takes ten minutes and changes product decisions more than any other exercise here.

Then the **boundary conditions**, which is where software actually breaks:

- Zero state: the first user, an empty city, a night with no events. A loop that needs density looks broken until it has it — what does the first user see?
- One of something, where the design assumed many; and thousands, where it assumed few.
- The very long name, the emoji-only name, the right-to-left name, the name with an apostrophe.
- Timezones, daylight saving, midnight, and an event that crosses it.
- Offline, then back online with queued writes. The same action submitted twice.
- The slow network, the old cheap phone, the small screen, the large font setting.
- The user who deletes their account while their content is load-bearing for someone else's.
- The supplier who is down during your busiest hour.

Pick the ones that matter for this product and put each as a test or a step. A listed edge case with no step is a note, not a plan.

## 3. Concentration risk

Name every single point of failure where a decision outside your control could end the business, and the mitigation or the accepted exposure:

- **One platform.** An app store rejection or policy change. Mitigation is usually a web path that works on its own.
- **One channel.** One algorithm change, one ranking update. If more than about 70% of acquisition comes from one channel, say that out loud.
- **One supplier.** Payments, auth, the model API, map tiles, hosting. For each: what happens if they double the price, change the terms, go down for a day, or launch your product?
- **One customer or one city.** Revenue concentration.
- **One person.** The operator. What breaks if they are unavailable for two weeks? Credentials, access, and the things only they know.

## 4. Kill scenarios

Three short paragraphs, written as if they happened:

1. **It dies in six months.** The most likely cause, honestly. For most bootstrapped products it is not competition — it is that the first 50 customers were harder to reach than planned, so revenue never started and attention went elsewhere. Say what the early warning sign would be and what you would do on seeing it.
2. **It dies at scale.** It works, grows, and then breaks: the architecture ceiling from Phase 4, support load that outgrows one person, moderation load, or unit economics that get worse with scale rather than better. Which one, and at what number?
3. **It succeeds and is competed away.** Someone with distribution copies it. What did you build in the meantime that keeps the customers?

For each, name the leading indicator you could watch and where it would be visible — a Phase 6 query, a support volume, a cohort retention curve. An unwatched risk is a surprise with extra steps.

## 5. The pre-handoff audit

Go through the whole plan once more against this list, then run the validator.

- [ ] Every department is planned from its head's seat, or not applicable with a reason and a trigger, and its hires and tools are in the model
- [ ] The riskiest assumptions each have an experiment with keep-going and stop thresholds written before running
- [ ] The prototype covers the core loop, the buyer's screen and the money moment, with no broken links, in the design language's tokens
- [ ] The venture site is rebuilt from the current files
- [ ] The trap sweep is complete: every canonical row answered with a source, or n/a with a reason, and re-asked since the product last changed shape
- [ ] Every number has a source and a date, or an `UNVERIFIED:` marker
- [ ] "What the re-read changed" exists and is not empty
- [ ] The market size is built bottom-up from countable units
- [ ] Every architecture layer has named rejected alternatives
- [ ] Every triggered compliance row points at a step that exists
- [ ] Rows needing a lawyer are collected in one place, and the review is a step
- [ ] Every roadmap step has an anchor, a risk, a test with a pass criterion, and a revert
- [ ] The cut line is written, in tiers, and the binary-only steps are named
- [ ] Gates are written as checks with pass criteria
- [ ] The cannot-be-undone list exists
- [ ] Human steps are separated, with lead times, and marked as blocking what they block
- [ ] Contracts are a workstream of their own and land before the others
- [ ] No two concurrent workstreams claim the same file
- [ ] Every user-facing feature appears in the event list with a pass criterion
- [ ] Every page type and link type has a generated preview image
- [ ] Contrast results are recorded and pass
- [ ] The abuse surface has steps, not just notes
- [ ] The critical path is estimated and the plan's claim matches it

## 6. Say what you did not verify

Close the plan with a section listing, plainly:

- Every `UNVERIFIED:` claim, who can verify it, and what it would change if wrong
- Everything you could not test for lack of access — credentials, a device, a bank account, a store account — and who must run it
- The three decisions you most want challenged
- What you deliberately left out of scope, and why

This is the most credible page in the document. A plan that admits its gaps can be acted on; one that hides them gets found out in week three, when correcting it is expensive.

## Output of this phase

Write `plan/10-red-team.md` with all six sections. Then run `python3 -I scripts/check_plan.py <plan-dir>` and fix everything it reports before handing anything over.
