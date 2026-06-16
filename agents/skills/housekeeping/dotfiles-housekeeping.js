export const meta = {
  name: "dotfiles-housekeeping",
  description:
    "Recurring whole-tree housekeeping sweep of the dotfiles repo: one scanner per standing-rot dimension, adversarially refute each finding, then synthesize a severity-ranked triage report. Report-only, writes nothing.",
  whenToUse:
    "Ad-hoc 'housekeeping time' cleanups: surface stale markers, dead code, orphaned files, instruction drift, convention debt, chronic infra traps, and test gaps that the diff-reviewer and the linters never see.",
  phases: [
    {
      title: "Sweep",
      detail: "one scanner per rot dimension over the whole tree",
    },
    { title: "Verify", detail: "adversarially refute each candidate finding" },
    {
      title: "Synthesize",
      detail: "merge survivors into a prioritized triage report",
    },
  ],
};

const COVERAGE_MAP_EXCLUSIONS = `Report only standing rot that NOTHING else catches. Never flag what existing tooling already owns, or the report floods and Lucas stops reading it:
- nix idiom, dead bindings, nix formatting -> statix, deadnix, nixfmt in the nix-lint CI
- any file over the 200-line hard limit -> check-line-counts.py and the post-tool-use hook
- code formatting -> the auto-format hook
- hardcoded home paths, employer-identifying names, agents/evals/config broken symlinks -> test_repo_hygiene.py
- SKILL.md missing frontmatter or an unresolved backtick sub-file reference -> validate-skill-frontmatter.sh
- git add -A or git add . inside scripts -> the prohibited-command guard test
- anything scoped to a specific uncommitted working diff -> that is the dotfiles-change-review workflow, not this one
Skip anything a formatter or the lists above already handle, and skip pure preference.`;

const DIMENSIONS = [
  {
    key: "stale-markers-and-dead-code",
    title: "Stale markers and dead code",
    focus:
      "TODO/FIXME/WIP/XXX/HACK markers and blocks of commented-out code anywhere in the tree; the repo forbids comments entirely so these are real rot",
    scan: "Grep for the marker words and for contiguous commented-out code blocks across the tree.",
    boundary:
      "A shebang, a load-bearing nix or python # expression, and a comment in a grandfathered legacy file that carried it before are NOT findings. Flag the marker or the dead block, never every # line.",
  },
  {
    key: "orphaned-files",
    title: "Orphaned files and dead symlinks",
    focus:
      "scripts under */scripts/ and bin/ and .config/scripts/ referenced by no .nix, .py, .sh, .yaml, .json, or .md anywhere, and broken symlinks outside the zone test_repo_hygiene.py already covers",
    scan: "List candidate scripts, then grep the whole tree for each basename. Run find for broken symlinks.",
    boundary:
      "A script referenced only through a nix glob, lib.fileset, a directory-wide source, or a runtime PATH lookup is NOT orphaned. Resolve globs before flagging, and default to keep when a reference is plausible.",
  },
  {
    key: "instruction-drift",
    title: "Instruction and doc drift",
    focus:
      "prose pointers in SKILL.md, CLAUDE.md, core.md, and READMEs that name a skill, script, path, or flag that was since moved or deleted, plus stale hardcoded dates",
    scan: "Grep instruction files for 'use the X skill', 'run scripts/Y', and absolute paths, then check each referent still exists.",
    boundary:
      "The SKILL.md frontmatter and backtick sub-file references are already validated, so skip those. A pointer that still resolves is not drift.",
  },
  {
    key: "convention-debt",
    title: "Convention debt",
    focus:
      "inline writeShellScript or writeText blocks past the ~10-line rule that should be extracted to scripts/, backward-compatible shims or aliases or re-exports the repo forbids, bash where python 3.12 is the default, and platform-specific code not guarded by isNixOS or isDarwin",
    scan: "Grep .nix for writeShellScript/writeText with long bodies, for alias/shim/compat wording, and for systemd/launchd/desktopItems without a platform guard.",
    boundary:
      "A short inline script under the line rule, and platform code already guarded upstream of the call, are not findings.",
  },
  {
    key: "chronic-infra-traps",
    title: "Chronic infra traps",
    focus:
      "the durable foot-guns this repo hits repeatedly: an uncommitted private-config submodule gitlink bump, orphaned tmux sessions left by disabled agents, the settings-seed allowlist missing a live runtime key, and nix eval call sites that omit ?submodules=1 for private-config",
    scan: "Run git submodule status and flag a leading +. Grep for nix eval call sites touching private-config without ?submodules=1, and check the settings-seed allowlist against the runtime keys it must cover.",
    boundary:
      "An in-flight gitlink the steward will reconcile is normal state, not a finding; only flag a gitlink bump that is staged or committed in the superproject yet points at an unpushed submodule commit.",
  },
  {
    key: "test-coverage-gaps",
    title: "Test coverage gaps",
    focus:
      "scripts under bin/ or */scripts/ and nix modules with behavior but no corresponding test under tests/ or a checks.nix, and recent bug-fix commits that landed without a regression test",
    scan: "List executable scripts and modules, then check for a matching test file. Skim git log for fix/revert commits and check whether a test accompanied them.",
    boundary:
      "Pure declarative config a rebuild already verifies needs no separate test. Only flag real logic left unguarded.",
  },
];

const FINDINGS_SCHEMA = {
  type: "object",
  properties: {
    findings: {
      type: "array",
      items: {
        type: "object",
        properties: {
          file: { type: "string" },
          line: { type: "string" },
          severity: { enum: ["critical", "high", "medium", "low"] },
          title: { type: "string" },
          detail: { type: "string" },
          suggestion: { type: "string" },
        },
        required: ["file", "severity", "title", "detail"],
      },
    },
  },
  required: ["findings"],
};

const VERDICT_SCHEMA = {
  type: "object",
  properties: {
    holds: { type: "boolean" },
    reason: { type: "string" },
  },
  required: ["holds", "reason"],
};

const swept = await pipeline(
  DIMENSIONS,
  (dimension) =>
    agent(
      `Sweep the dotfiles repository for one standing-rot dimension only: ${dimension.title}. Look for ${dimension.focus}. ${dimension.scan} False-positive boundary you must respect: ${dimension.boundary}\n\n${COVERAGE_MAP_EXCLUSIONS}\n\nReport only real, actionable rot with a concrete file and location and a fix suggestion. Severity floor: a committed secret-shaped string or a deployment-silent failure is critical, a stray marker is low.`,
      {
        label: `sweep:${dimension.key}`,
        phase: "Sweep",
        schema: FINDINGS_SCHEMA,
      },
    ),
  (review, dimension) =>
    parallel(
      (review?.findings ?? []).map(
        (finding) => () =>
          agent(
            `Adversarially verify this housekeeping finding by reading the actual code, and try hard to REFUTE it. It holds only if it is real standing rot worth cleaning; default to holds=false when the file is referenced via a glob, the marker is intentional backlog, the concern is already owned by existing tooling, the gitlink is normal in-flight steward state, or it is mere preference. Finding: ${JSON.stringify(
              finding,
            )}`,
            {
              label: `verify:${dimension.key}:${finding.file}`,
              phase: "Verify",
              schema: VERDICT_SCHEMA,
            },
          ).then((verdict) => ({
            ...finding,
            dimension: dimension.key,
            verdict,
          })),
      ),
    ),
);

const confirmedFindings = swept
  .flat()
  .filter(Boolean)
  .filter((finding) => finding.verdict && finding.verdict.holds);

phase("Synthesize");
const report = await agent(
  `Synthesize a dotfiles housekeeping triage report from these confirmed findings. Lead with critical and high, then medium, each grouped by dimension with file and location, the rot, and the suggested cleanup. Collapse the low pile into a single count line ("N low-severity markers, ask to list") rather than enumerating it. Deduplicate overlaps across dimensions. End with a short "clean these first" list naming the one to three items most worth fixing now. If there are no confirmed findings, say the tree looks clean and name the dimensions swept. Confirmed findings: ${JSON.stringify(
    confirmedFindings,
  )}.`,
  { label: "synthesize", phase: "Synthesize" },
);

return report;
