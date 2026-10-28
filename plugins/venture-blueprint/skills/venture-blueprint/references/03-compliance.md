# Compliance: the register, the trigger map, and platform policy

Compliance done late is a tax on finished work. Done at this phase it is usually free, because the obligation can be designed away before the data model exists. The two patterns that save the most money are *don't collect it* and *don't hold it*.

**This phase does not produce legal advice, and you must say so in the document.** It produces a register of what applies, what it appears to require, what the product will do about it, and what evidence will exist — so that a licensed attorney in the jurisdiction reviews a specific, cheap list instead of discovering the whole problem after launch. Name the review as a human step in Phase 9.

## The verification rule

Treat every legal and platform fact as unknown until you have read a primary source and written down the date you read it.

This is not caution for its own sake. While this skill was written, a single search returned Apple's US external-purchase-link commission as 0%, 15% and 27% at once, from sources that each sounded authoritative; and a Texas statute that had been preliminarily enjoined was back in force after a Fifth Circuit ruling, with secondary commentary still describing it as blocked. Both numbers would have gone straight into a pricing model and a launch plan.

So:

- **Primary sources only** for anything load-bearing: the statute text, the regulator's own page, Apple's App Store Review Guidelines, Google's Play policy centre, the provider's own developer docs. Law-firm alerts and vendor blogs are useful for *finding* an issue and unreliable for its current state.
- **Record the date.** Every row in the register carries `verified: YYYY-MM-DD`. Anything older than about 90 days at build time gets re-checked, and the roadmap includes that re-check as a step.
- **Litigation status is part of the fact.** A law can be passed, enjoined, stayed and in force within a year. Write the posture, not just the rule.
- **Write `UNVERIFIED:` and move on** rather than guessing. The validator counts these and the founder decides what to chase. A guess that reads as research is the expensive outcome.

## The register

One row per obligation, in `compliance.csv`. Every row must name a step in `roadmap.json` that implements it — an orphaned row is an obligation nobody will do.

| Column | Contents |
|---|---|
| `feature` | The product surface that triggers it (face match, invite SMS, ticket payout) |
| `regime` | The law, rule or policy section |
| `requirement` | What it appears to require, in a sentence |
| `posture` | In force / enjoined / effective `<date>` / proposed |
| `approach` | Design it away, implement it, or avoid the feature |
| `step` | The roadmap step id that does the work |
| `evidence` | The artifact that proves it (consent log, retention job, privacy manifest, registered agent, DPA) |
| `source` | URL or citation |
| `verified` | Date you read the source |
| `counsel` | Whether an attorney must review this row before launch |

## Trigger map

Walk the feature list and mark every trigger. These are prompts for what to research, not statements of law — follow each to a primary source.

**Any personal data.** US state comprehensive privacy laws now cover most of the population and differ in thresholds and rights. Texas's TDPSA, California's CCPA/CPRA, and the Virginia, Colorado and Connecticut acts are the usual starting set; several attach only above revenue or data-volume thresholds, which makes them a *cliff* for Phase 2. If anyone in the EU or UK can sign up, GDPR/UK GDPR applies regardless of where the company sits. Practical requirements that shape the build: a privacy notice that matches reality, a working data-subject request flow (access, delete, correct, port, opt out of sale/targeted ads), a universal opt-out signal, data minimisation, retention limits, and a subprocessor list with DPAs.

**Biometrics.** The sharpest edge in US privacy. Texas's CUBI requires notice and consent before capturing a biometric identifier for a commercial purpose, limits disclosure, and sets a destruction deadline; it is enforced by the Attorney General with penalties per violation. Illinois's BIPA is the dangerous one because it carries a **private right of action**, which is why biometric class actions cluster there. Face matching, voiceprints and fingerprint login all trigger this. Design responses: keep templates on-device, store a non-reversible hash rather than the template, make the feature opt-in with a separate consent record, never use it for ads, and build the deletion job before the feature. If the product can work with a user-tagged photo instead of a face template, that choice removes an entire regime.

**Minors.** Under-13 data triggers COPPA (verifiable parental consent, no behavioural ads). Several states add age-appropriate design duties. App-store age-signal laws — Texas's App Store Accountability Act and its counterparts in other states — put duties on *developers*, not only stores: receive and act on the store's age-category signal, honour store-provided parental consent, notify stores before significant changes to terms, privacy practices, age ratings, monetization or functionality, use that data only for age enforcement and delete it after, and not misrepresent the age rating. Verify current posture and the state list; this area is moving fast, is under First Amendment challenge, and the deadlines are staggered across states rather than shared. Two details change the engineering: these laws generally give a developer a **good-faith reliance safe harbour** for acting on the store's signal, which is the strongest argument for taking the signal instead of building your own age check — and at least one state reportedly provides **no cure period**, so there is no window to fix a miss after a complaint. At least one state's private right of action is also reported to attach later than the rest of its duties, which makes the real deadline a date per state rather than one date.

Practical design: take the store's signal rather than collecting IDs yourself, gate adult-context features on it, keep the signal only for that purpose and delete it after, and wire the store-notification duty into your release process rather than leaving it to memory — it fires on changes to terms, privacy practices, age ratings, monetization and functionality, which is most releases.

**SMS and email.** SMS to US numbers requires prior express written consent under the TCPA, plus carrier registration (10DLC) for application-to-person traffic, with quiet hours and a working STOP. TCPA has a private right of action and statutory damages per message, so this is a genuine business risk, not a formality. Email needs a working unsubscribe, a physical postal address and honest headers under CAN-SPAM. Build the consent record and the opt-out state into the data model, not into the sending tool — PXI's "only opted-in guests" rule is this, enforced in the product.

**Taking money.** The question that decides your architecture: **are you ever in possession of someone else's money?** If funds land in your account and you later pay them out, you are probably in money-transmission territory, which means state-by-state licensing, bonding and capital requirements that will stop a bootstrapped company outright. The standard way to design it away is to never hold the money: use a processor's connected-account model so the seller is the merchant of record and funds settle directly to them, with your fee taken as a platform fee. PXI does exactly this — money goes straight to the organizer's own Stripe and PXI never holds it — and that is a licensing decision expressed in a data flow. Also in scope: PCI-DSS (minimise by never touching card data — hosted fields or SDK only), card-network rules on surcharging and descriptors, chargeback handling, 1099-K reporting if you pay out, sales tax on SaaS (Texas's treatment of software and data-processing services is a classic surprise — verify it), and marketplace facilitator rules if you sell on others' behalf.

**User-generated content.** Register a DMCA agent with the Copyright Office — it is cheap, it is a precondition of safe harbour, and it is routinely forgotten. Build notice-and-takedown. Know your reporting obligations for child sexual abuse material and have the pipeline before launch, not after the first report. Apple and Google both require UGC apps to ship moderation, reporting and blocking before review will pass, so this is also Phase 8 work. Keep a terms of service and acceptable use policy that a moderator can actually enforce.

**Likeness, photos and AI.** Shared cameras and face matching mean photos of people who never signed up. Decide the consent model for appearing in someone else's photo, and build the removal path. Texas and other states regulate synthetic likeness and deepfakes; AI disclosure duties are emerging. If a model trains on user content, say so in the notice and get consent, and keep provenance for anything generated.

**Accessibility.** ADA claims against apps and sites are common and cheap to file. WCAG 2.2 AA is the practical standard; treat it as a design input in Phase 5 (contrast, focus order, labels, dynamic type, screen-reader names) rather than an audit in Phase 10. It is far cheaper in tokens and components than in retrofits.

**Vertical regimes.** Health data (HIPAA, if you are a covered entity or business associate), lending and money services, insurance, alcohol (state ABC rules — nightlife products bump into this), firearms, cannabis, education records (FERPA), background checks (FCRA), hiring (classification of workers, automated-decision rules). If the product touches one of these, mark it `counsel: required` and do not design around it from guesses.

**The company itself.** Entity choice and state of formation, registered agent, EIN, Texas franchise tax, foreign qualification in states where you have nexus, trademark search before you commit to the name (do this in Phase 0 — renaming after launch is expensive), contractor agreements with IP assignment, and a privacy and terms pair that matches what the product actually does.

## Apple and Google

Both stores reject at review for the same handful of reasons, and each rejection costs a release cycle. Map features to policy sections and verify each against the current guidelines text.

**Apple, the sections that bite:** completeness and no placeholder content (2.1); minimum functionality — a thin wrapper around a website gets rejected (4.2); digital goods and services must use in-app purchase, with carve-outs that differ by storefront and are actively litigated (3.1.1, 3.1.3) — verify the current rule for *your* storefront and never bake the commission number into a pricing model without a dated citation; account deletion must be available in-app if accounts can be created (5.1.1); privacy policy link, purpose strings, the privacy manifest and required-reason API declarations; App Tracking Transparency before any tracking across apps, with the prompt placed where it makes sense rather than on cold start; UGC moderation, reporting and blocking (1.2); Sign in with Apple where other third-party logins are offered; age rating accuracy; and a review note explaining anything a reviewer could misread. Write the review note in the plan — PXI drafted theirs in advance, explaining exactly when the ATT prompt appears, and that is why it passed.

**Google, the sections that bite:** the Data safety form must match actual behaviour, including SDKs you didn't write; sensitive permissions need declarations and often a demo video; Families policy if the audience could include children; billing rules and the alternatives programme, whose availability and fees vary by region and are mid-transition — verify per region and per date; target API level deadlines, which force a release on a schedule; account deletion with a web-accessible deletion request path; and background location, accessibility-service and all-files-access permissions, each of which needs a strong justification.

**Both:** an account deletion path, a privacy notice that matches the data flows, no surprise data sharing by SDKs, and the age-signal duties above. Put the store-asset work in Phase 5 and the submission steps in Phase 9's human section, with review time budgeted — review latency is a schedule dependency, and a rejection costs days.

## Design the obligation away

Prefer these in order, because each one removes work and risk permanently:

1. **Don't collect it.** The cheapest compliance is an absent field. Every data point you keep is a retention policy, a breach exposure, a DSAR obligation and a row in the register.
2. **Don't hold it.** Money, biometric templates, government IDs, card numbers. Route them to a party whose business is holding them.
3. **Keep it on the device.** On-device matching turns a biometric database into a local file.
4. **Take the signal, not the proof.** The store's age category instead of a scan of a licence.
5. **Make the right thing automatic.** A retention job that deletes on schedule is better than a policy saying you will, because the register asks for evidence and a cron job is evidence.

## Output of this phase

Write `plan/03-compliance.md` with: the disclaimer that this is not legal advice and names the attorney review step; the register, with every row pointing at a roadmap step; the obligations you designed away and how; the evidence artifacts that must exist before launch; the store review notes drafted; and a list of rows marked `counsel: required`. Every triggered row without a step is a validator failure.
