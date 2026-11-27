# tack: a pinning system to replace Nix flake inputs

**Bundle goal:** Keep vimjoyer's tack video as a Nix tooling reference; the dotfiles stay on flake inputs and nothing in Lucas's setup changes.

| # | Capture | TL;DR | Action | Why | Already covered | Second Brain direction | Systems | Local | Lucas's note |
|---|---|---|---|---|---|---|---|---|---|
| 1 | [Tweet from Yurii Melnychenko (2026-11-27 10-52-07)](https://x.com/vimjoyer/status/2126093782647210405) | vimjoyer's 6.5 minute video 'I Replaced Nix Flake Inputs With This', on tack (manic-systems/tack, 314 stars), a TOML pin file plus lock that Nix reads without flakes, with branch and tag following, patch following, input grouping, rollbacks and commit signature checks. | file → vimjoyer - tack Nix input pinning (Developer Tooling MOC) | Swapping flake inputs for tack would rework the dependencies sub-flake, flake.lock and every flake-based rebuild and CI path, and nothing breaks today. Its update, rollback and patch-following ideas are still worth keeping as a reference. Answer 'session' if you want a run that trials tack on one input group instead. | the dotfiles pin everything through flake inputs: repository/flake-assembly/dependencies/flake.nix owns every input and flake.lock holds 117 locked nodes; agent-harness/agent-instructions/skills/services/nix/references/repo.md documents the dependencies sub-flake as the only indirection Nix accepts for inputs; no file in the dotfiles mentions tack, npins or niv, and no Second Brain entry has this source | - | dotfiles | yes | - |

Answer on the pull request in plain language: approve the table as it stands, change any card ("drop 3", "session for 2 on kira"), or ask. Captures added after your approval need a new one.

<details><summary>Card data</summary>

<!-- ril-cards -->
```json
{
  "topic_slug": "tack-nix-input-pinning",
  "title": "tack: a pinning system to replace Nix flake inputs",
  "bundle_goal": "Keep vimjoyer's tack video as a Nix tooling reference; the dotfiles stay on flake inputs and nothing in Lucas's setup changes.",
  "session": null,
  "cards": [
    {
      "linked_urls": [
        "https://www.youtube.com/watch?v=MS_iZlr-XKI",
        "https://github.com/manic-systems/tack",
        "https://docs.manic.systems/tack"
      ],
      "covered_evidence": [
        "the dotfiles pin everything through flake inputs: repository/flake-assembly/dependencies/flake.nix owns every input and flake.lock holds 117 locked nodes",
        "agent-harness/agent-instructions/skills/services/nix/references/repo.md documents the dependencies sub-flake as the only indirection Nix accepts for inputs",
        "no file in the dotfiles mentions tack, npins or niv, and no Second Brain entry has this source"
      ],
      "second_brain_direction": [],
      "systems": [
        "dotfiles"
      ],
      "runs_locally_on_chise": true,
      "capture": "Tweet from Yurii Melnychenko (2026-11-27 10-52-07).md",
      "tldr": "vimjoyer's 6.5 minute video 'I Replaced Nix Flake Inputs With This', on tack (manic-systems/tack, 314 stars), a TOML pin file plus lock that Nix reads without flakes, with branch and tag following, patch following, input grouping, rollbacks and commit signature checks.",
      "origin_url": "https://x.com/vimjoyer/status/2126093782647210405",
      "lucas_note": "",
      "action": "file",
      "reason": "Swapping flake inputs for tack would rework the dependencies sub-flake, flake.lock and every flake-based rebuild and CI path, and nothing breaks today. Its update, rollback and patch-following ideas are still worth keeping as a reference. Answer 'session' if you want a run that trials tack on one input group instead.",
      "entry": {
        "title": "vimjoyer - tack Nix input pinning",
        "theme_moc": "Developer Tooling MOC",
        "tags": [
          "topic/dev-tools"
        ],
        "why": "A maintained alternative to flake inputs that keeps a lock file but adds update management flakes lack.",
        "what_to_steal": [
          "group inputs so related pins update together",
          "follow upstream patches automatically on top of a pinned revision",
          "verify commit signatures when bumping a pin",
          "user-defined short URLs like myforge:user/repo for private forges"
        ],
        "reuse_for": "a future rethink of how the dotfiles pin and update their 100+ inputs",
        "creator": "vimjoyer (@vimjoyer)",
        "platform": "X"
      },
      "added_at": "2026-11-27T14:08:00+00:00"
    }
  ]
}
```

</details>
