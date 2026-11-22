# codehygiene: a tiny code readability model as a skill

**Bundle goal:** Keep one tweet about brianbell-x/codehygiene, an 11 KB readability model installed as an agent skill, as reference beside the existing complexity lint, and drop its follow-up video capture; nothing in Lucas's setup changes.

| # | Capture | TL;DR | Action | Why | Already covered | Second Brain direction | Systems | Local | Lucas's note |
|---|---|---|---|---|---|---|---|---|---|
| 1 | [Tweet from brian (2026-11-21 10-47-22)](https://x.com/brianbellx/status/2121973517273153540) | codehygiene is described as a weight-space compiled model with 428K ternary parameters, no training, 10 ms CPU latency and 11 KB, that scores code readability and hygiene, installed with npx skills add. | file → brian - codehygiene readability model (Engineering MOC) | A fast local readability signal could complement the complexity lint that already gates functions. The performance claims are the author's own and were not tested, so this is reference only. | Second Brain: Alex Graveley - Complexity lint for agents; cyclomatic complexity above five is already gated in repository/verification/quality/local-lint/findings.py (c74b5ca42) | - | dotfiles | yes | - |
| 2 | [Tweet from brian (2026-11-21 11-05-24)](https://x.com/brianbellx/status/2123914488663474351) | Follow-up video with real examples of what perfectly clean code looks like to codehygiene, quoting the announcement. | drop | The text is a caption for a video and quotes the announcement already filed in this group; the video itself was not watched and adds no tool or step. | Tweet from brian (2026-11-21 10-47-22).md in this group quotes this same codehygiene announcement | - | - | no | - |

Answer on the pull request in plain language: approve the table as it stands, change any card ("drop 3", "session for 2 on kira"), or ask. Captures added after your approval need a new one.

<details><summary>Card data</summary>

<!-- ril-cards -->
```json
{
  "topic_slug": "codehygiene-readability-model",
  "title": "codehygiene: a tiny code readability model as a skill",
  "bundle_goal": "Keep one tweet about brianbell-x/codehygiene, an 11 KB readability model installed as an agent skill, as reference beside the existing complexity lint, and drop its follow-up video capture; nothing in Lucas's setup changes.",
  "cards": [
    {
      "linked_urls": [
        "npx skills add brianbell-x/codehygiene -g"
      ],
      "covered_evidence": [
        "Second Brain: Alex Graveley - Complexity lint for agents; cyclomatic complexity above five is already gated in repository/verification/quality/local-lint/findings.py (c74b5ca42)"
      ],
      "second_brain_direction": [],
      "systems": [
        "dotfiles"
      ],
      "runs_locally_on_chise": true,
      "capture": "Tweet from brian (2026-11-21 10-47-22).md",
      "tldr": "codehygiene is described as a weight-space compiled model with 428K ternary parameters, no training, 10 ms CPU latency and 11 KB, that scores code readability and hygiene, installed with npx skills add.",
      "origin_url": "https://x.com/brianbellx/status/2121973517273153540",
      "lucas_note": "",
      "action": "file",
      "reason": "A fast local readability signal could complement the complexity lint that already gates functions. The performance claims are the author's own and were not tested, so this is reference only.",
      "entry": {
        "title": "brian - codehygiene readability model",
        "theme_moc": "Engineering MOC",
        "tags": [
          "topic/engineering"
        ],
        "why": "A claimed 11 KB, 10 ms CPU model for code readability, installable as a skill.",
        "what_to_steal": [
          "treat a cheap local readability score as a second gate next to the cyclomatic complexity lint",
          "check the claims before adopting: the 428K ternary parameter figure and the zero-training approach come from the author alone"
        ],
        "reuse_for": "code quality gates for agent-written code",
        "creator": "brian (@brianbellx)",
        "platform": "X"
      },
      "added_at": "2026-11-22T20:11:05+00:00"
    },
    {
      "linked_urls": [],
      "covered_evidence": [
        "Tweet from brian (2026-11-21 10-47-22).md in this group quotes this same codehygiene announcement"
      ],
      "second_brain_direction": [],
      "systems": [],
      "runs_locally_on_chise": false,
      "capture": "Tweet from brian (2026-11-21 11-05-24).md",
      "tldr": "Follow-up video with real examples of what perfectly clean code looks like to codehygiene, quoting the announcement.",
      "origin_url": "https://x.com/brianbellx/status/2123914488663474351",
      "lucas_note": "",
      "action": "drop",
      "reason": "The text is a caption for a video and quotes the announcement already filed in this group; the video itself was not watched and adds no tool or step.",
      "added_at": "2026-11-22T20:11:05+00:00"
    }
  ]
}
```

</details>
