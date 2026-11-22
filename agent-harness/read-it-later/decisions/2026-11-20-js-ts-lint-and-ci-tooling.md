# JS/TS lint rule sets and sub-minute CI tweets

**Bundle goal:** Close out five tweets about the JavaScript and TypeScript toolchain (nkzw oxlint 3.0, the Cloudflare oxlint config, a sub-minute bun CI pipeline and two later captures of Pontus's updated CI prompt tweet); nothing in Lucas's setup changes, and the nkzw tweet is kept as reference.

| # | Capture | TL;DR | Action | Why | Already covered | Second Brain direction | Systems | Local | Lucas's note |
|---|---|---|---|---|---|---|---|---|---|
| 1 | [Tweet from Christoph Nakazawa (2026-11-18 22-39-10)](https://x.com/cnakazawa/status/2122974414098821174) | Christoph Nakazawa shipped @nkzw/oxlint 3.0, an oxlint config tuned to reduce agent mistakes in JS: type-aware rules on the tsrs beta, the anti-slop rules sped up and renamed 'quality', a few rules Seb Mck uses, and sorting split into its own module. | file → Christoph Nakazawa - nkzw oxlint 3.0 for agents (Developer Tooling MOC) | Worth keeping as the newest reference on agent-oriented oxlint rule sets, and it is the base the Cloudflare config builds on. The dotfiles carry a small TypeScript surface and lint it through qlty and ast-grep rules, so there is nothing to adopt wholesale. | Second Brain entry 'Dillon Mulroy - anti-slop oxlint rules' already holds the anti-slop lineage both oxlint tweets build on, and records that its one rule that matters is ported to ast-grep in .qlty/rules/policy.yml | - | - | no | - |
| 2 | [Tweet from Dane Knecht 🦭 (2026-11-20 09-43-19)](https://x.com/dok2001/status/2123697396508954893) | @cloudflare/oxlint-config is on npm: oxlint rules for JS and TS, inspired by Dillon Mulroy's anti-slop rules and built on the nkzw config, with type-aware checks on the tsrs beta. | drop | An npm package announcement that repackages the same anti-slop and nkzw rules; Lucas has no oxlint setup to apply it to, and the Nakazawa card above keeps the lineage and mentions this config. | Second Brain entry 'Dillon Mulroy - anti-slop oxlint rules' covers the anti-slop rules this config is inspired by | - | - | no | - |
| 3 | [Tweet from Pontus Abrahamsson (2026-11-20 10-01-33)](https://x.com/pontusab/status/2123750671795261748) | Pontus Abrahamsson cut a TypeScript CI pipeline under one minute by moving to bun test/check/lint/fmt, filling shards by recorded test time, running only tests the diff can reach, building the app once per process, and running lint, typecheck, build and tests in parallel. | drop | The bun-specific tooling does not apply to the dotfiles pipeline (bats, pytest, Nix), and its transferable ideas, recorded-time shard weights and parallel jobs, already landed in 3f9206ac7 and 74128da12. | 3f9206ac7 perf(ci): parallelize tests and reuse verified coverage artifacts; repository/verification/runner/python/pytest_shards.py already assigns test files to shards by recorded weights; .github/workflows/tests.yml already enforces coverage of changed lines; 74128da12 perf(ci): run Python test shards across four pytest workers | - | - | no | - |
| 4 | [Tweet from Pontus Abrahamsson (2026-11-20 17-47-18)](https://x.com/pontusab/status/2123771160261529982) | Pontus announces an updated prompt to get a CI pipeline under one minute, quoting his bun test, bun check, sharded-by-recorded-time pipeline list. | drop | Same status as the later capture below and the same quoted thread as the 10-01-33 capture already in this group; the origin text carries only the pitch for a prompt and no new tool or step. | Tweet from Pontus Abrahamsson (2026-11-20 10-01-33).md is already a card in this group and quotes the same sub-one-minute CI thread | - | - | no | - |
| 5 | [Tweet from Pontus Abrahamsson (2026-11-20 17-47-29)](https://x.com/pontusab/status/2123771160261529982) | Duplicate capture of the same updated CI prompt tweet, saved eleven seconds later. | drop | Duplicate of the capture saved eleven seconds earlier, with the same origin and the same quoted CI thread already in this group. | Tweet from Pontus Abrahamsson (2026-11-20 10-01-33).md is already a card in this group and quotes the same sub-one-minute CI thread | - | - | no | - |

Answer on the pull request in plain language: approve the table as it stands, change any card ("drop 3", "session for 2 on kira"), or ask. Captures added after your approval need a new one.

<details><summary>Card data</summary>

<!-- ril-cards -->
```json
{
  "topic_slug": "js-ts-lint-and-ci-tooling",
  "title": "JS/TS lint rule sets and sub-minute CI tweets",
  "bundle_goal": "Close out five tweets about the JavaScript and TypeScript toolchain (nkzw oxlint 3.0, the Cloudflare oxlint config, a sub-minute bun CI pipeline and two later captures of Pontus's updated CI prompt tweet); nothing in Lucas's setup changes, and the nkzw tweet is kept as reference.",
  "cards": [
    {
      "linked_urls": [
        "https://npmx.dev/package/@cloudflare/oxlint-config"
      ],
      "covered_evidence": [
        "Second Brain entry 'Dillon Mulroy - anti-slop oxlint rules' already holds the anti-slop lineage both oxlint tweets build on, and records that its one rule that matters is ported to ast-grep in .qlty/rules/policy.yml"
      ],
      "second_brain_direction": [],
      "systems": [],
      "runs_locally_on_chise": false,
      "capture": "Tweet from Christoph Nakazawa (2026-11-18 22-39-10).md",
      "tldr": "Christoph Nakazawa shipped @nkzw/oxlint 3.0, an oxlint config tuned to reduce agent mistakes in JS: type-aware rules on the tsrs beta, the anti-slop rules sped up and renamed 'quality', a few rules Seb Mck uses, and sorting split into its own module.",
      "origin_url": "https://x.com/cnakazawa/status/2122974414098821174",
      "lucas_note": "",
      "action": "file",
      "reason": "Worth keeping as the newest reference on agent-oriented oxlint rule sets, and it is the base the Cloudflare config builds on. The dotfiles carry a small TypeScript surface and lint it through qlty and ast-grep rules, so there is nothing to adopt wholesale.",
      "entry": {
        "title": "Christoph Nakazawa - nkzw oxlint 3.0 for agents",
        "theme_moc": "Developer Tooling MOC",
        "tags": [
          "topic/dev-tools"
        ],
        "why": "An oxlint config built specifically to cut agent mistakes in JavaScript, with the anti-slop rules inside it; the Cloudflare oxlint config (@cloudflare/oxlint-config, tweeted by Dane Knecht on 2026-11-20) is built on it.",
        "what_to_steal": [
          "Port individual rules to ast-grep with the upstream source pinned, as was done for no-chained-type-assertions, instead of adopting the whole plugin",
          "Split style sorting from quality rules so agent-facing lint stays about correctness"
        ],
        "reuse_for": "choosing the next lint rule to port when TypeScript surface grows",
        "creator": "Christoph Nakazawa (@cnakazawa)",
        "platform": "X"
      },
      "added_at": "2026-11-20T13:15:21+00:00"
    },
    {
      "linked_urls": [
        "https://npmx.dev/package/@cloudflare/oxlint-config"
      ],
      "covered_evidence": [
        "Second Brain entry 'Dillon Mulroy - anti-slop oxlint rules' covers the anti-slop rules this config is inspired by"
      ],
      "second_brain_direction": [],
      "systems": [],
      "runs_locally_on_chise": false,
      "capture": "Tweet from Dane Knecht 🦭 (2026-11-20 09-43-19).md",
      "tldr": "@cloudflare/oxlint-config is on npm: oxlint rules for JS and TS, inspired by Dillon Mulroy's anti-slop rules and built on the nkzw config, with type-aware checks on the tsrs beta.",
      "origin_url": "https://x.com/dok2001/status/2123697396508954893",
      "lucas_note": "",
      "action": "drop",
      "reason": "An npm package announcement that repackages the same anti-slop and nkzw rules; Lucas has no oxlint setup to apply it to, and the Nakazawa card above keeps the lineage and mentions this config.",
      "added_at": "2026-11-20T13:15:21+00:00"
    },
    {
      "linked_urls": [],
      "covered_evidence": [
        "3f9206ac7 perf(ci): parallelize tests and reuse verified coverage artifacts; repository/verification/runner/python/pytest_shards.py already assigns test files to shards by recorded weights",
        ".github/workflows/tests.yml already enforces coverage of changed lines",
        "74128da12 perf(ci): run Python test shards across four pytest workers"
      ],
      "second_brain_direction": [],
      "systems": [],
      "runs_locally_on_chise": false,
      "capture": "Tweet from Pontus Abrahamsson (2026-11-20 10-01-33).md",
      "tldr": "Pontus Abrahamsson cut a TypeScript CI pipeline under one minute by moving to bun test/check/lint/fmt, filling shards by recorded test time, running only tests the diff can reach, building the app once per process, and running lint, typecheck, build and tests in parallel.",
      "origin_url": "https://x.com/pontusab/status/2123750671795261748",
      "lucas_note": "",
      "action": "drop",
      "reason": "The bun-specific tooling does not apply to the dotfiles pipeline (bats, pytest, Nix), and its transferable ideas, recorded-time shard weights and parallel jobs, already landed in 3f9206ac7 and 74128da12.",
      "added_at": "2026-11-20T13:15:21+00:00"
    },
    {
      "linked_urls": [],
      "covered_evidence": [
        "Tweet from Pontus Abrahamsson (2026-11-20 10-01-33).md is already a card in this group and quotes the same sub-one-minute CI thread"
      ],
      "second_brain_direction": [],
      "systems": [],
      "runs_locally_on_chise": false,
      "capture": "Tweet from Pontus Abrahamsson (2026-11-20 17-47-18).md",
      "tldr": "Pontus announces an updated prompt to get a CI pipeline under one minute, quoting his bun test, bun check, sharded-by-recorded-time pipeline list.",
      "origin_url": "https://x.com/pontusab/status/2123771160261529982",
      "lucas_note": "",
      "action": "drop",
      "reason": "Same status as the later capture below and the same quoted thread as the 10-01-33 capture already in this group; the origin text carries only the pitch for a prompt and no new tool or step.",
      "added_at": "2026-11-22T20:11:05+00:00"
    },
    {
      "linked_urls": [],
      "covered_evidence": [
        "Tweet from Pontus Abrahamsson (2026-11-20 10-01-33).md is already a card in this group and quotes the same sub-one-minute CI thread"
      ],
      "second_brain_direction": [],
      "systems": [],
      "runs_locally_on_chise": false,
      "capture": "Tweet from Pontus Abrahamsson (2026-11-20 17-47-29).md",
      "tldr": "Duplicate capture of the same updated CI prompt tweet, saved eleven seconds later.",
      "origin_url": "https://x.com/pontusab/status/2123771160261529982",
      "lucas_note": "",
      "action": "drop",
      "reason": "Duplicate of the capture saved eleven seconds earlier, with the same origin and the same quoted CI thread already in this group.",
      "added_at": "2026-11-22T20:11:05+00:00"
    }
  ]
}
```

</details>
