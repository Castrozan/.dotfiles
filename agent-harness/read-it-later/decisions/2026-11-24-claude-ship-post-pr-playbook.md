# Claude Ship: handing PR follow-up to /ship and /steward

**Bundle goal:** Keep Anthropic's playbook for Claude Ship (/code-review, /ship, /steward, REVIEW.md and the steward house-rules skill) as reference beside the fleet steward that already looks after dotfiles pull requests; nothing in Lucas's setup changes.

| # | Capture | TL;DR | Action | Why | Already covered | Second Brain direction | Systems | Local | Lucas's note |
|---|---|---|---|---|---|---|---|---|---|
| 1 | [Tweet from ClaudeDevs (2026-11-24 21-33-09)](https://x.com/ClaudeDevs/status/2125365668463993091) | ClaudeDevs links Addy Osmani's playbook for Claude Ship: run /code-review before pushing, /ship to commit, open, review and then watch a PR for up to seven days, /steward to watch an existing PR, and record repeated lessons in CLAUDE.md, REVIEW.md, a verify skill and a steward house-rules skill. | file → Addy Osmani - Claude Ship post-PR playbook (AI Agent Skills MOC) | Anthropic's own account of the post-PR tools Lucas's fleet steward already builds on, worth keeping for its file conventions and watch limits. Nothing is adopted now: the fleet steward already does this work, and /ship refuses to commit in a public repository like the dotfiles. | agent-harness/harnesses/clawde/agents/steward/repository-ci-instructions.md already runs the fleet steward on top of the upstream steward skill, with forge-based CI watching and nightly deep-tier repair; The dotfiles repository is public, where the post says /ship will not commit pending changes, so the fleet steward remains the path for this repository; The repository has no REVIEW.md, .claude/skills/steward/SKILL.md or .claude/skills/verify/SKILL.md today | [[Lucas Zanoni - Workflows as the direction for agent work]] | dotfiles | yes | - |

Answer on the pull request in plain language: approve the table as it stands, change any card ("drop 3", "session for 2 on kira"), or ask. Captures added after your approval need a new one.

<details><summary>Card data</summary>

<!-- ril-cards -->
```json
{
  "topic_slug": "claude-ship-post-pr-playbook",
  "title": "Claude Ship: handing PR follow-up to /ship and /steward",
  "bundle_goal": "Keep Anthropic's playbook for Claude Ship (/code-review, /ship, /steward, REVIEW.md and the steward house-rules skill) as reference beside the fleet steward that already looks after dotfiles pull requests; nothing in Lucas's setup changes.",
  "cards": [
    {
      "linked_urls": [
        "https://claude.dev/blog/the-work-after-you-open-a-pr/"
      ],
      "covered_evidence": [
        "agent-harness/harnesses/clawde/agents/steward/repository-ci-instructions.md already runs the fleet steward on top of the upstream steward skill, with forge-based CI watching and nightly deep-tier repair",
        "The dotfiles repository is public, where the post says /ship will not commit pending changes, so the fleet steward remains the path for this repository",
        "The repository has no REVIEW.md, .claude/skills/steward/SKILL.md or .claude/skills/verify/SKILL.md today"
      ],
      "second_brain_direction": [
        "[[Lucas Zanoni - Workflows as the direction for agent work]]"
      ],
      "systems": [
        "dotfiles"
      ],
      "runs_locally_on_chise": true,
      "capture": "Tweet from ClaudeDevs (2026-11-24 21-33-09).md",
      "tldr": "ClaudeDevs links Addy Osmani's playbook for Claude Ship: run /code-review before pushing, /ship to commit, open, review and then watch a PR for up to seven days, /steward to watch an existing PR, and record repeated lessons in CLAUDE.md, REVIEW.md, a verify skill and a steward house-rules skill.",
      "origin_url": "https://x.com/ClaudeDevs/status/2125365668463993091",
      "lucas_note": "",
      "action": "file",
      "reason": "Anthropic's own account of the post-PR tools Lucas's fleet steward already builds on, worth keeping for its file conventions and watch limits. Nothing is adopted now: the fleet steward already does this work, and /ship refuses to commit in a public repository like the dotfiles.",
      "entry": {
        "title": "Addy Osmani - Claude Ship post-PR playbook",
        "theme_moc": "AI Agent Skills MOC",
        "tags": [
          "topic/engineering"
        ],
        "why": "The official map of which file each Claude Ship tool reads (CLAUDE.md for conventions, REVIEW.md for review-only rules, .claude/skills/verify for exercising a change, .claude/skills/steward for PR house rules) and the safety limits of the local watch.",
        "what_to_steal": [
          "Promote a repeated review comment to a rule only after it appears on at least two pull requests, and delete rules that stop paying",
          "Keep PR house rules (flaky checks to re-run once, commands to run before pushing, design comments left to the author) in a .claude/skills/steward/SKILL.md marked user-invocable false and disable-model-invocation true",
          "Escalate after three pushes on the same issue instead of a fourth attempt",
          "A repository-level PreToolUse or PermissionRequest hook on Bash blocks the local watch, and the watch's own commits skip git hooks, so required checks belong in CI and branch rules"
        ],
        "reuse_for": "deciding where the fleet steward's repository rules should live if Code Review or PR Steward is ever enabled on a repository",
        "creator": "Addy Osmani (Claude Code team)",
        "platform": "X"
      },
      "added_at": "2026-11-25T00:51:28+00:00"
    }
  ]
}
```

</details>
