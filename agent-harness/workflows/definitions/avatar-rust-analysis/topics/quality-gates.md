# Topic: quality-gates

Context file: {STANDARDS_FILE} (the owner's code standards as numbered rules; the Rust community standards take
precedence wherever they conflict). Also {AVATAR_ROOT}/runtime/README.md.

Set the Rust gates that run in CI and locally from the first slice. Community standards first: rustfmt configuration,
clippy with a justified lint table in `[workspace.lints]`, cargo-deny, cargo-audit or cargo-vet, cargo-nextest, coverage
with cargo-llvm-cov, MSRV, semver checks, the Rust API Guidelines checklist, and `unsafe` policy. Then map every numbered
rule in the standards file to one enforcing tool (clippy thresholds such as too_many_lines, too_many_arguments,
cognitive_complexity, a clippy.toml, ast-grep rules, dylint, a repository check script, a hook) or mark it not enforceable
by code, and say which community rule overrides which owner rule (for example rustdoc on public items against the
no-comments rule). The owner's policy is to reuse existing engines and never build a linter. Specify one local command
that CI also runs, a baseline ratchet equivalent, and the accepted and rejected fixtures each custom rule needs.
