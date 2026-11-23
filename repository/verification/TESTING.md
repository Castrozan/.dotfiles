# Testing

## Taxonomy

Test category is the **directory** a test lives in, not its filename. Any module
anywhere in the repo may carry a `__tests__/` directory, split into `unit/`,
`integration/`, and `e2e/`; the runner tiers off those directory names.

- `unit/` — fast, mocked, no system state. The `--quick` (default) gate.
- `integration/` — needs docker, real services, or multi-step subprocess flows.
- `e2e/` — runs against a live system (runtime checks, live desktop and terminal
  behavior, perf thresholds).

Agent LLM tests are a separate axis: the `agent-evals` suites under
`agent-harness/quality/evaluations/suites/`, run through the `dotfiles-evals` wrapper, keep their
own flags (`--evals`, `--integration`, `--e2e`).

## Discovery

`repository/verification/run.sh` is the canonical entry point. Every script-test tier collects
through one shared helper, `_discover_test_files` in `repository/verification/runner/discovery.sh`,
which walks the **whole repo** for `*/__tests__/<tier>/` and prunes `.git`,
`node_modules`, `private-configuration`, `result*`, `.deep-work`, `.direnv`,
`.worktrees`, and `__pycache__`. A new module's tests are picked up with zero
runner edits — there are no hardcoded collection roots.

A tier collects at **any depth** below its tier directory: the path pattern stops
at `*/__tests__/<tier>/*` and the file name is matched separately, so grouping a
tier's files into subdirectories keeps them collected.
`repository/verification/__tests__/unit/test_every_test_file_is_reachable_by_a_tier.py`
fails whenever a test file in the repo sits where no collector reaches it.

Two discovery policies:

- **platform-scoped** (bats, pytest): excludes the capability roots belonging to
  the other platform, because script tests can be platform-specific. macOS reads
  `repository/verification/runner/linux-only-test-roots.txt` and Linux reads
  `darwin-only-test-roots.txt`; `foreign-platform-test-roots.sh` picks between
  them so the collectors and the coverage run agree.
- **cross-platform** (lua, qml): walks both platforms, because those pure-logic
  suites run identically everywhere.

Nix domain checks (`checks.nix`) are not shell-discovered; the flake aggregates
them via `repository/verification/nix-checks/default.nix` and they run under `--nix`. Agent
evals are driven by the `agent-evals` engine, not the shell collectors.

`repository/verification/run.sh --map` prints the whole suite as a tree (module × tier ×
counts: bats `@test` blocks, pytest functions, lua and qml suites, and a
`checks.nix: registered` marker per module) so the structure is self-describing.

The nix check inventory in that map is not counted out of the source.
`repository/verification/map-test-suite.py` evaluates the flake's `checks` attribute
set for the current system and counts the attribute names it gets back, so the total
is the set `--nix` would build rather than a guess at how many `checks.nix` files
declare. When that evaluation cannot run — nix absent, a non-zero exit, a timeout, or
output it cannot parse — the total prints as `unavailable` with the reason instead of a
number, because a wrong count reads exactly like a right one.

## Tiers

| Tier                    | Content                                                                                                                                                                                             | Flag                                       |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| Map                     | prints the discovered suite tree, runs nothing                                                                                                                                                      | `--map`                                    |
| Quick                   | line counts + `unit/` bats + `unit/` pytest + qml + qmllint + lua                                                                                                                                   | `--quick` (default)                        |
| Nix                     | quick + every flake check attribute, built (`*/__tests__/checks.nix`)                                                                                                                               | `--nix`                                    |
| Integration (scripts)   | `integration/` bats + `integration/` pytest                                                                                                                                                         | `--integration-scripts` (alias `--docker`) |
| Runtime / e2e (scripts) | `e2e/` bats + `e2e/` pytest                                                                                                                                                                         | `--runtime`                                |
| CI                      | line counts + `unit/` bats + `integration/` bats + flake checks + both baseline checks                                                                                                              | `--ci`                                     |
| Perf                    | desktop + shell benchmarks, both baseline checks with the age gate, `perf-runtime.bats` thresholds                                                                                                  | `--perf`                                   |
| Agent evals             | `dotfiles-evals run`: every suite under `agent-harness/quality/evaluations/suites/` (`--evals`), or only the `integration_workflows` (`--integration`) or `end_to_end_workflows` (`--e2e`) category | `--evals` / `--integration` / `--e2e`      |

Additional modes: `--all` runs quick + nix + integration-scripts. `--coverage`
runs the `machine-configuration` `unit/` bats through kcov.

`--ci` is its own tier list, not the quick tier with skips. It drops pytest, qml,
qmllint and lua, and adds `integration/` bats, the flake checks, and the rebuild and
desktop baseline checks. Nothing it drops goes unrun: `.github/workflows/tests.yml`
runs pytest, the qml suites, qmllint (with `QMLLINT_REQUIRED` set, so the lint is
mandatory there) and lua in a second job.

## Run

```bash
repository/verification/run.sh                       # quick tier (default)
repository/verification/run.sh --map                 # print the suite tree (module x tier x counts)
repository/verification/run.sh --nix                 # quick + nix eval tests
repository/verification/run.sh --integration-scripts # integration/ bats + pytest (alias: --docker)
repository/verification/run.sh --runtime             # e2e/ script tests (live system)
repository/verification/run.sh --all                 # quick + nix + integration-scripts
repository/verification/run.sh --coverage            # machine-configuration unit/ bats with kcov
repository/verification/run.sh --ci                  # the tier continuous integration runs
repository/verification/run.sh --perf                # benchmarks + fresh-baseline gate + thresholds
```

While editing, run the exact file instead of a tier — the loop is faster and the
failure stays local to what you changed:

```bash
bats machine-configuration/development/development-utilities/__tests__/integration/killport.bats
pytest machine-configuration/development/testing/__tests__/unit/test_dotfiles_perf.py
```

Missing tools do not all fail the same way. Absent bats, nix, kcov or python3 make
their check print a warning and skip. Absent pytest is a failure whenever python test
files were collected: the runner refuses to skip silently and hand back a green run
that inspected nothing. Absent qmllint or quickshell skip too, unless
`QMLLINT_REQUIRED` is set. Docker is not detected by the runner at all — the
docker-backed tests skip themselves through
`repository/verification/helpers/docker-container-assertions.bash`. The `--integration` and
`--e2e` tiers run real agent sessions inside a `bwrap` sandbox that exists only on Linux, so
they report a skip (status 77) wherever `bwrap` is absent, which includes every darwin host.

### Performance testing

```bash
dotfiles-perf run               # benchmark all desktop components
dotfiles-perf run 10 tmux       # benchmark tmux only, 10 iterations
dotfiles-perf check             # compare the latest run against the baseline
dotfiles-perf validate          # validate the tracked desktop baseline
dotfiles-perf test              # pass/fail threshold tests (bats)
dotfiles-perf all               # full suite: benchmark + check + threshold tests
dotfiles-perf baseline          # measure and save new baseline
dotfiles-perf report            # show benchmark history
dotfiles-perf shell             # shell startup benchmark
dotfiles-perf rebuild           # nix rebuild benchmark
```

Validating a baseline and retaking one are different acts, and the runner separates
them. The baseline check validates the tracked file itself: that it parses as a JSON
object, that it records `git_commit`, `host` and `config`, that `threshold_percent` is
a number above zero, and that every measurement carries a value and a ceiling that are
numbers above zero. That runs everywhere, `--ci` included, because reading a committed
file needs no hardware and a malformed baseline should turn a push red wherever it is
noticed.

Baseline age is gated only by `--perf`. It is the one caller that adds
`--require-fresh`, which is what turns a stale or timestamp-less `generated_at` into a
failure, and it applies it to both `benchmark-desktop --check-baseline` and
`benchmark-rebuild --check-baseline`. The gate belongs there because nothing else can
clear it: clearing it means retaking the measurement, and the nix packaging injects
`DOTFILES_BENCHMARK_HOST` from the machine the flake builds the command for, so
`dotfiles-perf baseline` measures the owning host and no other. Continuous integration
therefore never benchmarks — a shared runner's numbers describe no machine this
repository configures. The nightly deep tiers run `--perf` on the owning host itself,
so an expired baseline surfaces in the steward inbox on the one machine that can
retake it, instead of waiting for someone to type the flag. A host never fails on a
baseline another host recorded: the age gate applies only where `DOTFILES_BENCHMARK_HOST`
equals the baseline's recorded `host`.

The nightly runner owns every tier continuous integration cannot reach:
`--integration-scripts`, `--runtime`, `--perf`, `--integration` and `--e2e`. The last
two run real agent sessions through `dotfiles-evals`, which no shared runner can.

A tier that cannot run is not a tier that passed. `--evals`, `--integration` and
`--e2e` return 77, the automake convention for a skipped test, when the tool they
drive is absent. The nightly runner counts that status as neither a pass nor a
failure and names the skipped tiers in its verdict, so a machine that quietly lost
`dotfiles-evals` cannot read as a green night. A night where every
tier skipped proved nothing and fails.

`benchmark-desktop` is packaged on Linux only, so on darwin the `dotfiles-perf`
subcommands that delegate to it report the command as unavailable rather than
producing numbers; `benchmark-rebuild` and `benchmark-shell` are packaged on both.

## What Each Check Proves

These are not interchangeable, and no one of them stands in for another.

- `--ci` proves what a shared Linux runner can prove about a pushed commit: the
  line-count policy, `unit/` and `integration/` bats, every flake check, and that both
  tracked baselines are well formed.
- A named file run directly — `bats <file>`, `pytest <file>` — proves that one file
  with no tier around it. It is the editing loop, and the only form that keeps a
  failure local to the thing you touched.
- `rebuild` proves the Nix modules evaluate and the machine activates. It switches the
  host to the flake in `~/.dotfiles`, and on darwin aborts when `/run/current-system`
  did not move, so an activation that died mid-script cannot pass as success. It
  deploys the main checkout, not a worktree, so what it proves is what is already in
  `~/.dotfiles`.
- Live tests prove behavior on a running machine: a real window server, a real daemon,
  real windows. No automated tier replaces them.
  `machine-configuration/terminal/__tests__/e2e/README.md` says so directly about its
  own stress run, which cannot go in CI at any tier.
- `--perf` measures. A measurement is not a pass/fail claim about a commit; it is a
  number one machine produced under one load. That is why only the owning host
  produces it, and why continuous integration deliberately never runs it.

## Test Categories

| Category                 | Location                                                                                                                      | Requires                          |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| Unit script tests        | `*/__tests__/unit/*.bats`, `.../unit/test_*.py`                                                                               | bats / pytest                     |
| Integration script tests | `*/__tests__/integration/*.bats`, `.../integration/test_*.py`                                                                 | bats / pytest, docker or services |
| E2E script tests         | `*/__tests__/e2e/*.bats`, `.../e2e/test_*.py`                                                                                 | bats / pytest, live system        |
| Lua / QML suites         | `*/__tests__/*_test.lua`, `*/__tests__/qml/run-qml-tests.sh`                                                                  | lua / quickshell                  |
| Domain nix tests         | `*/__tests__/checks.nix`                                                                                                      | nix                               |
| Instruction surface lint | `agent-harness/quality/evaluations/__tests__/unit/instruction-formatting/test_instruction_surfaces_are_structurally_sound.py` | pytest                            |
| Agent evals              | `agent-harness/quality/evaluations/suites/**/*.yaml`                                                                          | agent-evals cli, model access     |

## Pytest Configuration

The root `pytest.ini` is authoritative for every pytest invocation in the repo,
including a bare `pytest` at the root:

- `filterwarnings = error`: a warning fails the run. This is not cosmetic; it is
  what catches leaked file descriptors and sockets, and it is what turns a test
  that reports its outcome by `return True`/`return False` (which pytest ignores)
  into a visible failure instead of a silent pass.
- `--strict-markers`: every `pytest.mark.<name>` must be registered under
  `markers` here. A module-local `pytest.ini` does not help: when the invocation
  spans several directories the rootdir resolves to the repo root and the local
  file is shadowed, so register markers in the root config only.
- `--strict-config`, `xfail_strict`: an unknown ini key or an unexpectedly
  passing xfail fails rather than warns.
- `norecursedirs` mirrors the prune list in `repository/verification/runner/discovery.sh`, so a bare root
  `pytest` never walks into `private-configuration`.
- `python_files = test_*.py` matches the collector's own pattern, so a live
  stress script named `*_test.py` is not collected as a test suite.

## Co-located Domain Tests

Tests live alongside their modules in `<module>/__tests__/`:
`agent-harness/<capability>` and `machine-configuration/<domain>/<capability>`,
both treated alike, split into `unit/`,
`integration/`, and `e2e/` subdirectories. The runner
discovers them by directory (`*/__tests__/<tier>/*.bats` and `*/__tests__/<tier>/test_*.py`)
— the subdirectory **is** the tier. There is no filename-suffix routing.

Bats tests load shared helpers from the root `repository/verification/helpers/` via relative path;
the number of `../` segments is the module's nesting depth (a test in
`machine-configuration/<domain>/<capability>/__tests__/unit/` is five levels deep, so it loads
`'../../../../../repository/verification/helpers/bash-script-assertions'`). Pytest tests resolve the
script under test through a `conftest.py` at the module's `__tests__/` level, which
applies to all three subdirectories.

## What earns a test

A test costs runtime on every push and attention on every change it breaks for. One enters the suite, and stays in it,
only while all seven conditions hold. This is the line for a new test and the cut for an old one.

1. **It discriminates.** Break the behavior it names and it fails. A test that still passes with the behavior broken
   leaves; prove it by breaking the code once before keeping the test.
2. **It guards a cost.** The regression would lose data, break a rebuild or a deployed command, corrupt state another
   tool reads, or cost a debugging session to rediscover. Wording, layout and incidental structure do not pay.
3. **It does not repeat another gate.** What shellcheck, a linter, a type checker, the Nix evaluation or the build
   already proves needs no test, and neither does an assertion that the source contains a given text: it passes exactly
   while the text is there and says nothing about behavior. A rule over source text belongs in lint. Whoever deletes
   such a test names the gate that covers it.
4. **It charges one behavior.** The name states it and every assertion serves it.
5. **It runs at its own level.** `unit/` decides one behavior with no system state; anything that needs a process, a
   service or a container is `integration/`; a live machine is `e2e/`.
6. **It is unique.** No other test charges the same behavior. Of two, the one that discriminates better stays; a
   small finite input space is one exhaustive test and an open one is one property test.
7. **It fits the budget.** `repository/verification/quality/test-budget/budget.json` holds the number of pytest,
   bats and QML tests. A new test over the budget removes another that pays less; the budget never rises, and it is
   lowered in the same change that removes a test.

A test that fails intermittently has its cause fixed in the change that notices it, or leaves; splitting it or
retrying it is not a fix. A test that always fails has the test or the code wrong: correct that one, never skip it.
Code with no test that pays stays without one and shows as uncovered; never write a test to raise coverage.

`dotfiles-lint` enforces the budget and runs shellcheck over every tracked shell script, with or without an extension.
Conditions 1 to 6 are checked in review of the change, against this section.

## What earns an eval

Each eval case costs model tokens and minutes on every measurement. The same seven conditions apply to a case of an AI
instruction, read this way:

1. **It discriminates.** Without the instruction the agent would get it wrong; a case that passes a paired control run
   (`dotfiles-evals run --pareado`) leaves. In its wording the question does not carry the deciding fact, does not
   offer the act as a yes or no, and does not charge practice any model follows unprompted.
2. **It guards a costly decision.** A gate that waits for a person, a routing choice, or an external or irreversible
   write. Style, wording and justification do not pay.
3. **It does not repeat code.** A rule a hook, a lint or a test already enforces leaves the suite, and the deletion
   names that check.
4. **It charges one behavior.** At most two judge criteria, each one claim about the observable act, with no clause
   that grades an explanation, no text copied from the instruction and no negative about something the question did
   not provoke. A required substring is one exact token; a forbidden one is the specific wrong answer.
5. **It runs at its own level.** A unit case charges one decision in one answer; an act or an artifact needs an
   integration case with a staged environment.
6. **It is unique.** No other case charges the same act.
7. **It fits the budget.** A full measurement stays within the execution budget. A new case over it removes another
   or lowers a level's executions; the budget never rises.

A case that passes between 20% and 93% of its runs in two measurements has its cause fixed in the same change or
leaves. A case that always fails has the case or the instruction wrong: correct that one, never the floor. An
instruction with no case that pays stays unmeasured; never invent a case to cover it. The only case of a critical
category is rewritten to one criterion before it is deleted.

`agent-harness/quality/evaluations/__tests__/unit/suites/test_every_case_pays_for_its_execution.py` enforces the
criteria ceiling, the justification and substring rules, and the execution budget. The other conditions are checked
in review of the change, against this section.

## Writing script tests

A `scripts/foo` under a capability is tested by `<capability>/__tests__/<tier>/foo.bats`.
`repository/verification/helpers/bash-script-assertions.bash` resolves the script from the test filename and provides
`run_script_under_test [args...]`, `assert_fails_with "pattern" [args...]` and
`assert_succeeds_with "pattern" [args...]`; all three execute the script.

```bash
#!/usr/bin/env bats

load '../../../../../repository/verification/helpers/bash-script-assertions'

@test "shows usage with no args" {
    assert_fails_with "Usage:"
}
```

Docker-backed tests go under `integration/` and drive the container through
`repository/verification/helpers/docker-container-assertions.bash`, which skips when no docker daemon is reachable.
Shell files under `__tests__/` follow the repository's script conventions, with
`machine-configuration/development/system-rebuild/scripts/rebuild/rebuild` as the worked example.
