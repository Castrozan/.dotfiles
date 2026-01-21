# Dotfiles Testing Plan

## Overview

Testing strategy to maintain code quality when working with AI assistants.

## CI (GitHub Actions) - Lightweight

Memory-safe checks that avoid full Nix builds:

| Check | Memory | Purpose |
|-------|--------|---------|
| statix | Very low | Nix linting |
| deadnix | Very low | Dead code detection |
| nixfmt | Very low | Format validation |
| `nix flake check --no-build` | Low | Eval validation |
| Agent YAML validation | Very low | Frontmatter structure |

**Key**: `--no-build` evaluates without building derivations, avoiding memory issues.

## Local Testing - Heavy

| Component | Tool | Status |
|-----------|------|--------|
| Full rebuilds | `nix build`, `home-manager switch` | - |
| Rebuild benchmarks | Custom script | TODO |
| Shell startup | `hyperfine` | TODO |
| Script tests | `bats` | TODO |
| Agent behavior evals | Claude API | TODO |

## Implementation Progress

- [x] Planning complete
- [ ] Minimal GitHub Actions workflow
- [ ] Flake checks (linting derivations)
- [ ] Benchmark scripts
- [ ] Script tests (bats)
- [ ] Agent YAML validation

## GitHub Actions Strategy

Avoid duplication between push and PR:
- Run on `push` to main
- Run on `pull_request` targeting main
- Skip redundant runs using `concurrency` groups
