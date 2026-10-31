# Product preview: showing what you'd build

A plan someone can't picture is half a plan. The product preview draws the key screens in the product's own design language and shows them as polished imagery — three phones fanned on a soft backdrop, or a browser window for web products — on the solution beat of the story and wherever a path needs to be seen to be judged.

It is **imagery, not a working demo**. Its job is to make the product real at a glance and to carry the brand's look, the way a store listing or a launch page would. It also gives customers something concrete to react to during validation, and it is the starting point for the build.

## Which screens to draw

Not the whole app — the screens that carry the business:

- **The core moment** — the screen where the user gets the value. This is usually the hero, shown in the middle.
- **The screen the buyer sees**, if the buyer isn't the user — the one that renews the subscription.
- **The moment money changes hands** — paywall, checkout, upgrade — because it's where the price and the store-policy line become real.
- **The first screen** a new user sees.

Stage 1: three or four per path, enough to make each path tangible and show where they differ. Stage 2: six to ten for the chosen path.

Each screen gets a `for` (which persona, at what moment) and `notes` (why it exists, what decision it embodies) — they appear in the documents and keep the screens honest.

## The file

Stage 1: `plan/paths/<path-id>.screens.json`. Stage 2: `plan/screens.json`. `templates/screens.example.json` is a complete worked example.

```json
{
  "platform": "ios",
  "tokens": { "bg": "#f4f4f1", "surface": "#ffffff", "text": "#15171a", "muted": "#7a7d82",
              "accent": "#2f7d5b", "accent_fg": "#ffffff", "border": "rgba(21,23,26,0.12)", "radius": 12 },
  "hero": ["home", "tool", "manager"],
  "screens": [
    { "id": "home", "title": "Library", "for": "a resident looking for a tool",
      "notes": "Why this screen exists and what decision it embodies.",
      "html": "<div class='title'>Tool library</div>…" }
  ]
}
```

- `platform` is `ios`, `android` or `web`; it picks the frame.
- `tokens` are the design language. In Stage 2 they must match `05-design-language.md`. In Stage 1 a quick palette per path helps the paths feel different.
- `hero` lists the up-to-three screens shown together, best first — the first goes in the middle and largest. Without it, the first three screens are used.
- The story shows a set with `{"type": "screens", "path": "<path-id>"}`, optionally with its own `ids`.

## The building blocks

Screens are short HTML fragments built from a kit of native-looking parts. The kit handles spacing, type, colour, safe areas and the status bar. Icons are `<i data-i="name"></i>`.

| Class | What it is |
|---|---|
| `title`, `sub`, `h`, `section-h` | Large title, grey line under it, section heading, small group label |
| `bar` with `a`, `t`, `a r` | Navigation bar: left action, centre title, right action |
| `search`, `input` | Search field, form field |
| `chips` / `chip` / `chip on` | Horizontal filter pills |
| `list` / `row` | Grouped list; a row holds `ic` or `avatar`, then `tx` with `t` and `s`, then `r` |
| `card`, `grid2` + `card stat` with `k` / `v` | Surfaces and two-up statistic tiles |
| `img`, `img hero`, `img sq`, `img tall` | Image placeholder in the accent colour with a caption |
| `btn`, `btn ghost`, `btn sm` | Buttons |
| `badge`, `note`, `code`, `divider`, `spacer` | Small label, footnote, big code, rule, gap |
| `map` with `pin` | Map with pins at `style="left:30%;top:40%"` |
| `done` with `ok` | Success state |
| `tabbar` / `tab` / `tab on`, `sheet` | Bottom tab bar, bottom sheet |
| `webnav`, `web` | Web navigation bar and centred column |

Icons: home, search, plus, user, users, calendar, map-pin, bell, chat, settings, chevron-right, chevron-left, check, star, camera, wallet, heart, share, clock, ticket, tool, image, filter, more, x, upload, lock, chart, card, phone, doc, building, alert, target, tag, receipt, arrow, play, trend, eye, info, copy.

Inline `style` is allowed for one-off colours and positions. Scripts, styles, forms and event handlers are stripped.

## Making them look good

These screens are judged as images, so craft matters:

- **Real content.** Specific names, realistic prices, plausible counts that match the plan's numbers. Nothing sells a screen like believable content, and nothing kills one like lorem ipsum.
- **One job per screen**, with a clear primary action. Busy screens look worse at hero size than at full size.
- **The hero screen is the richest one** — a populated list, a map with pins, a stat grid — not a sparse form. Put a sparse screen (a confirmation, a paywall) at the sides.
- **Follow the platform.** iOS: large titles, grouped lists, a tab bar. Web: a top navigation bar and a centred column.
- **One accent colour, used deliberately.** It is also the backdrop of the hero image, so pick it as the brand colour, not a default blue.
- **Look at it.** Build the site, open the solution beat, and judge the three phones together as one image. If they don't look like a product you'd want to use, fix the content before the colours.
