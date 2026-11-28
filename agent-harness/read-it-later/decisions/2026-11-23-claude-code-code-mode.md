# Claude Code Code Mode: scripted multi-step tool calls

**Bundle goal:** Evaluate Claude Code's experimental Code Mode (CLAUDE_CODE_EXPERIMENTAL_CODE_MODE=1) against the workflows direction and the existing hooks, and enable it in the managed Claude Code settings only if hooks and permissions still govern every scripted tool call.

| # | Capture | TL;DR | Action | Why | Already covered | Second Brain direction | Systems | Local | Lucas's note |
|---|---|---|---|---|---|---|---|---|---|
| 1 | [Tweet from Addy Osmani (2026-11-23 00-02-34)](https://x.com/addyosmani/status/2124229492248019362) | Code Mode lets Claude Code write and run JavaScript to chain tool calls in parallel, filter outputs before they reach context and run long commands in the background for up to two hours; each scripted call stays under deny and ask policies, sandbox and PreToolUse hooks. | session | Gather found no commit or Second Brain entry covering the feature, and a search of the dotfiles finds no CLAUDE_CODE_EXPERIMENTAL_CODE_MODE setting. It overlaps the workflows direction for batch work and could change how every Claude Code session on chise runs, so it deserves a hook-compatibility check before anyone enables it. | - | [[Lucas Zanoni - Workflows as the direction for agent work]] | dotfiles | yes | - |

## Session on chise

Done when:
- a Claude Code session started with CLAUDE_CODE_EXPERIMENTAL_CODE_MODE=1 on chise runs a multi-file search-and-filter task and the existing PreToolUse hooks and deny rules still fire on the scripted tool calls
- the finding is recorded: enabled in the dotfiles-managed Claude Code settings, or left off with the concrete reason

Constraints:
- work in a worktree
- never run rebuild or any activation command; chise deploys through its private entrypoint
- leave the setting off if any hook or permission policy is bypassed

Answer on the pull request in plain language: approve the table as it stands, change any card ("drop 3", "session for 2 on kira"), or ask. Captures added after your approval need a new one.

<details><summary>Card data</summary>

<!-- ril-cards -->
```json
{
  "topic_slug": "claude-code-code-mode",
  "title": "Claude Code Code Mode: scripted multi-step tool calls",
  "bundle_goal": "Evaluate Claude Code's experimental Code Mode (CLAUDE_CODE_EXPERIMENTAL_CODE_MODE=1) against the workflows direction and the existing hooks, and enable it in the managed Claude Code settings only if hooks and permissions still govern every scripted tool call.",
  "session": {
    "host": "chise",
    "done_when": [
      "a Claude Code session started with CLAUDE_CODE_EXPERIMENTAL_CODE_MODE=1 on chise runs a multi-file search-and-filter task and the existing PreToolUse hooks and deny rules still fire on the scripted tool calls",
      "the finding is recorded: enabled in the dotfiles-managed Claude Code settings, or left off with the concrete reason"
    ],
    "constraints": [
      "work in a worktree",
      "never run rebuild or any activation command; chise deploys through its private entrypoint",
      "leave the setting off if any hook or permission policy is bypassed"
    ]
  },
  "cards": [
    {
      "linked_urls": [
        "http://code.claude.com/docs/en/code-mode"
      ],
      "covered_evidence": [],
      "second_brain_direction": [
        "[[Lucas Zanoni - Workflows as the direction for agent work]]"
      ],
      "systems": [
        "dotfiles"
      ],
      "runs_locally_on_chise": true,
      "capture": "Tweet from Addy Osmani (2026-11-23 00-02-34).md",
      "tldr": "Code Mode lets Claude Code write and run JavaScript to chain tool calls in parallel, filter outputs before they reach context and run long commands in the background for up to two hours; each scripted call stays under deny and ask policies, sandbox and PreToolUse hooks.",
      "origin_url": "https://x.com/addyosmani/status/2124229492248019362",
      "lucas_note": "",
      "action": "session",
      "reason": "Gather found no commit or Second Brain entry covering the feature, and a search of the dotfiles finds no CLAUDE_CODE_EXPERIMENTAL_CODE_MODE setting. It overlaps the workflows direction for batch work and could change how every Claude Code session on chise runs, so it deserves a hook-compatibility check before anyone enables it.",
      "added_at": "2026-11-23T03:15:59+00:00"
    }
  ]
}
```

</details>
