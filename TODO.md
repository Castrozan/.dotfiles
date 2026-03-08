## Migrate scripts from shell/bash to Python

All scripts in `bin/` and `tests/` are currently shell/bash. Migrate to Python for better maintainability, error handling, and testability. Use `uv` for dependency management where needed.

### Priority targets

- `bin/` scripts — stateful system automation (brightness, volume, network tuning)
- `tests/run.sh` — test orchestrator
- `agents/evals/validate-skill-frontmatter.sh` — YAML validation
- `tests/cover/bash-coverage.sh` — coverage runner
- `tests/helpers/` — shared test utilities

### Keep as shell

- One-liners and trivial wrappers that just exec another binary
- Nix-generated scripts (substituteAll patterns)
