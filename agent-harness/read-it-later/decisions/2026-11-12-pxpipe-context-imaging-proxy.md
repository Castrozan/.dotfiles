# pxpipe: rendering Claude Code context as images

**Bundle goal:** Keep the pxpipe context-imaging proxy as reference with its model caveats; nothing in Lucas's Claude Code setup changes.

| # | Capture | TL;DR | Action | Why | Already covered | Second Brain direction | Systems | Local | Lucas's note |
|---|---|---|---|---|---|---|---|---|---|
| 1 | [Tweet from bebu (2026-11-12 20-50-49)](https://x.com/bebuu_ai/status/2120782516038865270) | pxpipe is a local proxy (pxpipe warp -- claude) that renders Claude Code's system prompt, tool docs and old history as dense PNGs, reported as $42.21 down to $6.06 on one session. | file → teamchong - pxpipe context imaging proxy (Developer Tooling MOC) | A real, active, MIT-licensed project (teamchong/pxpipe, pushed 2026-11-11) with a measured idea worth keeping, but the tweet overstates it. The README's own table puts the $42.21 to $6.06 run on original claude-fable-5 (13/15 dense hex); claude-opus-5-5 reads 0/15 to 3/15 and sits in a gist-only tier, fable-5-1 and fable-5-2 need extra row spacing, and the README says savings track uncached bulk the client re-sends. Imaging CLAUDE.md and the system prompt would also let the model misread exact rules, so a session to adopt it is not proposed. | agent-harness/harnesses/claude-code/docs/context-management.md section Token Cost and Caching already names cache_read re-reads as the cost driver and sets the levers: small working set, delegation, /clear, output caps, 1-hour cache TTL on the subscription; no Second Brain entry or dotfiles reference mentions pxpipe or text-as-image context compression | - | - | yes | - |

Answer on the pull request in plain language: approve the table as it stands, change any card ("drop 3", "session for 2 on kira"), or ask. Captures added after your approval need a new one.

<details><summary>Card data</summary>

<!-- ril-cards -->
```json
{
  "topic_slug": "pxpipe-context-imaging-proxy",
  "title": "pxpipe: rendering Claude Code context as images",
  "bundle_goal": "Keep the pxpipe context-imaging proxy as reference with its model caveats; nothing in Lucas's Claude Code setup changes.",
  "cards": [
    {
      "linked_urls": [
        "https://github.com/teamchong/pxpipe"
      ],
      "covered_evidence": [
        "agent-harness/harnesses/claude-code/docs/context-management.md section Token Cost and Caching already names cache_read re-reads as the cost driver and sets the levers: small working set, delegation, /clear, output caps, 1-hour cache TTL on the subscription",
        "no Second Brain entry or dotfiles reference mentions pxpipe or text-as-image context compression"
      ],
      "second_brain_direction": [],
      "systems": [],
      "runs_locally_on_chise": true,
      "capture": "Tweet from bebu (2026-11-12 20-50-49).md",
      "tldr": "pxpipe is a local proxy (pxpipe warp -- claude) that renders Claude Code's system prompt, tool docs and old history as dense PNGs, reported as $42.21 down to $6.06 on one session.",
      "origin_url": "https://x.com/bebuu_ai/status/2120782516038865270",
      "lucas_note": "",
      "action": "file",
      "reason": "A real, active, MIT-licensed project (teamchong/pxpipe, pushed 2026-11-11) with a measured idea worth keeping, but the tweet overstates it. The README's own table puts the $42.21 to $6.06 run on original claude-fable-5 (13/15 dense hex); claude-opus-5-5 reads 0/15 to 3/15 and sits in a gist-only tier, fable-5-1 and fable-5-2 need extra row spacing, and the README says savings track uncached bulk the client re-sends. Imaging CLAUDE.md and the system prompt would also let the model misread exact rules, so a session to adopt it is not proposed.",
      "entry": {
        "title": "teamchong - pxpipe context imaging proxy",
        "theme_moc": "Developer Tooling MOC",
        "tags": [
          "topic/dev-tools"
        ],
        "why": "Token cost depends on image pixels, not on the text inside, so dense static context such as the system prompt and tool docs is cheaper as a picture; the README publishes per-model reader scores that show where it fails.",
        "what_to_steal": [
          "measure a context-compression idea per model with exact-recall benchmarks, not one headline cost number",
          "profitability gate: transform only where the math wins, pass everything else through byte-identical",
          "warp wrapper that diverts one client's traffic without overriding the base URL"
        ],
        "reuse_for": "judging any proxy that rewrites agent context before it reaches the model",
        "creator": "teamchong",
        "platform": "GitHub"
      },
      "added_at": "2026-11-13T00:08:55+00:00"
    }
  ]
}
```

</details>
