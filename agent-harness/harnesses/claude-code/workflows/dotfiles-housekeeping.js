export const meta = {
  name: "dotfiles-housekeeping",
  description:
    "Two-pass whole-tree housekeeping sweep of the dotfiles repo: find standing rot outside existing checks, then independently refute and rank the candidates.",
  whenToUse:
    "For an explicit housekeeping audit of stale markers, dead code, orphaned files, instruction drift, convention debt, chronic infrastructure traps, and test gaps. Uses at most two model calls, reports only, and writes nothing.",
  phases: [
    { title: "Sweep", detail: "scan every standing-rot dimension" },
    {
      title: "Verify",
      detail: "independently refute candidates and synthesize triage",
    },
  ],
};

const COVERAGE_EXCLUSIONS = `Report only standing rot that no existing check catches. Skip nix idiom, dead bindings, and nix formatting owned by statix, deadnix, and nixfmt. Skip line-count violations, code formatting, hardcoded home paths, identifying names, broken evaluation symlinks, instruction structure, prohibited blanket staging, and anything scoped to the current working diff because repository checks or dotfiles-change-review own them. Skip pure preference.`;

const SWEEP_DIMENSIONS = `Apply all six dimensions in one pass:
1. TODO, FIXME, WIP, XXX, or HACK markers and commented-out code, excluding shebangs, load-bearing expressions, and intentional backlog;
2. unused scripts, files, and broken symlinks, proving absence through imports, globs, filesets, generators, runtime discovery, and PATH lookup;
3. stale, contradictory, or duplicated policy and pointers across core, project context, skills, agents, hooks, evals, and docs;
4. long scripts embedded in nix, compatibility shims, aliases, re-exports, bash used for stateful logic, and unguarded platform-specific configuration;
5. committed private submodule gitlinks that point to unpushed commits, orphaned agent sessions, settings seed ownership gaps, and flake evaluations that omit required submodules;
6. scripts, behavior-bearing modules, or recent bug fixes without focused regression coverage, excluding declarative configuration already proven by rebuild.`;

const FINDINGS_SCHEMA = {
  type: "object",
  properties: {
    findings: {
      type: "array",
      maxItems: 8,
      items: {
        type: "object",
        properties: {
          dimension: { type: "string" },
          file: { type: "string" },
          line: { type: "string" },
          severity: { enum: ["critical", "high", "medium", "low"] },
          title: { type: "string" },
          detail: { type: "string" },
          suggestion: { type: "string" },
        },
        required: ["dimension", "file", "severity", "title", "detail"],
      },
    },
  },
  required: ["findings"],
};

phase("Sweep");
const candidates = await agent(
  `Sweep the dotfiles repository for standing rot. ${SWEEP_DIMENSIONS} ${COVERAGE_EXCLUSIONS} Search the actual tree and history as needed. Try to refute each concern before returning it. Report at most eight actionable findings with a concrete file, location, evidence, and fix. Treat a committed secret or silent deployment failure as critical and an isolated stale marker as low. Keep each detail under 80 words.`,
  {
    label: "sweep",
    phase: "Sweep",
    schema: FINDINGS_SCHEMA,
    model: "haiku",
    maxTurns: 8,
  },
);

phase("Verify");
const report = await agent(
  `Independently verify this dotfiles housekeeping candidate set by reading the actual tree and history. Try hard to refute every candidate. Keep one only when it is standing rot worth cleaning and no existing formatter, linter, test, diff reviewer, import mechanism, glob, generator, intentional backlog, or steward behavior already owns or explains it. Return a markdown triage report under 400 words with no more than five confirmed findings, critical first. Each finding must name its dimension, file and location, evidence, and smallest cleanup. If none survive, say the tree looks clean and name the six dimensions reviewed. Candidates: ${JSON.stringify(candidates?.findings ?? [])}.`,
  {
    label: "verify",
    phase: "Verify",
    model: "sonnet",
    maxTurns: 8,
  },
);

return report;
