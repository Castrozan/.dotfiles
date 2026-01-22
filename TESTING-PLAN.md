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
| Rebuild benchmarks | `benchmark-rebuild` | Done |
| Shell startup | `benchmark-shell` | Done |
| Script tests | `bats` | Done |
| Script coverage | `kcov` | Done |
| Nix module coverage | `nix-coverage.sh` | Done |
| Agent behavior evals | `agent-eval` | Done |

## Implementation Progress

- [x] Planning complete
- [x] Minimal GitHub Actions workflow (`.github/workflows/ci.yml`)
- [x] Flake eval in CI (enabled)
- [ ] Flake checks (linting derivations in flake.nix)
- [x] Benchmark scripts (`benchmark-rebuild`, `benchmark-shell`)
- [x] Script tests (bats - `tests/scripts/*.bats`)
- [x] Agent YAML validation (`tests/validate-agents.sh`)
- [x] Script coverage (`tests/coverage.sh` - requires kcov)
- [x] Nix module coverage (`tests/nix-coverage.sh`)
- [x] Agent behavior evals (`agent-eval`, `tests/agents/`)

## GitHub Actions Strategy

Avoid duplication between push and PR:
- Run on `push` to main
- Run on `pull_request` targeting main
- Skip redundant runs using `concurrency` groups

## Agent Evals

Test that Claude agents follow instructions correctly. Uses Claude Max subscription via CLI - **no API costs!**

**Location:** `tests/agents/`
**Runner:** `agent-eval` command (available after rebuild)

**Local only** - Run manually when changing:
- `agents/**`
- `home/modules/claude/**`

**Test categories:**
- `core_rules`: Delegation, git rules, safety
- `subagents`: Agent-specific behavior
- `hooks`: Hook functionality (placeholder)
- `skills`: Skill execution (placeholder)

**Usage:**
```bash
agent-eval --smoke          # Quick sanity check (~5s)
agent-eval --dry-run        # Show what would run
agent-eval --category core_rules
agent-eval --test delegates_to_subagent
agent-eval                  # Run all tests
```

**Requirements:** Claude Code CLI installed (via `rebuild`)
