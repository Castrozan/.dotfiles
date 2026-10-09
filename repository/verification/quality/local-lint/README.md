# Local quality checks

`dotfiles-lint` runs Qlty CLI and Nix-packaged analyzers on the working tree.
Configuration and exceptions live in Git under `.qlty/`; no account, hosted
analysis, API token, or editor integration is required. Telemetry and upgrade
checks are disabled. The same command runs locally and in CI.

Run from the repository root:

```sh
dotfiles-lint --all
dotfiles-lint repository/verification/quality/local-lint
dotfiles-lint --base origin/main
dotfiles-lint --all --json
dotfiles-lint --all --output .quality-results/local-lint.json
```

Paths and `--base` select code to analyze. Duplication compares selected code
against the repository; secret detection, custom-rule tests, the 200-line code
file limit, and the 15-entry directory limit always check the repository.
Analyzer failures produce a failed result, even when other analyzers succeed.
Runs use two worker threads, two lint jobs, and bounded subprocess timeouts.

Qlty supplies multi-language complexity and duplication analysis. Native
linters cover Python, JavaScript, TypeScript, shell, Markdown, and Nix.
Ast-grep supplies custom syntax rules, including Nix and Lua patterns; add
valid and invalid examples alongside each rule. QML lint remains in the
existing QML checks. Grammar support and rule depth differ by language;
this does not provide universal interprocedural taint analysis.

## Existing findings

`.qlty/baseline.json` records existing findings by identity, score, and count.
The gate rejects new findings, higher scores, and additional occurrences.
Function cyclomatic complexity above five is a finding. Recorded exceptions
allow existing code to be repaired incrementally.

After repairs, `dotfiles-lint --all --write-baseline` removes resolved
exceptions and lowers recorded scores. It refuses to absorb new findings or
write after an analyzer failure. Initialization requires a complete scan.
Reports omit source snippets, and secret findings redact detected values.

## Coverage migration

`dotfiles-coverage-check` uses diff-cover with standard Cobertura XML reports:

```sh
dotfiles-coverage-check .coverage-reports/python-coverage.xml \
  .coverage-reports/swift-coverage.xml --compare-branch origin/main
```

CI requires at least 65% coverage of changed executable lines represented in
the Python and Swift reports. Files without coverage data remain unmeasured.
The comparison uses the pull request base or the preceding push revision;
it replaces Sonar's hosted new-code window. New duplication findings are
blocked rather than measured against Sonar's 3% density threshold. Sonar's
manual security-hotspot review percentage has no local equivalent; local
security and secret findings use the same blocking gate as other findings.

Qlty CLI runs independently of the hosted Qlty Cloud service.
