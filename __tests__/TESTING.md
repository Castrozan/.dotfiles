# Testing

## Taxonomy

Test category is the **directory** a test lives in, not its filename. Any module
anywhere in the repo may carry a `__tests__/` directory, split into `unit/`,
`integration/`, `e2e/`, and `evals/`; the runner tiers off those directory names.

- `unit/` — fast, mocked, no system state. The `--quick` (default) gate.
- `integration/` — needs docker, real services, or multi-step subprocess flows.
- `e2e/` — runs against a live system (runtime checks, headless browser, perf).
- `evals/` — per-skill LLM eval yamls the `agent-eval` engine auto-discovers.

Agent LLM tests are a separate axis under `agents/evals/{evals,integration,e2e}/`
and keep their own flags (`--evals`, `--integration`, `--e2e`).

## Discovery

`__tests__/run.sh` is the canonical entry point. Every script-test tier collects
through one shared helper, `_discover_test_files` in `__tests__/lib/discovery.sh`,
which walks the **whole repo** for `*/__tests__/<tier>/` and prunes `.git`,
`node_modules`, `private-config`, `result*`, `.deep-work`, `.direnv`,
`.worktrees`, and `__pycache__`. A new module's tests are picked up with zero
runner edits — there are no hardcoded collection roots.

Two discovery policies:

- **platform-scoped** (bats, pytest): excludes the *other* platform's home tree
  (`home/linux` on macOS, `home/darwin` on Linux), because script tests can be
  platform-specific.
- **cross-platform** (lua, qml): walks both platforms, because those pure-logic
  suites run identically everywhere.

Nix domain checks (`checks.nix`) are not shell-discovered; the flake aggregates
them via `__tests__/nix-checks/default.nix` and they run under `--nix`. Agent
evals are driven by the `agent-eval` engine, not the shell collectors.

`__tests__/run.sh --map` prints the whole suite as a tree (module × tier ×
counts: bats `@test` blocks, pytest functions, lua/qml suites, eval yamls, nix
eval-checks) so the structure is self-describing.

## Tiers

| Tier | Content | Flag |
|---|---|---|
| Map | prints the discovered suite tree, runs nothing | `--map` |
| Quick | line counts + `unit/` bats + `unit/` pytest + qml + lua | `--quick` (default) |
| Nix | quick + domain nix checks (`*/__tests__/checks.nix`) | `--nix` |
| Integration (scripts) | `integration/` bats + `integration/` pytest | `--integration-scripts` (alias `--docker`) |
| Runtime / e2e (scripts) | `e2e/` bats + `e2e/` pytest | `--runtime` |
| Perf | desktop + shell benchmarks, baseline checks, threshold tests | `--perf` |
| Agent evals | `agents/evals/` single-turn / sessions / herdr | `--evals` / `--integration` / `--e2e` |

Additional modes: `--all` runs quick + nix + integration-scripts. `--coverage`
runs `unit/` bats through kcov. `--ci` runs quick with CI-appropriate skips.

## Run

```bash
__tests__/run.sh                       # quick tier (default): unit/ only
__tests__/run.sh --map                 # print the suite tree (module x tier x counts)
__tests__/run.sh --nix                 # quick + nix eval tests
__tests__/run.sh --integration-scripts # integration/ bats + pytest (alias: --docker)
__tests__/run.sh --runtime             # e2e/ script tests (live system)
__tests__/run.sh --all                 # quick + nix + integration-scripts
__tests__/run.sh --coverage            # unit/ bats with kcov coverage
__tests__/run.sh --perf                # performance benchmarks + threshold tests
bats home/base/system/__tests__/unit/foo.bats  # single test file
```

### Performance testing

```bash
dotfiles-perf run               # benchmark all desktop components
dotfiles-perf run 10 tmux       # benchmark tmux only, 10 iterations
dotfiles-perf check             # compare latest run against baseline
dotfiles-perf test              # pass/fail threshold tests (bats)
dotfiles-perf all               # full suite: benchmark + check + threshold tests
dotfiles-perf baseline          # measure and save new baseline
dotfiles-perf report            # show benchmark history
dotfiles-perf shell             # shell startup benchmark
dotfiles-perf rebuild           # nix rebuild benchmark
```

Each tier auto-detects tool availability (bats, nix, docker, kcov) and skips gracefully with a message when tools are missing.

## Test Categories

| Category | Location | Requires |
|---|---|---|
| Unit script tests | `*/__tests__/unit/*.bats`, `.../unit/test_*.py` | bats / pytest |
| Integration script tests | `*/__tests__/integration/*.bats`, `.../integration/test_*.py` | bats / pytest, docker or services |
| E2E script tests | `*/__tests__/e2e/*.bats`, `.../e2e/test_*.py` | bats / pytest, live system |
| Lua / QML suites | `*/__tests__/*_test.lua`, `*/__tests__/qml/run-qml-tests.sh` | lua / quickshell |
| Domain nix tests | `*/__tests__/checks.nix` | nix |
| Instruction surface lint | `agents/__tests__/unit/test_instruction_surfaces_are_structurally_sound.py` | pytest |
| A/B instruction-loading record | `agents/evals/instruction-loading-experiment.json` (`agent-eval --ab`) | claude cli to re-measure |
| Agent evals | `agents/evals/{evals,integration,e2e}/`, `agents/skills/*/__tests__/evals/` | claude cli |

## Co-located Domain Tests

Tests live alongside their modules in `<module>/__tests__/` — `home/<domain>`,
`agents/<tool>`, `nixos/modules/<name>`, `hosts/<host>`, all treated alike —
split into `unit/`, `integration/`, and `e2e/` subdirectories. The runner
discovers them by directory (`*/__tests__/<tier>/*.bats` and `*/__tests__/<tier>/test_*.py`)
— the subdirectory **is** the tier. There is no filename-suffix routing.

Bats tests load shared helpers from the root `__tests__/helpers/` via relative path;
the number of `../` segments is the module's nesting depth (a test in
`home/base/<domain>/__tests__/unit/` is five levels deep, so it loads
`'../../../../../__tests__/helpers/bash-script-assertions'`). Pytest tests resolve the
script under test through a `conftest.py` at the module's `__tests__/` level, which
applies to all three subdirectories.

## Writing Bin Script Tests

Test filename must match script name: `bin/foo` → `home/{base,linux,darwin}/<domain>/__tests__/unit/foo.bats` (or `integration/` / `e2e/` for the heavier tiers).

The shared helper at `__tests__/helpers/bash-script-assertions.bash` auto-resolves the script path from the test filename.

### Minimal template

```bash
#!/usr/bin/env bats

load '../../../../../__tests__/helpers/bash-script-assertions'

@test "is executable" {
    assert_is_executable
}

@test "passes shellcheck" {
    assert_passes_shellcheck
}
```

### Available assertions

**Quality gates** — every script test should include these:

| Assertion | Checks |
|---|---|
| `assert_is_executable` | +x permission bit |
| `assert_passes_shellcheck` | shellcheck passes (skips if not installed) |
| `assert_uses_strict_error_handling` | `set -euo pipefail` in first 5 lines |

**Behavioral** — test script execution:

| Assertion | Usage |
|---|---|
| `run_script_under_test [args...]` | Run script under test, sets `$status` and `$output` |
| `assert_fails_with "pattern" [args...]` | Exits non-zero, output contains pattern |
| `assert_succeeds_with "pattern" [args...]` | Exits zero, output contains pattern |

**Static analysis** — test script content without executing:

| Assertion | Usage |
|---|---|
| `assert_script_source_matches "regex"` | Script source matches regex |
| `assert_script_source_matches_all "a" "b" "c"` | Script source matches all regexes |
| `assert_pattern_appears_before "first" "second"` | First pattern appears before second |
| `assert_installs_apt_packages pkg1 pkg2` | `apt-get install` lines for each package |
| `assert_writes_config_to_path "/path" "val1" "val2"` | Config path and values in source |
| `assert_activates_systemd_service name` | `activate_service` or `systemctl enable` for service |

### Example: behavioral test

```bash
#!/usr/bin/env bats

load '../../../../../__tests__/helpers/bash-script-assertions'

@test "is executable"     { assert_is_executable; }
@test "passes shellcheck" { assert_passes_shellcheck; }

@test "shows usage with no args" {
    assert_fails_with "Usage:"
}

@test "processes valid input" {
    assert_succeeds_with "Done" --flag value
}
```

### Example: setup script (static analysis)

```bash
#!/usr/bin/env bats

load '../../../../../__tests__/helpers/bash-script-assertions'

@test "is executable"              { assert_is_executable; }
@test "passes shellcheck"          { assert_passes_shellcheck; }
@test "uses strict error handling"  { assert_uses_strict_error_handling; }

@test "installs required packages" {
    assert_installs_apt_packages foo bar
}

@test "configures service" {
    assert_writes_config_to_path "/etc/foo.conf" "KEY=value"
    assert_activates_systemd_service foo
}
```

### When setup/teardown is needed

Override `setup()` and `teardown()` for tests that need temp files or state. The helper assertions still work because they resolve the script path from the test filename, not from a variable.

```bash
setup() {
    TEST_DIR=$(mktemp -d)
    cd "$TEST_DIR" || return 1
}

teardown() {
    rm -rf "$TEST_DIR"
}
```

## Policies

1. **Every `bin/` script gets a test file.** At minimum: `assert_is_executable` + `assert_passes_shellcheck`.
2. **Test filename = script name, category = directory.** `bin/foo` → `home/{base,linux,darwin}/<domain>/__tests__/unit/foo.bats`. The helper auto-resolves the script path from the filename regardless of which tier directory the test lives in.
3. **Static over execution for setup scripts.** Scripts requiring sudo/root are tested via content analysis, not execution. Verify configs, packages, and service activation are declared correctly.
4. **Behavioral tests for CLI scripts.** Scripts that take user input should test error paths (missing args, bad input) and success paths.
5. **Containerized integration tests go in `integration/`.** Place docker-backed tests under `<domain>/__tests__/integration/`; they run via `--integration-scripts` (alias `--docker`) and stay out of the quick gate by directory, not by filename. Run `docker run --rm --privileged dotfiles-test bash -c 'bin/setup-foo'` to verify setup scripts install and configure correctly on Ubuntu.
6. **No external test libraries.** `__tests__/helpers/bash-script-assertions.bash` covers common assertions. Avoid adding bats-assert/bats-file/bats-mock unless a concrete need arises.
7. **Shellcheck is mandatory.** All bash scripts must pass shellcheck. The `assert_passes_shellcheck` assertion handles environments where shellcheck isn't installed by skipping.
8. **Names mean things.** Test directories mirror source directories. File and function names describe what they test, not how. Follow `agents/core_rules/core.md` naming and script conventions.
9. **Canonical script pattern.** All shell scripts under `__tests__/` follow the same pattern as `home/{base,linux,darwin}/system/scripts/rebuild`: `set -Eeuo pipefail`, `readonly` constants, `main()` at bottom, `_` prefixed private functions, no comments.
