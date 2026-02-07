# Dotfiles Workflow

**This file is nix-managed (read-only). Read on-demand when working with dotfiles.**

The dotfiles repo (`~/.dotfiles`) is used by **multiple actors simultaneously** — @userName@, Claude Code agents, and other grid agents.

1. **Pull first**: `git pull --rebase origin main`
2. **Code conduct**: follow conventions and always read dotfiles-expert on /agents
3. **Make changes**: edit, commit locally
4. **Code quality**: lint, format, test with the ci.yaml workflow
5. **Rebuild & test**: with the /rebuild skill or .dotfiles/bin/rebuild — verify it succeeds
6. **Push**: `git push origin main` only after successful rebuild

**Never skip rebuild.** A broken push blocks everyone.
**Always use conventional commits**: `feat(scope)`, `fix(scope)`, `refactor(scope)`, etc.
