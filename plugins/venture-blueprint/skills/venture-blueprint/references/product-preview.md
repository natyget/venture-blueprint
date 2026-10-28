# Product preview: drawing the screens before building them

A plan someone can't picture is half a plan. The clickable prototype on the venture site makes each path tangible in Stage 1 — "this is what you'd be building" — and in Stage 2 it becomes the specification of the core loop, the thing a founder shows to customers in validation, and the starting point for the build. It costs a fraction of building the real thing and answers questions no document can: is the core task obvious, are there too many steps, does the buyer see what they're paying for.

## Which screens to draw

Not the whole app. The screens that carry the business:

- **The core loop**, end to end — the steps a user takes to get the value, from opening the app to the moment it pays off. For a tool library: find → check → reserve → pick up. Usually four to six screens.
- **The screen the buyer sees**, if the buyer isn't the user. A building manager paying for a tenant app needs a screen that proves it's being used; that screen is what renews the subscription.
- **The moment money changes hands** — the paywall, checkout or upgrade — because it is where the store-policy line and the price become real.
- **The first screen a new user sees.** It decides whether there is a second.

In Stage 1, draw three or four per path: enough to make the path concrete and to show where the paths differ. In Stage 2, draw the full core loop for the chosen path, plus the buyer, money and first-run screens — typically six to ten.

Each screen gets a `for` (which persona, at what moment) and `notes` (why the screen exists, and what decision it embodies). The notes are what turn a mock-up into an argument.

## The file

Stage 1: `plan/paths/<path-id>.screens.json`, beside that path's assumptions. Stage 2: `plan/screens.json`. `templates/screens.example.json` is a complete worked example — copy its shape.

```json
{
  "platform": "ios",
  "tokens": { "bg": "#f4f4f1", "surface": "#ffffff", "text": "#15171a", "muted": "#7a7d82",
              "accent": "#2f7d5b", "accent_fg": "#ffffff", "border": "rgba(21,23,26,0.12)", "radius": 12 },
  "start": "home",
  "flows": [{ "name": "A resident borrows a drill", "steps": ["home", "tool", "reserve", "confirm"] }],
  "screens": [
    { "id": "home", "title": "Library", "for": "a resident looking for a tool",
      "notes": "Why this screen exists and what decision it embodies.",
      "html": "<div class='title'>Tool library</div>…" }
  ]
}
```

- `platform` is `ios`, `android` or `web`; it picks the device frame.
- `tokens` are the design language. In Stage 2 they must be the same values as `05-design-language.md`; in Stage 1 a quick palette per path is fine, and helps the paths feel different.
- `flows` are named sequences the viewer can play step by step. Write one per job a persona does.
- Links: any element with `data-go="<screen id>"` navigates there; `data-back` goes back. Every link must point at a real screen — `build_site.py` and `check_plan.py` both report broken ones.

## The building blocks

Screens are small HTML fragments built from a kit of native-looking parts. The kit already handles spacing, type, colour, safe areas and the status bar, so screens stay short and consistent. Icons are `<i data-i="name"></i>`.

| Class | What it is |
|---|---|
| `title` | Large page title (iOS large-title style) |
| `sub` | Grey line under a title |
| `h` | Section heading inside a page |
| `section-h` | Small grey group label above a list |
| `bar` with `a`, `t`, `a r` | Navigation bar: left action, centre title, right action |
| `search` | Search field |
| `chips` / `chip` / `chip on` | Horizontal filter pills |
| `list` / `row` | Grouped list; a row holds `ic` (icon tile) or `avatar`, then `tx` with `t` (title) and `s` (subtitle), then `r` (right detail) |
| `card` | Rounded surface for grouped content |
| `grid2` + `card stat` with `k` / `v` | Two-up statistic tiles |
| `img`, `img hero`, `img sq`, `img tall` | Image placeholder in the accent colour, with a caption |
| `btn`, `btn ghost`, `btn sm` | Primary, secondary and small buttons |
| `input` | Form field |
| `badge` | Small tinted label ("Free", "New") |
| `map` with `pin` | Map placeholder with location pins (`style="left:30%;top:40%"`) |
| `done` with `ok` | Success state with a big check |
| `code` | Large monospace code (door codes, tickets) |
| `note` | Small grey footnote |
| `tabbar` / `tab` / `tab on` | Bottom tab bar |
| `sheet` | Bottom sheet |
| `webnav`, `web` | Web navigation bar and centred page column |

Icons available: home, search, plus, user, users, calendar, map-pin, bell, chat, settings, chevron-right, chevron-left, check, star, camera, wallet, heart, share, clock, ticket, tool, image, filter, more, x, upload, lock, chart, card, phone, doc, building, alert, target, tag, receipt, arrow, play, trend, eye, info, copy.

Inline `style` attributes are allowed for one-off colours and positions. Scripts, styles, forms and event handlers are stripped, so the prototype stays a picture that clicks, not an app.

## Making screens that look real

- **Real content, not lorem ipsum.** Specific item names, realistic prices, plausible counts. Content is what makes a reviewer believe the screen. Keep it consistent with the plan's numbers — if the model says 38 tools per building, the library says 38.
- **One job per screen**, with the primary action obvious and at the bottom. If you can't say what the screen is for in the `notes`, it doesn't belong in the preview.
- **Follow the platform.** iOS: large titles, grouped lists, a bottom tab bar, back at top left. Android: the same structure reads fine; keep touch targets generous. Web: a top navigation bar and a centred column.
- **The empty and success states matter.** A confirmation screen with the one thing the user needs next (a code, a time, a place) is often the most persuasive screen in the set.
- **Use the design language.** In Stage 2 the tokens come from `05-design-language.md`, so the preview, the store screenshots and the link previews all look like one product.

## Output

Stage 1: a screens file for each path. Stage 2: `plan/screens.json` with the core loop, the buyer screen, the money moment and the first-run screen, plus one flow per persona job. Then run `build_site.py`, open the Product tab, click through every flow yourself, and fix any broken link it reports before showing the founder.
