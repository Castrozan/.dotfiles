# bootvine: systemd boot screen tool

**Bundle goal:** Close out one tweet about bootvine, a Rust boot screen for systemd; chise deliberately hides boot output, so nothing in Lucas's setup changes.

| # | Capture | TL;DR | Action | Why | Already covered | Second Brain direction | Systems | Local | Lucas's note |
|---|---|---|---|---|---|---|---|---|---|
| 1 | [Tweet from sysxplore (2026-11-14 11-55-02)](https://x.com/sysxplore/status/2120882263348892017) | bootvine v0.1.3, a GPL-3.0 Rust tool that replaces boot log output with a live tree of pending systemd jobs and a timeline of the slowest units. | drop | chise already boots quiet on purpose (commit 201f5fe99 keeps boot status off the console), the tool is a v0.1.3 cosmetic boot screen that needs a systemd initrd chise does not use, and the tweet has no link beyond itself. Flip to file if you want it kept as a reference. | 201f5fe99 fix(chise): keep boot status off the tuigreet console; machine-configuration/machines/chise/system/nixos-system.nix sets boot.consoleLogLevel = 3, boot.initrd.verbose = false and the kernel parameters quiet and systemd.show_status=error; no boot.initrd.systemd setting exists under machine-configuration/machines/chise, and bootvine needs a systemd initrd to show early boot | - | dotfiles | no | - |

Answer on the pull request in plain language: approve the table as it stands, change any card ("drop 3", "session for 2 on kira"), or ask. Captures added after your approval need a new one.

<details><summary>Card data</summary>

<!-- ril-cards -->
```json
{
  "topic_slug": "bootvine-boot-screen",
  "title": "bootvine: systemd boot screen tool",
  "bundle_goal": "Close out one tweet about bootvine, a Rust boot screen for systemd; chise deliberately hides boot output, so nothing in Lucas's setup changes.",
  "cards": [
    {
      "linked_urls": [],
      "covered_evidence": [
        "201f5fe99 fix(chise): keep boot status off the tuigreet console",
        "machine-configuration/machines/chise/system/nixos-system.nix sets boot.consoleLogLevel = 3, boot.initrd.verbose = false and the kernel parameters quiet and systemd.show_status=error",
        "no boot.initrd.systemd setting exists under machine-configuration/machines/chise, and bootvine needs a systemd initrd to show early boot"
      ],
      "second_brain_direction": [],
      "systems": [
        "dotfiles"
      ],
      "runs_locally_on_chise": false,
      "capture": "Tweet from sysxplore (2026-11-14 11-55-02).md",
      "tldr": "bootvine v0.1.3, a GPL-3.0 Rust tool that replaces boot log output with a live tree of pending systemd jobs and a timeline of the slowest units.",
      "origin_url": "https://x.com/sysxplore/status/2120882263348892017",
      "lucas_note": "",
      "action": "drop",
      "reason": "chise already boots quiet on purpose (commit 201f5fe99 keeps boot status off the console), the tool is a v0.1.3 cosmetic boot screen that needs a systemd initrd chise does not use, and the tweet has no link beyond itself. Flip to file if you want it kept as a reference.",
      "added_at": "2026-11-14T15:01:36+00:00"
    }
  ]
}
```

</details>
