# The three machine-readable artifacts

These sit beside the documents in the plan directory. They exist so that the validator can enforce the bar mechanically and the build briefs can be generated rather than written by hand. Keep them in step with the prose — where they disagree, the artifact is what tooling believes.

## `decisions.json`

Every choice, with what you rejected and why. The rejected list is what stops a settled debate reopening in month four.

```json
{
  "venture": "Acme",
  "updated": "2026-10-28",
  "decisions": [
    {
      "id": "D1",
      "phase": 4,
      "topic": "mobile-client",
      "chosen": "Native: Swift/SwiftUI + Kotlin/Compose",
      "rejected": [
        { "option": "React Native", "why": "Camera, background upload and the photo pipeline all need native modules anyway, so the saving is partly illusory" },
        { "option": "Flutter", "why": "Platform-review friction on camera and photo permissions; smaller hiring pool in this market" }
      ],
      "because": "The core loop is camera to background upload to gallery, which is the part users judge and the part a bridge taxes most",
      "costs": "Two codebases; features land about 1.4x slower after the shared API",
      "revisit_if": "The roadmap shifts to form-heavy surfaces where the loop does not dominate",
      "sources": [{ "ref": "https://example.com/docs", "verified": "2026-10-28" }]
    }
  ]
}
```

`topic` is free text, but use the same value as the architecture layer or the phase's subject so the validator can tell that each Phase 4 layer has a decision. Decisions from any phase belong here — the price, the rail order, the build-vs-rent calls, the wedge itself.

## `compliance.csv`

One row per obligation. A row whose `step` is empty or names a step that does not exist in `roadmap.json` is an obligation nobody will do, and the validator treats that as an error.

```csv
feature,regime,requirement,posture,approach,step,evidence,source,verified,counsel
face match,TX CUBI (Bus. & Com. 503.001),Notice and consent before capturing a biometric identifier; destruction deadline after purpose,in force,implement,A7,consent log row + retention job,https://statutes.capitol.texas.gov/...,2026-10-28,required
face match,IL BIPA,Written release before collection; private right of action,in force,design away,A6,on-device matching only; no template stored server-side,https://www.ilga.gov/...,2026-10-28,required
invite SMS,TCPA + 10DLC,Prior express written consent; working STOP; carrier registration,in force,implement,H3,consent record + opt-out state in user table,https://www.fcc.gov/...,2026-10-28,no
accounts,Apple 5.1.1(v),Account deletion available in app,in force,implement,A12,delete endpoint + UI path,https://developer.apple.com/app-store/review/guidelines/,2026-10-28,no
```

`posture` is one of `in force`, `enjoined`, `effective <date>`, `proposed`. `approach` is one of `implement`, `design away`, `avoid feature`. `counsel` is `required` or `no`.

## `roadmap.json`

The steps, the gates, and the things that cannot be undone. `scripts/parallel_brief.py` reads this to generate the build briefs and to prove that concurrent workstreams own disjoint files.

```json
{
  "venture": "Acme",
  "updated": "2026-10-28",
  "workstreams": [
    { "id": "contracts", "branch": "build/contracts", "blocking": true,
      "paths": ["packages/contracts/"] },
    { "id": "api", "branch": "build/api", "blocking": false },
    { "id": "web", "branch": "build/web", "blocking": false },
    { "id": "human", "branch": null, "blocking": false }
  ],
  "steps": [
    {
      "id": "C1",
      "workstream": "contracts",
      "anchor": "packages/contracts/src/events.ts",
      "change": "Define the event taxonomy from plan/06-growth.md as typed constants, plus cities.json and the shared enums",
      "why": "Every client imports this, so a drift test can fail instead of a report quietly breaking",
      "risk": "A missing event means a consumer invents its own name. Low, the list is enumerated",
      "test": "npm run test:contracts",
      "pass": "Every event in the plan's list is present and the parity test passes in all three consumers",
      "revert": "Revert the commit; no consumer depends on it yet",
      "effort_hours": 2,
      "depends": [],
      "files": ["packages/contracts/src/events.ts", "packages/contracts/src/cities.json"],
      "human": false,
      "irreversible": false,
      "tier": "must",
      "user_facing": false
    },
    {
      "id": "H1",
      "workstream": "human",
      "anchor": "Texas SOS filing + registered agent",
      "change": "Form the entity, obtain the EIN, appoint a registered agent",
      "why": "Blocks the bank account, which blocks the payment processor, which blocks any paid step",
      "risk": "Lead time. Filing and EIN can take days to weeks",
      "test": "Formation certificate and EIN letter in hand",
      "pass": "Both documents received",
      "revert": "Not practical once filed",
      "effort_hours": 3,
      "depends": [],
      "files": [],
      "human": true,
      "irreversible": true,
      "tier": "must",
      "blocks": ["api", "web"],
      "lead_time_days": 21
    }
  ],
  "gates": [
    { "check": "npm run test:analytics && npm run test:contracts", "pass": "exit 0" },
    { "check": "Funnel script from plan/06-growth.md on a physical device", "pass": "Every step's expected event and parameter values observed" },
    { "check": "Asset coverage check over every route and size", "pass": "No missing images and no fallback-template hits" },
    { "check": "Compliance rows with counsel=required reviewed", "pass": "All signed off" }
  ],
  "cannot_undo": [
    "Tracking consent answers once a user responds",
    "A published package version",
    "A sent invite batch",
    "An activated analytics data filter — it drops data permanently"
  ]
}
```

Notes that matter for the tooling:

- `tier` is `must`, `should` or `can-follow` — the cut line from Phase 9.
- `files` is the ownership claim. Be exhaustive: `parallel_brief.py` refuses to emit briefs when two workstreams with no dependency path between them claim the same path.
- `binary_only: true` marks a step that must ship in a native binary rather than an over-the-air update, because that decides whether a late cut is possible.
- `user_facing: true` means the validator expects an `event` field naming its measurement, so that Phase 6's rule holds mechanically.
- `blocks` and `lead_time_days` on human steps let the plan schedule them first in wall-clock time.
- Step ids are short and stable (`C1`, `A7`, `W4`, `H1`) because the compliance register and the prose both point at them.
