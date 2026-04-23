# Heartbeat

## Current objective
Make `cla`, `cl`, `cla`, `clau`, `claud`, `cal`, `ca`, and `claude` launch a workspace-isolated Claude session that loads local workspace skills plus injected `/core` and `/personal-skills`, while using generic core instructions from `agents/core.md`.

Add a `personal-skills` skill with a Python script that lists personal skill vault metadata and filesystem paths so the agent can inspect personal-only skills without loading the full personal skill set into every session.

Keep the global `~/.claude/CLAUDE.md` sourced from `agents/core.md`.

## Next steps
1. Update the workspace launcher tests to require injected `core` and `personal-skills`.
2. Change the Python launcher to load those two skills by default before optional `--extend` merging.
3. Verify the global `~/.claude/CLAUDE.md` wiring still mirrors `agents/core.md`.
4. Format, commit, rebuild, and run `tests/run.sh --nix`.
