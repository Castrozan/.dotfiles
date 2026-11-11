# Browser Use 1.0.0 on raw CDP

**Bundle goal:** Keep the Browser Use 1.0.0 announcement as reference for the raw CDP direction the browser skill already takes.

| # | Capture | TL;DR | Action | Why | Already covered | Second Brain direction | Systems | Local | Lucas's note |
|---|---|---|---|---|---|---|---|---|---|
| 1 | [Tweet from Browser Use (2026-11-10 19-19-32)](https://x.com/browser_use/status/2119983662162952278) | Browser Use 1.0.0 deletes 90% of the library: the agent writes a Python REPL on raw CDP, claimed up to 50% better, 2-5x cheaper and 2-3x faster, with a request to pin versions. | file → Browser Use - 1.0.0 raw CDP agent (Developer Tooling MOC) | confirms that fewer predefined actions and a raw CDP channel work for a web agent, which matches the browser skill, but the numbers are the vendor's own and there is nothing to build now | agent-harness/agent-instructions/skills/workstation/browser/SKILL.md already drives the browser through Chrome DevTools CLI over CDP; agent-harness/harnesses/claude-code/mcps/mcp-server-injection-partition.nix:11 names a browser-use MCP server | [[Lucas Zanoni - Workflows as the direction for agent work]] | dotfiles | no | - |

Answer on the pull request in plain language: approve the table as it stands, change any card ("drop 3", "session for 2 on kira"), or ask. Captures added after your approval need a new one.

<details><summary>Card data</summary>

<!-- ril-cards -->
```json
{
  "topic_slug": "browser-use-raw-cdp",
  "title": "Browser Use 1.0.0 on raw CDP",
  "bundle_goal": "Keep the Browser Use 1.0.0 announcement as reference for the raw CDP direction the browser skill already takes.",
  "cards": [
    {
      "capture": "Tweet from Browser Use (2026-11-10 19-19-32).md",
      "tldr": "Browser Use 1.0.0 deletes 90% of the library: the agent writes a Python REPL on raw CDP, claimed up to 50% better, 2-5x cheaper and 2-3x faster, with a request to pin versions.",
      "origin_url": "https://x.com/browser_use/status/2119983662162952278",
      "linked_urls": [],
      "covered_evidence": [
        "agent-harness/agent-instructions/skills/workstation/browser/SKILL.md already drives the browser through Chrome DevTools CLI over CDP",
        "agent-harness/harnesses/claude-code/mcps/mcp-server-injection-partition.nix:11 names a browser-use MCP server"
      ],
      "second_brain_direction": [
        "[[Lucas Zanoni - Workflows as the direction for agent work]]"
      ],
      "systems": [
        "dotfiles"
      ],
      "runs_locally_on_chise": false,
      "lucas_note": "",
      "action": "file",
      "reason": "confirms that fewer predefined actions and a raw CDP channel work for a web agent, which matches the browser skill, but the numbers are the vendor's own and there is nothing to build now",
      "entry": {
        "title": "Browser Use - 1.0.0 raw CDP agent",
        "theme_moc": "Developer Tooling MOC",
        "tags": [
          "topic/dev-tools"
        ],
        "why": "A browser agent library removed its predefined state and action space and got better, cheaper and faster results by letting the model write Python against raw CDP.",
        "what_to_steal": [
          "prefer a thin raw CDP channel the model scripts over a fixed action vocabulary",
          "pin the version of a fast-shipping agent library"
        ],
        "reuse_for": "judging changes to the browser skill and any browser worker",
        "creator": "Browser Use (@browser_use)",
        "platform": "X"
      },
      "added_at": "2026-11-11T02:24:17+00:00"
    }
  ]
}
```

</details>
