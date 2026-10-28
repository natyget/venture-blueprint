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

## `traps.csv`

The trap sweep from `references/traps.md`. `new_plan.py` seeds every canonical row from `templates/traps.json`; `check_plan.py` requires each one to be present and complete, so a plan cannot pass by quietly dropping a question.

```csv
id,category,question,status,answer,source,verified,step
T01,platform,"For each revenue line separately: is the thing being bought consumed inside the app, or in the real world?","answered","Three lines. Event tickets are consumed in the world, so no store commission. Ad credits and SMS credits are consumed in the app, so they are sold on the web only and the app does not offer them.",https://developer.apple.com/app-store/review/guidelines/,2026-10-28,
T02,platform,"Does anything let a user buy credits, ad spend, boosts, balances or promotion from inside the app?","answered","No. Organizer ad and messaging credits are web-dashboard only, deliberately, so no in-app purchase obligation attaches.",https://developer.apple.com/app-store/review/guidelines/,2026-10-28,W6
T10,users,"Do you capture anything that counts as a biometric identifier, and does any state with a private right of action apply?","n/a","No biometric capture anywhere in the product.",,,
T13,money,"Do you ever hold money belonging to someone else, even briefly?","answered","No. Funds settle directly to the seller's own connected account and we take a platform fee, so no money-transmission exposure.",https://stripe.com/docs/connect,2026-10-28,C4
```

`status` is `answered` or `n/a`, and nothing else — an empty status is an unanswered question, which the validator treats as an error rather than a default. An `answered` row needs both `source` and `verified` (`YYYY-MM-DD`); an `n/a` row needs the reason in `answer`, because "n/a" with no reason is indistinguishable from not having looked. `step` is optional and names the roadmap step that does the work when a trap needs some.

The T01/T02 rows above are a real worked example: a product can owe a store nothing on its main revenue line and still owe commission on a smaller one, which is why the question is answered per revenue line rather than per product. Selling that line on the web only is the design that removes the obligation.

Project-specific traps the research turns up get their own ids (`P01`, `P02`) and are held to the same standard.

## `assumptions.json`

The input to `scripts/model.py`. See `templates/assumptions.example.json` for a complete worked file.

- `customers`: `new_first_month`, `new_growth_monthly`, optional `new_max_per_month`, `churn_monthly`, `cac`, plus a `label` ("organizers", "clinics") used in the output.
- `revenue_lines`: each has a `kind` — `subscription` (price per month), `per_unit` (price × `units_per_customer_month`), `take_rate` (`rate` × `gmv_per_customer_month`) or `one_time` (price per new customer) — plus optional `attach_rate`, `store_commission`, `processing_pct` and `processing_fixed`. Set `store_commission` per line: it is the T01 trap in numbers.
- `variable_costs`: `per_customer_month` and/or `pct_of_revenue`.
- `fixed_costs`: `monthly`, optional `start_month` / `end_month`, and optional `steps` (`at_customers`, `monthly`) for costs that jump at a threshold.
- `scenarios`: multipliers `new_x`, `growth_x`, `churn_x`, `price_x`, `cac_x`. Defaults to conservative / base / optimistic.
- Every block carries a `source`. `TODO` or empty fails the plan-stage check; `UNVERIFIED: …` passes but is listed.

`financials.md` records a hash of the assumptions it was built from, so `check_plan.py` can tell when someone edited the inputs and forgot to rerun the model.

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
