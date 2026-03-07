## Migrate scripts from shell/bash to Python

All scripts in `bin/` and `tests/` are currently shell/bash. Migrate to Python for better maintainability, error handling, and testability. Use `uv` for dependency management where needed.

### Priority targets

- `bin/` scripts — stateful system automation (brightness, volume, network tuning)
- `tests/run-all.sh` — test orchestrator
- `tests/validate-skill-frontmatter.sh` — YAML validation
- `tests/bash-coverage.sh` — coverage runner
- `tests/helpers/` — shared test utilities

### Keep as shell

- One-liners and trivial wrappers that just exec another binary
- Nix-generated scripts (substituteAll patterns)
