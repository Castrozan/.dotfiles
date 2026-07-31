---
name: claude-harness
description: How the Claude Code and Codex harnesses actually behave - settings and config resolution, transcript and project-dir layout, hooks, MCP and connector gating, subagent and model routing, token budgets, and the tool quirks that make a command land somewhere you did not intend. Read when debugging the harness itself rather than the code it is editing.
---

<orientation>
This covers the harness a session runs inside, not the project it is working on. Reach for it when a symptom is about
Claude Code or Codex themselves: a setting that will not stick, a skill or connector that never loads, a subagent that
cost more than expected, a transcript that cannot be found, a hook that does not fire, or a tool that acted on the
wrong target. Almost every one of these is a documented shape rather than a defect, and `knowledge.md` holds them.
</orientation>

<settings_are_nix_sourced_and_mutable>
`~/.claude/settings.json` is deliberately mutable, because the harness and the user both write runtime keys to it that
a read-only symlink would reject. Home-manager renders the declarative config to a `.nix-source` sibling and an
activation seeds the mutable copy from it, with the nix source authoritative on key collisions, so a key dropped from
nix disappears on the next rebuild while live-only keys survive. Anything loaded at session start, a settings key or an
instruction surface, stays dormant in an already-running session even after a green rebuild, so never verify such a
change from the rebuild alone.
</settings_are_nix_sourced_and_mutable>

<verify_against_the_harness_not_the_config>
The recurring failure in this domain is trusting a file instead of the running process. A listing shows a skill that
was silently skipped, a config names a model the resumed session ignores, a statusline shows a number the harness never
recomputed, and a built-in subagent runs a model nothing in the interface names. Ask the harness what it actually
loaded, compare live state across panes, and check the version before assuming a documented default still holds.
</verify_against_the_harness_not_the_config>

<knowledge>
`knowledge.md` holds the traps: the project-directory slug rule, model routing and the split weekly budgets, the
Codex hook protocol and its wrapper, skill and connector discovery gates, and the tool-anchoring rule that keeps a
command from acting on the wrong repository.
</knowledge>
