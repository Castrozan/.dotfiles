# Testing

## Run

```bash
tests/run-all.sh                                    # everything
tests/run-all.sh --coverage                         # with kcov coverage
tests/run-all.sh --runtime                          # include live service tests
bats tests/bin-scripts/                             # bin/ script tests only
bats tests/bin-scripts/killport.bats                # single file
docker build -t dotfiles-test -f tests/Dockerfile . # in Docker
docker run --rm dotfiles-test bats tests/bin-scripts/
```

## Structure

```
tests/
├── run-all.sh                          # entrypoint: runs all test categories
├── Dockerfile                          # Ubuntu 24.04 + Nix test environment
├── bash-coverage.sh                    # kcov coverage for bin/ scripts
├── nix-coverage.sh                     # unused .nix file detection
├── validate-skill-frontmatter.sh       # YAML frontmatter validation for skills
├── TESTING.md
│
├── helpers/
│   └── bash-script-assertions.bash     # shared bats assertions for bin/ tests
│
├── bin-scripts/                        # tests for bin/ shell scripts
│   ├── killport.bats
│   ├── on.bats
│   ├── setup-oom-protection.bats
│   └── tar-unzip2dir.bats
│
├── nix-modules/                        # tests home-manager module evaluation
│   └── home-manager.bats
│
├── openclaw/                           # openclaw-specific tests
│   ├── nix-config.bats                 # nix configuration for both machines
│   └── live-services.bats              # running gateway, systemd, deployed files
│
├── agent-evals/                        # AI agent behavior evaluation (python)
│   ├── run-evals.py
│   └── config/
│
└── coverage/                           # generated coverage output
```

## Test Categories

| Category | Location | Requires | CI |
|---|---|---|---|
| Bin scripts | `tests/bin-scripts/*.bats` | bats | yes |
| Home manager modules | `tests/nix-modules/home-manager.bats` | bats, nix | Docker |
| OpenClaw nix config | `tests/openclaw/nix-config.bats` | bats, nix | Docker |
| OpenClaw live services | `tests/openclaw/live-services.bats` | bats, running services | opt-in (`--runtime`) |
| Skill frontmatter | `tests/validate-skill-frontmatter.sh` | bash | yes |
| Agent evals | `tests/agent-evals/` | claude cli | manual |

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
| `assert_strict_mode` | `set -euo pipefail` in first 5 lines |

**Behavioral** — test script execution:

| Assertion | Usage |
|---|---|
| `run_script [args...]` | Run script under test, sets `$status` and `$output` |
| `assert_fails_with "pattern" [args...]` | Exits non-zero, output contains pattern |
| `assert_succeeds_with "pattern" [args...]` | Exits zero, output contains pattern |

**Static analysis** — test script content without executing:

| Assertion | Usage |
|---|---|
| `assert_contains "regex"` | Script source matches regex |
| `assert_contains_all "a" "b" "c"` | Script source matches all regexes |
| `assert_line_order "first" "second"` | First pattern appears before second |
| `assert_installs_apt_packages pkg1 pkg2` | `apt-get install` lines for each package |
| `assert_writes_config "/path" "val1" "val2"` | Config path and values in source |
| `assert_activates_service name` | `activate_service` or `systemctl enable` for service |

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

@test "is executable"     { assert_is_executable; }
@test "passes shellcheck" { assert_passes_shellcheck; }
@test "uses strict mode"  { assert_strict_mode; }

@test "installs required packages" {
    assert_installs_apt_packages foo bar
}

@test "configures service" {
    assert_writes_config "/etc/foo.conf" "KEY=value"
    assert_activates_service foo
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
5. **Docker for e2e.** Run `docker run --rm --privileged dotfiles-test bash -c 'bin/setup-foo'` to verify setup scripts actually install and configure correctly on Ubuntu.
6. **No external test libraries.** `tests/helpers/bash-script-assertions.bash` covers common assertions. Avoid adding bats-assert/bats-file/bats-mock unless a concrete need arises.
7. **Shellcheck is mandatory.** All bash scripts must pass shellcheck. The `assert_passes_shellcheck` assertion handles environments where shellcheck isn't installed by skipping.
8. **Names mean things.** Test directories mirror source directories. File and function names describe what they test, not how.
