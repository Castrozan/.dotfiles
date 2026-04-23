# Heartbeat

## Current objective
Make `cla`, `cl`, `cla`, `clau`, `claud`, `cal`, `ca`, and `claude` launch a workspace-isolated Claude session that loads only local workspace skills plus generic core instructions from `agents/core.md`.

Add a `personal-skills` skill with a Python script that lists personal skill vault metadata and filesystem paths so the agent can inspect personal-only skills without loading the full personal skill set into every session.

## Next steps
1. Add tests for the isolated workspace launcher and the personal skill metadata indexer.
2. Replace the inline `claude-workspace` shell logic with a dedicated Python launcher script and a minimal config allowlist.
3. Point shell aliases and the fish `claude` function at `claude-workspace`.
4. Add `agents/skills/personal-skills/` and its script.
5. Format, commit, rebuild, and run `tests/run.sh --nix`.
