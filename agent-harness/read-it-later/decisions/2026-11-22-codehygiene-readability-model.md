# codehygiene: a tiny code readability model as a skill

**Bundle goal:** Keep three code-quality checkers as reference beside the existing complexity lint, the codehygiene readability model tweet, the deslop-please structural linter repository and the pstack no-comments skill with Matt Pocock's comment-audit prompt, and drop the codehygiene follow-up video capture; nothing in Lucas's setup changes.

| # | Capture | TL;DR | Action | Why | Already covered | Second Brain direction | Systems | Local | Lucas's note |
|---|---|---|---|---|---|---|---|---|---|
| 1 | [Tweet from brian (2026-11-21 10-47-22)](https://x.com/brianbellx/status/2121973517273153540) | codehygiene is described as a weight-space compiled model with 428K ternary parameters, no training, 10 ms CPU latency and 11 KB, that scores code readability and hygiene, installed with npx skills add. | file → brian - codehygiene readability model (Engineering MOC) | A fast local readability signal could complement the complexity lint that already gates functions. The performance claims are the author's own and were not tested, so this is reference only. | Second Brain: Alex Graveley - Complexity lint for agents; cyclomatic complexity above five is already gated in repository/verification/quality/local-lint/findings.py (c74b5ca42) | - | dotfiles | yes | - |
| 2 | [Tweet from brian (2026-11-21 11-05-24)](https://x.com/brianbellx/status/2123914488663474351) | Follow-up video with real examples of what perfectly clean code looks like to codehygiene, quoting the announcement. | drop | The text is a caption for a video and quotes the announcement already filed in this group; the video itself was not watched and adds no tool or step. | Tweet from brian (2026-11-21 10-47-22).md in this group quotes this same codehygiene announcement | - | - | no | - |
| 3 | [GitHub - deterministic-machinesdeslop-please Bring (back) sanity to your code](https://github.com/deterministic-machines/deslop-please) | deslop-please is a Rust linter, installed with cargo install, that flags structural sloppiness (module-cycle, tangle, field-leak, shallow-module) following A Philosophy of Software Design: deep modules, narrow interfaces. It ships an AGENTS.md snippet telling agents to fix findings from first principles and holistically, and an allow-file to mute existing errors. | file → deterministic-machines - deslop-please structural linter (Engineering MOC) | The capture holds only the repository README, with no personal note from Lucas, and I did not run the tool. The existing complexity lint measures function size and does not look at module boundaries, so this is a different signal worth keeping beside it, and the AGENTS.md wording matches his practice of fixing causes instead of hiding them. Nothing is proposed to build until its output is tried on a real repository. | Second Brain: Alex Graveley - Complexity lint for agents; cyclomatic complexity above five is already gated in repository/verification/quality/local-lint/findings.py (c74b5ca42); Same group: the codehygiene tweet is another code-quality checker kept as reference | - | dotfiles | yes | - |
| 4 | [Tweet from lauren (2026-11-24 10-01-41)](https://x.com/poteto/status/2123898792487576021) | lauren (@poteto) points at the /no-comments skill in Cursor's pstack plugin, which spawns a comment-sicko subagent to delete or encode comments, and suggests turning it into a lint rule; she quotes Matt Pocock's prompt that classifies every comment as tautology, excuse, stale or decision record, then bans comments with a ratchet lint rule and a repeatable skill. | file → lauren - pstack no-comments skill (Developer Tooling MOC) | Worth keeping as the reference for the one gap in Lucas's no-comments rule: it lives in instructions and an evaluation grader, with no repository lint that enforces it. The skill itself is Cursor-specific, and a comment-ban ratchet would touch comments the rule deliberately preserves, so nothing is built from it now. | Lucas's core instructions already forbid comments, docstrings, TODO and FIXME notes in owned code; e62d8af21 fix(agent-harness): grade comments and docstrings by parsing the artifact, and agent-harness/quality/evaluations/scripts/__tests__/unit/test_the_no_comments_grader_detects_every_forbidden_form.py, already check the rule in evaluations; no lint rule in .qlty/rules/policy.yml bans comments in the repository itself | - | dotfiles | no | - |

Answer on the pull request in plain language: approve the table as it stands, change any card ("drop 3", "session for 2 on kira"), or ask. Captures added after your approval need a new one.

<details><summary>Card data</summary>

<!-- ril-cards -->
```json
{
  "topic_slug": "codehygiene-readability-model",
  "title": "codehygiene: a tiny code readability model as a skill",
  "bundle_goal": "Keep three code-quality checkers as reference beside the existing complexity lint, the codehygiene readability model tweet, the deslop-please structural linter repository and the pstack no-comments skill with Matt Pocock's comment-audit prompt, and drop the codehygiene follow-up video capture; nothing in Lucas's setup changes.",
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
    },
    {
      "linked_urls": [
        "https://github.com/deterministic-machines/deslop-please",
        "https://crates.io/crates/deslop-please"
      ],
      "covered_evidence": [
        "Second Brain: Alex Graveley - Complexity lint for agents; cyclomatic complexity above five is already gated in repository/verification/quality/local-lint/findings.py (c74b5ca42)",
        "Same group: the codehygiene tweet is another code-quality checker kept as reference"
      ],
      "second_brain_direction": [],
      "systems": [
        "dotfiles"
      ],
      "runs_locally_on_chise": true,
      "capture": "GitHub - deterministic-machinesdeslop-please Bring (back) sanity to your code.md",
      "tldr": "deslop-please is a Rust linter, installed with cargo install, that flags structural sloppiness (module-cycle, tangle, field-leak, shallow-module) following A Philosophy of Software Design: deep modules, narrow interfaces. It ships an AGENTS.md snippet telling agents to fix findings from first principles and holistically, and an allow-file to mute existing errors.",
      "origin_url": "https://github.com/deterministic-machines/deslop-please",
      "lucas_note": "",
      "action": "file",
      "reason": "The capture holds only the repository README, with no personal note from Lucas, and I did not run the tool. The existing complexity lint measures function size and does not look at module boundaries, so this is a different signal worth keeping beside it, and the AGENTS.md wording matches his practice of fixing causes instead of hiding them. Nothing is proposed to build until its output is tried on a real repository.",
      "entry": {
        "title": "deterministic-machines - deslop-please structural linter",
        "theme_moc": "Engineering MOC",
        "tags": [
          "topic/engineering"
        ],
        "why": "A linter for module-level structure (cycles, tangles, leaked fields, shallow modules) aimed at agent-written code, rooted in deep modules and narrow interfaces.",
        "what_to_steal": [
          "pair a structure lint with the cyclomatic complexity lint so agent code is gated on module boundaries as well as function size",
          "borrow its AGENTS.md rules: fix flagged structure from first principles, fix leaks holistically, and draw a before and after diagram"
        ],
        "reuse_for": "code quality gates for agent-written code",
        "creator": "deterministic-machines",
        "platform": "GitHub"
      },
      "added_at": "2026-11-23T22:12:55+00:00"
    },
    {
      "linked_urls": [
        "https://github.com/cursor/plugins/blob/main/pstack/skills/no-comments/SKILL.md"
      ],
      "covered_evidence": [
        "Lucas's core instructions already forbid comments, docstrings, TODO and FIXME notes in owned code",
        "e62d8af21 fix(agent-harness): grade comments and docstrings by parsing the artifact, and agent-harness/quality/evaluations/scripts/__tests__/unit/test_the_no_comments_grader_detects_every_forbidden_form.py, already check the rule in evaluations; no lint rule in .qlty/rules/policy.yml bans comments in the repository itself"
      ],
      "second_brain_direction": [],
      "systems": [
        "dotfiles"
      ],
      "runs_locally_on_chise": false,
      "capture": "Tweet from lauren (2026-11-24 10-01-41).md",
      "tldr": "lauren (@poteto) points at the /no-comments skill in Cursor's pstack plugin, which spawns a comment-sicko subagent to delete or encode comments, and suggests turning it into a lint rule; she quotes Matt Pocock's prompt that classifies every comment as tautology, excuse, stale or decision record, then bans comments with a ratchet lint rule and a repeatable skill.",
      "origin_url": "https://x.com/poteto/status/2123898792487576021",
      "lucas_note": "",
      "action": "file",
      "reason": "Worth keeping as the reference for the one gap in Lucas's no-comments rule: it lives in instructions and an evaluation grader, with no repository lint that enforces it. The skill itself is Cursor-specific, and a comment-ban ratchet would touch comments the rule deliberately preserves, so nothing is built from it now.",
      "entry": {
        "title": "lauren - pstack no-comments skill",
        "theme_moc": "Developer Tooling MOC",
        "tags": [
          "topic/dev-tools",
          "topic/engineering"
        ],
        "why": "Two takes on removing code comments from an agent-written codebase: Cursor's pstack /no-comments skill, where a fresh-perspective subagent flags comments and constraint comments are offered as type, test or lint encodings, and Matt Pocock's prompt that classifies each comment as tautology, excuse, stale or decision record.",
        "what_to_steal": [
          "Turn a constraint comment into the cheapest in-scope type, runtime, test or CI check, then delete the comment",
          "Classify comments as tautology, excuse, stale or decision record, and move decision records to an ADR instead of keeping them inline",
          "Ban comments with a ratchet lint rule so a repository can adopt it without deleting every comment in one pull request"
        ],
        "reuse_for": "deciding whether to enforce the no-comments rule with a deterministic lint in the dotfiles instead of only instructions and an evaluation grader",
        "creator": "lauren (@poteto)",
        "platform": "X"
      },
      "added_at": "2026-11-24T13:17:29+00:00"
    }
  ]
}
```

</details>
