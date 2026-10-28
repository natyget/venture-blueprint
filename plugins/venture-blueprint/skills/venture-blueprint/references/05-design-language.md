# Design language: from inspiration to tokens to every generated surface

Consistency is not a matter of taste or discipline. It is a matter of whether there is one source of truth that every surface reads from. A product looks coherent when the colour in the push notification, the store screenshot, the link preview and the button all come from the same file — and it drifts the moment one of them is hand-made.

This phase produces three things: a written design language, tokens as code, and a generator for every image the product needs.

## 1. Research the look, then abstract it

Collect references before deciding anything. Pull 15–25 screens from products whose audience overlaps yours, plus the platform's own first-party apps, which is what your users' expectations are actually calibrated against.

Sources, checked live on 2026-10-28:

| Source | What it holds | Fetchable? |
|---|---|---|
| `designeer.xyz` | **Start here.** A curated collection of interface craft, component libraries, AI tools and resources for builders, by Dhruv Jaradi. Sections: `/finds`, `/inspiration`, `/resources`, `/tools`, `/portfolios`. Supports `?view=list` and `?view=tile`; folders and favourites need a login, browsing does not | 200 |
| `mobbin.com` | Mobile and web app screens by app, flow and UI pattern. The strongest source for app UI | 200, but screens sit behind an app shell — use the browser pane |
| `refero.design` | Real product screens, searchable by element and pattern | 200 |
| `screensdesign.com` | iOS app screens and flows, video-captured | 200 |
| `pageflows.com` | Recorded user flows — the best source for *sequence*, not just screens | 200 |
| `godly.website` | High-craft web design | 200 |
| `awwwards.com`, `designspiration.com`, `uisources.com` | Broad web and visual reference | 200 |
| `land-book.com`, `lapa.ninja` | Landing pages | 403 to automated fetch — open in the browser pane instead |
| Apple Human Interface Guidelines | The platform's own rules, and what iOS users expect | Yes, and authoritative |
| Material 3 guidelines | The same for Android | Yes, and authoritative |

Two notes. First, a source the operator names is worth more than a generic one — ask, and use theirs first. But **verify it loads before relying on it**: parked domains and near-miss spellings are common, and a misremembered name costs a phase. `designer.xyz` is a parked domain for sale and `desingeer.xyz` has no DNS record at all, while `designeer.xyz` is the real site — three plausible spellings, one of which works. Check with a DNS lookup or a fetch before building a research pass on a name. Second, sites that return 403 to a fetch are usually fine in a real browser, so reach for the browser pane rather than concluding the source is gone.

Then abstract. **Take the mechanism, not the skin.** "A dense list with a persistent filter bar and a sticky summary row" is a mechanism you can reuse; copying a competitor's exact palette and corner radius produces something that looks like them and belongs to nobody. Write what you took and why it fits this audience — for each reference, one line: *what it does well, the mechanism, and whether it survives on a cheap Android phone in sunlight.*

## 2. Write the language before the tokens

Three or four sentences that a designer and a developer would both act on identically, naming the actual decisions:

> Dense, not airy: the user is looking for one thing in a list of forty. Dark by default, because it's used at night in low light, with a light theme that is a real theme and not an inversion. One accent colour, used only for the action that moves the user forward, so that it always means the same thing. Photography is the content and carries the warmth; the chrome stays neutral and gets out of the way. Motion confirms, never decorates: nothing animates longer than 200ms except a deliberate reveal.

Then the anti-list, which is what keeps it from drifting: what this product never does. No gradients on text. No more than two type weights per screen. No icon without a label in primary navigation. No modal over a modal. Each line should be checkable by looking.

## 3. Tokens, as code, as the only source

Tokens are a file that every surface imports — app, web, emails, generated images, store assets. If a colour exists in two places, it will differ in three months.

- **Colour.** A small neutral ramp (5–7 steps), one accent with its own ramp, and semantic roles layered on top: `bg`, `surface`, `border`, `text`, `text-muted`, `accent`, `accent-fg`, `success`, `warning`, `danger`. Define roles for both themes. **Verify every text-on-background pair at 4.5:1 for body and 3:1 for large text and UI boundaries, and put the check in CI** — contrast is the one design property that is objectively pass/fail, and the one most often broken by a later tweak. Never encode meaning in hue alone; pair it with an icon or label.
- **Type.** One or two families, a scale with named steps rather than arbitrary sizes, line heights as ratios, and the OS dynamic-type mapping so the app respects the user's accessibility setting. Test the longest realistic string, not the designed one.
- **Space.** One base unit and a short scale from it. Every gap comes from the scale.
- **Radius, border, elevation, motion.** Few values each, named by role. Motion gets durations and easings as tokens too, plus the reduced-motion variant, which is both an accessibility requirement and a store review consideration.
- **Icons.** One set, one grid, one stroke weight. Mixing two icon sets is the most visible kind of inconsistency and the easiest to avoid.

Ship them as the platform's native format — CSS custom properties, a Swift enum, a Kotlin object — generated from one source file so they cannot diverge. **A component that hardcodes a value instead of using a token is a lint error.** That rule, enforced, is what consistency actually is.

## 4. The component inventory

List every component the roadmap needs, each with its states, because the states are where the work hides and where the plan usually lies: default, hover, focus (visible, and keyboard-reachable), active, disabled, loading, empty, error, and the long-content case.

Then list the whole-screen states that products skip and users meet constantly: first-run empty, empty-after-filter, offline, slow network, permission denied, signed out, server error, item deleted while viewing, and the destructive-action confirmation. Each needs words written by someone who thought about what the user does next — an error state that says "Something went wrong" is an unfinished screen.

## 5. Every image is generated

This is the rule that makes "clean assets and intentional thumbnails everywhere" achievable rather than aspirational. Hand-made assets rot; generated ones stay right.

Build a **render pipeline**: templates in HTML/CSS reading the token file, rendered headlessly to PNG at the required sizes, run in CI, with the output committed or uploaded. One command regenerates everything after a token change.

What it produces:

- **App icon**, every required size per platform, from one source; plus the alternate icons if you offer them, and a dark/tinted variant where the OS supports it.
- **Store screenshots**, per required device class, per locale. Treat the set as a narrative: the first two are what most people see, so they carry the value proposition, not a feature tour. Generate the device frames and caption text from templates so a copy change is a re-render, not a design session.
- **Link previews, per page type.** This is the "intentional thumbnail for every link" requirement, and it is only tractable as a generator. Decide the page types in Phase 6, then build one template per type that takes the page's own data — an event's image, title, date and city; a listing's source and price; a profile's name and avatar. The default template is the fallback, never the plan. Every route must resolve to an image: a route that falls through to a generic card is a bug, and the site check should fail on it.
- **Favicons and web app manifest icons**, including maskable.
- **Email and push assets**: header, footer, and any image a transactional email carries, from the same tokens as the app.
- **Social and ad creative sizes**, if Phase 6 calls for them.

Add a check that walks every route and asset size and fails on a missing or default-fallback image. That check is what keeps the system honest after the third month, when nobody remembers the rule.

## 6. Accessibility as a token-level decision

Cheap here, expensive later: contrast in the palette and checked in CI; dynamic type in the type scale; touch targets at the platform minimum in the component sizes; focus states as a token so they exist everywhere at once; labels on every control and every icon-only button; reduced-motion variants in the motion tokens; and screen-reader names written alongside the component, not discovered in an audit. Phase 10 verifies; it should find little.

## 7. Keeping it consistent

- Tokens only, enforced by lint.
- One component per job. Two buttons that look alike become three.
- Visual regression snapshots on the component set, so a token change shows you every surface it touched.
- A single place where copy lives, so the product's voice is reviewable and translatable.
- The asset pipeline in CI, so regenerating is automatic rather than remembered.

## Output of this phase

Write `plan/05-design-language.md` with: the reference set and what mechanism you took from each; the language statement and its anti-list; the full token table with contrast results; the component inventory with states; the screen-state list; the asset pipeline with every output size and the per-page-type link preview templates; the accessibility decisions; and the CI checks that enforce all of it. The roadmap gets a step for the pipeline and a step for the checks.
