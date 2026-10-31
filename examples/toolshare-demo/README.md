# Example: ToolShare, at the end of the brainstorm stage

Three ways to build one idea — neighbours sharing tools — told the way the skill tells every plan. Download `venture.html` and open it in a browser.

- **Map** — ToolShare in the centre with its verdict; the case branching around it in reading order. Green moss where a beat is backed by sources (Apple's store rules), red where it's a risk (the consumer app), grey where it's still a guess.
- **Story** — press Story, then the arrow keys: the idea, what the research found, each path with its numbers or its product, the recommendation, and the test to run first.

The numbers are rough estimates marked `UNVERIFIED`, as they should be at this stage, and the verdict says so: *promising, not yet proven*. Even so, the site makes three things obvious: the consumer app loses more money the faster it grows, selling to buildings pays for itself by month 5, and everything hinges on price — which is what to test first.

- `story.json` — the case, beat by beat
- `paths/*.json` — each path's assumptions
- `paths/*.screens.json` — each path's screens, shown as product imagery
- `venture.html` — the generated site

This folder holds only what the site is built from. A real plan folder also has the brief and `paths.md`, which `check_plan.py` requires, so running the checker here reports those two as missing.
