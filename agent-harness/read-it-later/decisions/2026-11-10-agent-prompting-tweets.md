# Agent prompting tweets: codebase ownership, ID audit and settings trim

**Bundle goal:** Decide what the three saved Claude prompting tweets change for Lucas's own repositories: check the claimed Anthropic guide finding and, if it holds, add the codebase-ownership sentence where Lucas's repository context is defined, keep the canonical-ID audit prompt as a reference beside the implicit state machines prompt, and drop the settings-trim prompt that fights his current setup.

| # | Capture | TL;DR | Action | Why | Already covered | Second Brain direction | Systems | Local | Lucas's note |
|---|---|---|---|---|---|---|---|---|---|
| 1 | [Tweet from bebu (2026-11-10 23-00-20)](https://x.com/bebuu_ai/status/2120080226801820156) | Claims the Fable 5.2 prompting guide says one sentence, "This codebase is yours...", makes the model merge duplicate code and fix nearby bugs in about 50% of runs versus under 10%. | session | a second-hand claim about an Anthropic guide that would change how every session behaves in Lucas's repositories, so it needs checking against the guide first; it is one line of judgment prose, which his workflows note says belongs in instructions | agent-harness/agent-instructions/core-rules/core.md contains no codebase-ownership sentence | [[Lucas Zanoni - Workflows as the direction for agent work]] | dotfiles | yes | - |
| 2 | [Tweet from Dr. Dad, PhD 🔄🔼◀️🔽▶️ (2026-11-08 08-50-08)](https://x.com/GarrettPetersen/status/2119213952106373177) | A one-line audit prompt: find every object in the codebase that is referenced without a stable, canonical ID. | file → Garrett Petersen - Canonical ID audit prompt (Engineering MOC) | a reusable audit prompt with nothing to build on its own, and it pairs with the implicit state machines prompt already in the Second Brain | Inspiration/Steve Ruiz - Implicit state machines prompt.md is the same kind of audit prompt and is already filed | - | - | yes | - |
| 3 | [Tweet from Aaron Delasy (2026-11-08 08-05-51)](https://x.com/aarondelasy/status/2119024883971891207) | A prompt that sets disableBundledSkills, disableWorkflows, disableRemoteControl, disableClaudeAiConnectors and disableArtifact to true in ~/.claude/settings.json to cut Claude Code usage. | drop | two of the five keys are already handled or deliberately kept off, disableWorkflows contradicts his workflows direction, and the usage saving is unmeasured in the tweet; settings here are declared in nix, not hand-edited | agent-harness/harnesses/claude-code/__tests__/remove-claude-managed-settings-nix-darwin-checks.nix:34 requires disableClaudeAiConnectors to stay off because it would drop wanted connectors such as Claude Docs; agent-harness/harnesses/claude-code/settings/global-settings.nix:92 already denies the Artifact tool | [[Lucas Zanoni - Workflows as the direction for agent work]] | dotfiles | yes | - |

## Session on chise

Done when:
- the claim is checked against Anthropic's Fable 5.2 prompting guide, and the outcome is recorded in the session report
- if the guide confirms it, the ownership sentence is in the dotfiles repository context so sessions in Lucas's own repositories read it, with a test that the projected instructions contain it
- if the guide does not confirm it, nothing is changed and the report says what the guide states instead

Constraints:
- scope the sentence to repositories Lucas owns; do not put it in core instructions that also apply to other people's codebases
- work in a worktree and leave ~/.dotfiles clean
- never run rebuild, nixos-rebuild or darwin-rebuild

Answer on the pull request in plain language: approve the table as it stands, change any card ("drop 3", "session for 2 on kira"), or ask. Captures added after your approval need a new one.

<details><summary>Card data</summary>

<!-- ril-cards -->
```json
{
  "topic_slug": "agent-prompting-tweets",
  "title": "Agent prompting tweets: codebase ownership, ID audit and settings trim",
  "bundle_goal": "Decide what the three saved Claude prompting tweets change for Lucas's own repositories: check the claimed Anthropic guide finding and, if it holds, add the codebase-ownership sentence where Lucas's repository context is defined, keep the canonical-ID audit prompt as a reference beside the implicit state machines prompt, and drop the settings-trim prompt that fights his current setup.",
  "session": {
    "host": "chise",
    "done_when": [
      "the claim is checked against Anthropic's Fable 5.2 prompting guide, and the outcome is recorded in the session report",
      "if the guide confirms it, the ownership sentence is in the dotfiles repository context so sessions in Lucas's own repositories read it, with a test that the projected instructions contain it",
      "if the guide does not confirm it, nothing is changed and the report says what the guide states instead"
    ],
    "constraints": [
      "scope the sentence to repositories Lucas owns; do not put it in core instructions that also apply to other people's codebases",
      "work in a worktree and leave ~/.dotfiles clean",
      "never run rebuild, nixos-rebuild or darwin-rebuild"
    ]
  },
  "cards": [
    {
      "capture": "Tweet from bebu (2026-11-10 23-00-20).md",
      "tldr": "Claims the Fable 5.2 prompting guide says one sentence, \"This codebase is yours...\", makes the model merge duplicate code and fix nearby bugs in about 50% of runs versus under 10%.",
      "origin_url": "https://x.com/bebuu_ai/status/2120080226801820156",
      "linked_urls": [],
      "covered_evidence": [
        "agent-harness/agent-instructions/core-rules/core.md contains no codebase-ownership sentence"
      ],
      "second_brain_direction": [
        "[[Lucas Zanoni - Workflows as the direction for agent work]]"
      ],
      "systems": [
        "dotfiles"
      ],
      "runs_locally_on_chise": true,
      "lucas_note": "",
      "action": "session",
      "reason": "a second-hand claim about an Anthropic guide that would change how every session behaves in Lucas's repositories, so it needs checking against the guide first; it is one line of judgment prose, which his workflows note says belongs in instructions",
      "added_at": "2026-11-11T02:24:17+00:00"
    },
    {
      "capture": "Tweet from Dr. Dad, PhD 🔄🔼◀️🔽▶️ (2026-11-08 08-50-08).md",
      "tldr": "A one-line audit prompt: find every object in the codebase that is referenced without a stable, canonical ID.",
      "origin_url": "https://x.com/GarrettPetersen/status/2119213952106373177",
      "linked_urls": [],
      "covered_evidence": [
        "Inspiration/Steve Ruiz - Implicit state machines prompt.md is the same kind of audit prompt and is already filed"
      ],
      "second_brain_direction": [],
      "systems": [],
      "runs_locally_on_chise": true,
      "lucas_note": "",
      "action": "file",
      "reason": "a reusable audit prompt with nothing to build on its own, and it pairs with the implicit state machines prompt already in the Second Brain",
      "entry": {
        "title": "Garrett Petersen - Canonical ID audit prompt",
        "theme_moc": "Engineering MOC",
        "tags": [
          "topic/engineering"
        ],
        "why": "Names a class of defect, objects identified by position, name or object identity instead of a stable ID, in one sentence an agent can run.",
        "what_to_steal": [
          "run it as an audit pass beside the implicit state machines prompt on a codebase before a refactor"
        ],
        "reuse_for": "auditing agent wrappers and data models for unstable identifiers",
        "creator": "Garrett Petersen (@GarrettPetersen)",
        "platform": "X"
      },
      "added_at": "2026-11-11T02:24:17+00:00"
    },
    {
      "capture": "Tweet from Aaron Delasy (2026-11-08 08-05-51).md",
      "tldr": "A prompt that sets disableBundledSkills, disableWorkflows, disableRemoteControl, disableClaudeAiConnectors and disableArtifact to true in ~/.claude/settings.json to cut Claude Code usage.",
      "origin_url": "https://x.com/aarondelasy/status/2119024883971891207",
      "linked_urls": [],
      "covered_evidence": [
        "agent-harness/harnesses/claude-code/__tests__/remove-claude-managed-settings-nix-darwin-checks.nix:34 requires disableClaudeAiConnectors to stay off because it would drop wanted connectors such as Claude Docs",
        "agent-harness/harnesses/claude-code/settings/global-settings.nix:92 already denies the Artifact tool"
      ],
      "second_brain_direction": [
        "[[Lucas Zanoni - Workflows as the direction for agent work]]"
      ],
      "systems": [
        "dotfiles"
      ],
      "runs_locally_on_chise": true,
      "lucas_note": "",
      "action": "drop",
      "reason": "two of the five keys are already handled or deliberately kept off, disableWorkflows contradicts his workflows direction, and the usage saving is unmeasured in the tweet; settings here are declared in nix, not hand-edited",
      "added_at": "2026-11-11T02:24:17+00:00"
    }
  ]
}
```

</details>
