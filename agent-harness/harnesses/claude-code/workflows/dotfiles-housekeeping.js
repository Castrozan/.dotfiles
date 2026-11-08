export const meta = {
  name: "dotfiles-housekeeping",
  description:
    "Slice one dotfiles subtree, read every slice twice for standing rot and real defects, then independently refute and rank the candidates.",
  whenToUse:
    "For an explicit housekeeping audit of one subtree: stale markers, dead code, orphaned files, instruction drift, convention debt, chronic infrastructure traps, test gaps, and real defects. Pass args {root, subtree}. Reports only and writes nothing. Uses one slicer, up to 24 Haiku readers, and five Sonnet verifiers.",
  phases: [
    { title: "Slice", detail: "numbered artifacts of the subtree" },
    { title: "Read", detail: "one reader per slice" },
    { title: "Second look", detail: "one reviewer per slice" },
    { title: "Verify", detail: "five verifiers refute the candidates" },
  ],
};

const instructionData = (value) =>
  "`" + JSON.stringify(value).replaceAll("`", "\\u0060") + "`";

const COVERAGE_EXCLUSIONS =
  "### Coverage exclusions\n\nReport only standing rot that no existing check catches. Skip nix idiom, dead bindings, and nix formatting owned by\nstatix, deadnix, and nixfmt. Skip line-count violations, code formatting, hardcoded home paths, identifying names,\nbroken evaluation symlinks, instruction structure, prohibited blanket staging, and anything a repository check or the\npre-push change-review procedure already owns. Skip pure preference.";

const SWEEP_DIMENSIONS =
  "### Sweep dimensions\n\nApply all seven dimensions in one pass: 1) TODO, FIXME, WIP, XXX, or HACK markers and commented-out code, excluding\nshebangs, load-bearing expressions, and intentional backlog; 2) unused scripts, files, and broken symlinks, proving\nabsence through imports, globs, filesets, generators, runtime discovery, and PATH lookup; 3) stale, contradictory, or\nduplicated policy and pointers across core, project context, skills, agents, hooks, evals, and docs;\n\n4\\) long scripts\nembedded in nix, compatibility shims, aliases, re-exports, bash used for stateful logic, and unguarded platform-specific\nconfiguration; 5) committed private submodule gitlinks that point to unpushed commits, orphaned agent sessions, settings\nseed ownership gaps, and flake evaluations that omit required submodules; 6) scripts, behavior-bearing modules, or\nrecent bug fixes without focused regression coverage, excluding declarative configuration already proven by rebuild;\n\n7\\) real defects: inverted or off-by-one comparisons, wrong boolean operators, dropped negations, wrong defaults or\nconstants, and broken empty-input handling.";

const FINDING_PROPERTIES = {
  dimension: { type: "string" },
  file: { type: "string" },
  line: { type: "integer" },
  severity: { enum: ["critical", "high", "medium", "low"] },
  title: { type: "string" },
  detail: { type: "string" },
  confidence: { type: "integer", minimum: 1, maximum: 5 },
};
const listSchema = (listName, itemProperties, maxItems) => ({
  type: "object",
  properties: {
    [listName]: {
      type: "array",
      maxItems,
      items: {
        type: "object",
        properties: itemProperties,
        required: Object.keys(itemProperties),
      },
    },
  },
  required: [listName],
});
const VERDICT_PROPERTIES = {
  index: { type: "integer" },
  confirmed: { type: "boolean" },
  reason: { type: "string" },
};
const FINDINGS_SCHEMA = listSchema("findings", FINDING_PROPERTIES, 15);
const VERDICTS_SCHEMA = listSchema("verdicts", VERDICT_PROPERTIES, 40);
const SLICES_SCHEMA = {
  type: "object",
  properties: {
    slices: { type: "array", items: { type: "string" } },
    error: { type: "string" },
  },
};

const MAXIMUM_SLICES = 12;
const VERIFIER_COUNT = 5;
const MAXIMUM_CANDIDATES = 40;
const MAXIMUM_REPORTED_FINDINGS = 15;
const SEVERITY_ORDER = ["critical", "high", "medium", "low"];
const severityRank = (finding) => SEVERITY_ORDER.indexOf(finding.severity);
const SLICER = { model: "haiku", effort: "low", schema: SLICES_SCHEMA };
const READER = { model: "haiku", effort: "low", schema: FINDINGS_SCHEMA };
const SECOND_LOOK = { model: "haiku", effort: "low", schema: FINDINGS_SCHEMA };
const VERIFIER = { model: "sonnet", effort: "medium", schema: VERDICTS_SCHEMA };
const root = args?.root ?? ".";
const subtree = args?.subtree ?? "";
const SWEEP_TASK =
  "Sweep this slice of the dotfiles repository for standing rot and real defects.";
const secondLookTask = (firstFindings) =>
  `Take a second look and report only what the first reader missed. It reported the findings below.\n\n${instructionData(firstFindings)}.\n\n`;

const readerBrief = (artifactPath, task) => `### Housekeeping slice

${task}
The slice artifact is the file named on the next line.

${instructionData(artifactPath)}.

It holds every file of the slice under a "=== path" header, each line prefixed with its line number inside that file.
Read the whole artifact, in chunks when it is long, and report each finding with the file path from its header and the
line number printed beside it.

${SWEEP_DIMENSIONS}

${COVERAGE_EXCLUSIONS}

Try to refute each concern before returning it. Keep each detail under 60 words and rate your confidence from 1 to 5.`;

const verifierBrief = (batch) => `### Verification

Independently verify these dotfiles housekeeping candidates by reading the actual checkout and its history. The checkout
root is the path on the next line.

${instructionData(root)}.

Try hard to refute every candidate. Confirm one only when it is real and no existing formatter, linter, test, diff
reviewer, import mechanism, glob, generator, intentional backlog, or steward behavior already owns or explains it.

### Candidates

${instructionData(batch.map(({ index, file, line, dimension, title, detail }) => ({ index, file, line, dimension, title, detail })))}.

Return one verdict per candidate index.`;

phase("Slice");
const sliced = !subtree
  ? { error: "pass args {root, subtree} naming one subtree of the checkout" }
  : await agent(
      `### Slice

Run the installed dotfiles-housekeeping-slices command directly in Bash as your first action; it is already on PATH.
Set its --root and --subtree options to the two values below.

${instructionData({ root, subtree })}.

Return its JSON output as structured data.`,
      { label: "slice", phase: "Slice", ...SLICER },
    );
const allSlicePaths = sliced?.slices ?? [];
const slicePaths = allSlicePaths.slice(0, MAXIMUM_SLICES);
if (allSlicePaths.length > MAXIMUM_SLICES)
  log(`audited ${MAXIMUM_SLICES} slices`);

const perSlice = await pipeline(
  slicePaths,
  (artifactPath, _, sliceIndex) =>
    agent(readerBrief(artifactPath, SWEEP_TASK), {
      label: `read-${sliceIndex}`,
      phase: "Read",
      ...READER,
    }),
  (readerResult, artifactPath, sliceIndex) =>
    agent(
      readerBrief(artifactPath, secondLookTask(readerResult?.findings ?? [])),
      { label: `second-${sliceIndex}`, phase: "Second look", ...SECOND_LOOK },
    ).then((reviewerResult) => [
      ...(readerResult?.findings ?? []),
      ...(reviewerResult?.findings ?? []),
    ]),
);

const isNear = (left, right) =>
  left.file === right.file && Math.abs(left.line - right.line) <= 2;
const isFirstAtItsSite = (finding, position, all) =>
  all.findIndex((kept) => isNear(kept, finding)) === position;
const distinct = perSlice.filter(Boolean).flat().filter(isFirstAtItsSite);
const candidates = distinct
  .filter((finding) => finding.confidence >= 3)
  .sort((left, right) => right.confidence - left.confidence)
  .slice(0, MAXIMUM_CANDIDATES)
  .map((finding, index) => ({ ...finding, index }));
log(
  `${distinct.length} distinct findings, ${candidates.length} sent to verification`,
);

const batches = Array.from({ length: VERIFIER_COUNT }, (_, batchIndex) =>
  candidates.filter(({ index }) => index % VERIFIER_COUNT === batchIndex),
).filter((batch) => batch.length > 0);
const verdictLists = await parallel(
  batches.map(
    (batch, batchIndex) => () =>
      agent(verifierBrief(batch), {
        label: `verify-${batchIndex}`,
        phase: "Verify",
        ...VERIFIER,
      }),
  ),
);

const confirmedIndexes = new Set(
  verdictLists
    .filter(Boolean)
    .flatMap((verdictList) => verdictList.verdicts ?? [])
    .filter((verdict) => verdict.confirmed)
    .map((verdict) => verdict.index),
);
const confirmed = candidates
  .filter((candidate) => confirmedIndexes.has(candidate.index))
  .sort((left, right) => severityRank(left) - severityRank(right));
const summary = `Housekeeping of ${subtree}: ${perSlice.filter(Boolean).length} of ${slicePaths.length} slices read twice, ${candidates.length} candidates, ${verdictLists.filter(Boolean).length} of ${batches.length} verifier batches returned, ${confirmed.length} confirmed.`;
const reportLine = (finding) =>
  `- **${finding.severity}** ${finding.file}:${finding.line} (${finding.dimension}): ${finding.title}. ${finding.detail}`;
const shown = confirmed.slice(0, MAXIMUM_REPORTED_FINDINGS);
const hidden = confirmed.length - shown.length;
const report = slicePaths.length
  ? [
      summary,
      ...shown.map(reportLine),
      ...(hidden > 0 ? [`${hidden} more confirmed findings not shown.`] : []),
    ].join("\n")
  : `Housekeeping did not run: ${sliced?.error ?? "the slicer returned no slices"}.`;
return report;
