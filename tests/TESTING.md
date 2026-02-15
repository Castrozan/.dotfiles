# Testing

## Tiers

Tests are organized in tiers by speed and tool requirements. The `tests/run-all.sh` script is the canonical entry point for all tiers.

| Tier | Content | Time | Flag |
|---|---|---|---|
| Quick | skill frontmatter + pure bash bats (excludes `*-docker.bats`) | ~3s | `--quick` (default) |
| Nix | home-manager + openclaw nix eval tests | ~120s | `--nix` (includes quick) |
| Docker | `*-docker.bats` integration tests | ~60s | `--docker` |
| Runtime | live-services.bats (needs running gateway) | variable | `--runtime` |

Additional modes: `--all` runs quick + nix + docker. `--coverage` runs quick tests through kcov. `--ci` runs quick with CI-appropriate skip messages.

## Run

```bash
tests/run-all.sh                    # quick tier (default)
tests/run-all.sh --nix              # quick + nix eval tests
tests/run-all.sh --docker           # docker integration tests only
tests/run-all.sh --all              # everything except runtime
tests/run-all.sh --coverage         # quick tests with kcov coverage
tests/run-all.sh --runtime          # openclaw live service tests
bats tests/bin-scripts/foo.bats     # single test file
```

Each tier auto-detects tool availability (bats, nix, docker, kcov) and skips gracefully with a message when tools are missing.

## Docker Test Naming Convention

Files matching `*-docker.bats` are docker integration tests. They require docker, run inside containers, and are excluded from the quick tier, pre-push hook, CI, and kcov coverage. When adding a new docker integration test, name it `<script>-docker.bats` and it will automatically be routed to the docker tier.

## Test Categories

| Category | Location | Requires |
|---|---|---|
| Bin scripts | `tests/bin-scripts/*.bats` (excluding `*-docker.bats`) | bats |
| Docker integration | `tests/bin-scripts/*-docker.bats` | bats, docker |
| Home manager modules | `tests/nix-modules/home-manager.bats` | bats, nix |
| OpenClaw nix config | `tests/openclaw/nix-config.bats` | bats, nix |
| OpenClaw live services | `tests/openclaw/live-services.bats` | bats, running services |
| Skill frontmatter | `tests/validate-skill-frontmatter.sh` | bash |
| Agent evals | `tests/agent-evals/` | claude cli |

## Writing Bin Script Tests

Test filename must match script name: `bin/foo` → `tests/bin-scripts/foo.bats`.

The shared helper at `tests/helpers/bash-script-assertions.bash` auto-resolves the script path from the test filename.

### Minimal template

```bash
#!/usr/bin/env bats

load '../helpers/bash-script-assertions'

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

load '../helpers/bash-script-assertions'

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

load '../helpers/bash-script-assertions'

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
2. **Test filename = script name.** `bin/foo` → `tests/bin-scripts/foo.bats`. The helper auto-resolves the path.
3. **Static over execution for setup scripts.** Scripts requiring sudo/root are tested via content analysis, not execution. Verify configs, packages, and service activation are declared correctly.
4. **Behavioral tests for CLI scripts.** Scripts that take user input should test error paths (missing args, bad input) and success paths.
5. **Docker for e2e.** Name docker integration test files `*-docker.bats` so they are automatically excluded from the quick tier. Run `docker run --rm --privileged dotfiles-test bash -c 'bin/setup-foo'` to verify setup scripts actually install and configure correctly on Ubuntu.
6. **No external test libraries.** `tests/helpers/bash-script-assertions.bash` covers common assertions. Avoid adding bats-assert/bats-file/bats-mock unless a concrete need arises.
7. **Shellcheck is mandatory.** All bash scripts must pass shellcheck. The `assert_passes_shellcheck` assertion handles environments where shellcheck isn't installed by skipping.
8. **Names mean things.** Test directories mirror source directories. File and function names describe what they test, not how. Follow `agents/core.md` naming and script conventions.
9. **Canonical script pattern.** All shell scripts under `tests/` follow the same pattern as `bin/rebuild`: `set -Eeuo pipefail`, `readonly` constants, `main()` at bottom, `_` prefixed private functions, no comments.
