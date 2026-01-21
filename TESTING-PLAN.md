# Dotfiles Testing Plan

## Overview

Testing strategy to maintain code quality when working with AI assistants.

## Original Request

> I think we've got to configure some kind of CI or even if we use Github actions. Just make sure we are keeping the same quality when it comes to code linting and when it comes to rebuild speed and when it comes to the minimum packages that we expect and the minimum users that we expect for the flake. So I want you to figure out how can we build a test suite for the dotfiles repo? Just to make sure when we work on the dotfiles through AI, we can make sure the AI keeps a high level of code quality when working with this repository. I want code linting, rebuild speed benchmark, shell loading speed, and tests for most of the scripts that we have, also im thinking of tests for the agent instructions, maybe testing if agents like claude, with the instructions we have set for the repo will follow the minimum of instructions. How can we set this up? I would like to have all of this on github actions, but ive tried sometime ago and the containers dont have enough memory to run nix rebuilds or memory demanding jobs

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
- [x] Minimal GitHub Actions workflow (`.github/workflows/ci.yml`)
- [ ] **Fix flake eval in CI** (blocked by local-only paths - antipattern)
- [ ] Flake checks (linting derivations in flake.nix)
- [ ] Benchmark scripts
- [ ] Script tests (bats)
- [ ] Agent YAML validation

## Known Issues

### Flake not evaluable in CI
The flake currently can't be fully evaluated in CI due to local-only paths:
- `/nix/store/...-claude` referenced by home/modules/claude
- Possibly agenix secrets expecting local keys

This is an antipattern. The flake should evaluate anywhere without requiring local state.

## GitHub Actions Strategy

Avoid duplication between push and PR:
- Run on `push` to main
- Run on `pull_request` targeting main
- Skip redundant runs using `concurrency` groups
