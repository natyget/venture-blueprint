# Calibration: one real release plan, annotated

This is a condensed, annotated version of a real analytics release plan for PXI, a nightlife app with an iOS and Android client, a web property, an API and a shared specs repository. It is here as **calibration, not a template.** It plans one release across four repositories; this skill plans a whole company. What transfers is the resolution: how specific a claim has to be before it is useful, and how much of a step has to be written down before an agent or a founder can execute it unsupervised.

Read it once before Phase 9, and once again before handing a plan over.

---

## The opening paragraph

> I re-read every call site in four repos: app `b75f7fd`, web `41d7e96`, API `eac9d97`, specs `4caf1a3`. I didn't change any code. I wrote the BigQuery checks for baseline and release QA (Q1–Q13, each with a pass criterion) to `<path>/ga4-release-qa.sql`. I still have no BigQuery credentials, so someone on your side has to run them.

**Technique.** Four things in four sentences: the sources were re-read and are pinned to commits, so a reader can verify any claim; nothing was changed, so the reader knows the state of the world; the deliverable is named with its path; and the gap is stated plainly — no credentials, so a human must run the queries. The last sentence is the one most plans omit, and it is the one that prevents a stall in week three.

## "What the re-read changed"

> Web counts every free RSVP twice. `EventCheckout.jsx:721-725` sends a client `join_event` and labels it a "mirror". The RSVP request also carries GA ids (`src/services/tickets.js:167-175`), so the server sends a second `join_event` (`ticket.routes.ts:63-97`). Both have the same name, so GA4 counts both.
>
> TikTok can't start even after the ATT fix. The production iOS build and the OTA workflow write a fixed `.env` that has none of the `EXPO_PUBLIC_TIKTOK_*` variables (`deploy-ios-main.yml:38-64`, `ota-production.yml:30-56`). There's no Android workflow at all.
>
> Item format: the app and the server are the ones off, not web.
>
> Verified in the package sources rather than from memory: RNFB 23.8.8 reads the auto-screen-reporting key from `firebase.json` on Android (`android/build.gradle:101`) and on iOS. `expo-router` 6.0.23 drops a trailing index segment (`routeInfo.js:84-86`). That is the confirmed cause of `(tabs)`.

**Technique.** This is the most valuable section in the document, because it is the part a reader cannot get anywhere else. Each item is an assumption that was wrong, with the exact file and line that proves it. Note "verified in the package sources rather than from memory" — the author distrusted their own recall of a library's behaviour and went to the source, which is where the real cause of a mystery bug (`(tabs)` appearing as a screen name) turned up. Every plan this skill produces gets this section. If it is empty, the research is not finished.

## The contract, before the work

> Files in `pxi-specs/analytics/`: `TAXONOMY.md` (the human-readable contract), `taxonomy.json` (events, params, enums, item shape, screens), `cities.json` (`{slug, code, label, short, aliases[]}`), `QA.md`, `CHANGELOG.md` (dated cutovers).
>
> Each repo gets a copy of `taxonomy.json` plus a parity test that fails if a constant isn't in it.
>
> Conventions: booleans are the strings `'true'`/`'false'`. Counts are numbers. Money is in USD. `event_city` is always a slug from `cities.json`. `event_id`, `listing_id` and `album_id` are BigQuery join keys, so don't register them as GA4 dimensions.

**Technique.** The shared vocabulary is an artifact in its own repository, copied into each consumer with a test that fails on drift. This is what makes parallel work safe: three clients cannot invent three names for one concept if the name is a constant they import and a test enforces it. The conventions look pedantic — booleans as strings, slugs not display names — and they are exactly the decisions that, left unmade, produce a reporting mess nobody can fix retroactively at any price.

The `CHANGELOG.md` of dated cutovers deserves note: when an enum changes, reports before and after are not comparable, and a future reader chasing a phantom drop will need that date.

## A step

> **W4.** `src/app/get/route.js:16-26`
> **Change:** accept only whitelisted params — `ct`: `^[a-z0-9-]{1,40}$`; click ids: `^[\w-]{1,200}$`; `utm_*`: at most 100 characters; `city` must be in `cities.json`; `intent` must be one of the known intents. Build the store URL with W1. The redirect host stays fixed to the two stores, and keep `no-store` and `Vary: User-Agent`.
> **Test:** `curl -sI` with an iPhone and an Android user agent and check the `Location` header.

and another, with its reasoning spelled out:

> **W3.** `AnalyticsProvider.jsx`
> **Change:** in `StoreClickTracker` (`:71-92`), gather context from the URL, then the remembered session values, then `getAttribution().last`. Call `a.setAttribute('href', decorateStoreHref(…))` before sending the event.
> **Why this works:** every hub store button is a plain `<a>` (`Navbar:132-138`, `AppMapTeaser:34`, `MapGate:391-396`). The browser reads `href` only after the click event has finished dispatching.

**Technique.** The anchor is a file and a line range. The change is specific enough to implement without a judgement call — including the regexes, including the headers to preserve. The test is a command. And in W3, "why this works" explains a non-obvious browser behaviour the plan depends on, with the call sites that confirm the assumption holds everywhere. That paragraph is what stops a future reader "simplifying" the code and silently breaking attribution.

## A decision deferred to a measurement

> **W8.** Remove the duplicate web `join_event`. Run the Q7 baseline first.
> If the server hits roughly equal the client hits: replace the client call at `EventCheckout.jsx:725` with `mirrorToSocialPixels('join_event', …)`. Meta and TikTok keep their event, and GA4 keeps the server's hit.
> If there are almost no server hits: keep the client event and open an API ticket instead.

**Technique.** The decision is not made now, because the data to make it does not exist yet. So both branches are written in advance, with the query that decides between them. This is the opposite of "we'll see how it goes": the measurement is named, the threshold is named, and both actions are pre-authorised. Nobody has to make a judgement call under deploy pressure.

## The funnel script, with expected values

> 3. Install from the internal track and open. Expect: `first_open`; `firebase_campaign` with `source=google`, `medium=cpc`, `campaign=halloween-nyc` and the QA gclid; `deep_link_open` with `link_source=install_referrer`, target `/all-events` and cold start true; an `all_events` screen view for New York, weekend.
> 11. Take 3 photos with LIVE on. Expect exactly one `scrapbook_upload`: `media_count=3`, `first_for_night=true`, `capture_source=camera`; no `post_created` carrying an `album_id`.
> 16. Kill the app and relaunch. No prompt; ad consent is still granted.

**Technique.** Not "test the funnel" but sixteen numbered steps, each with the exact events and the exact parameter values expected. It doubles as the clearest specification of the product's happy path in the whole document, and it is runnable by someone who has never seen the code. Note step 11's negative assertion — *no* `post_created` with an album id — because the bug being fixed was a duplicate event, and a test that only checks for the presence of the right event would pass while the bug remained.

## Gates, the cut line, and rollback

> **Gates before submitting the binary:** every automated check green; D1 passes steps 1–16; the D2–D4 ATT matrix passes; Q13 shows `sign_up` with a user id; smoke tests pass.
>
> **Cut line:** A1 is the only step that must be in the binary. If time runs out, A26 and W9 can ship in the OTA afterwards.
>
> **Rollback:** App JS — republish the previous OTA update. Web — Netlify rollback. API — revert (the changes are additive). **ATT answers: can't be undone.**

**Technique.** Gates are enumerated conditions, not a feeling. The cut line is one sentence written a week before the deadline, and it is precise about the thing that matters most — which step must be in a native binary rather than an over-the-air update, because that is what decides whether a late cut is possible at all. And rollback is per surface, ending with the item that cannot be rolled back. That last line is the one people most need and least often have.

## Human steps, separated

> **Tonight:** GitHub — add the three TikTok secrets, using a token separate from the server's. BigQuery — run Q7 before W8. GA4 — register event-scoped dimensions; create derived events `app_store_click_ios` and `app_store_click_android`; mark key events; create the internal-traffic filter **in Testing state**.
> **Tomorrow:** App Review note: "The ATT prompt appears right after the passport setup's APPROVED stamp for new accounts, and on the second launch on the Home tab for existing accounts." GA4 — switch the internal filter to Active after QA.

**Technique.** Console work an agent cannot do, with exact values, in time order. The App Review note is drafted in advance rather than improvised at submission — which is why the release passed review. And note "in Testing state": an active filter drops data permanently, so the irreversible version of the action is deliberately deferred until the tagging is confirmed.

## "What not to do"

> Don't change `runtimeVersion`, and don't add any native module in this binary. Don't prompt for ATT on cold start, on first open over the welcome card, over a sheet or popup, or on the camera. Don't put album ids in `event_id`. Don't send `purchase` from clients. Don't remove the server's `join_event` without the Q7 baseline. Don't put the gclid into GA4 web event params. Don't activate the internal-traffic filter before Q6 shows the tagging works; **an active filter drops data permanently.** Don't import `attribution.ts` into `analytics.ts`.

**Technique.** A negative-constraint list, each item a mistake someone would plausibly make while doing the work correctly — including the circular import that an agent would otherwise discover the hard way. Several entries name the permanent consequence inline. Every plan this skill produces ends with its own version of this list, drawn from the specific traps the research turned up.

---

## What to take from this

1. Pin your sources — commits, file:line, URLs with dates — and say when you went to the source instead of trusting memory.
2. Lead with what the re-read changed. It is the part nobody else can write.
3. Make the shared vocabulary an artifact with a test, before any parallel work starts.
4. A step is an anchor, a change specific enough to need no judgement call, a risk, a runnable test, and a revert.
5. When a decision needs data you don't have, write both branches and the query that chooses.
6. Write the funnel as numbered steps with expected values, including the negative assertions.
7. Decide the cut line early, and name what must be in a binary.
8. End with the human steps and the things that cannot be undone.
