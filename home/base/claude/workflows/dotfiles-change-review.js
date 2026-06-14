export const meta = {
  name: "dotfiles-change-review",
  description:
    "Adversarial multi-dimension review of the current dotfiles working diff: one reviewer per dimension, refute every finding, then synthesize a prioritized report tuned to this nix/home-manager repo.",
  whenToUse:
    "Before committing a substantive change to the dotfiles repo, when you want broader cross-checked coverage than a single-pass review: nix rebuild safety, code style, instruction-surface quality, and test coverage.",
  phases: [
    { title: "Scope", detail: "resolve the working diff and digest it" },
    { title: "Review", detail: "one reviewer per dimension over the diff" },
    { title: "Verify", detail: "adversarially refute each finding" },
    {
      title: "Synthesize",
      detail: "merge survivors into a prioritized report",
    },
  ],
};

const reviewTarget = typeof args === "string" ? args : (args && args.ref) || "";

const DIFF_SCHEMA = {
  type: "object",
  properties: {
    changedFiles: { type: "array", items: { type: "string" } },
    digest: { type: "string" },
  },
  required: ["changedFiles", "digest"],
};

phase("Scope");
const scope = await agent(
  `Resolve and digest the change under review in the dotfiles repository. ${
    reviewTarget
      ? `Review target ref: "${reviewTarget}".`
      : "No target given: review the uncommitted working changes plus any commits on the current branch that are not yet on the steward base. Diff against the merge-base of HEAD and origin/main, falling back to main."
  } Include both staged and unstaged changes. Return the changed-file list and a compact digest of the diff: the hunks that matter, not whole files.`,
  { label: "scope", phase: "Scope", schema: DIFF_SCHEMA },
);

if (!scope || !(scope.changedFiles && scope.changedFiles.length)) {
  return { target: reviewTarget, result: "No diff to review." };
}

const REVIEW_DIMENSIONS = [
  {
    key: "correctness",
    title: "Correctness and behavior",
    focus:
      "logic errors, wrong option values, broken references between modules, edge cases, and changes that silently do nothing",
  },
  {
    key: "nix-rebuild-safety",
    title: "Nix and rebuild safety",
    focus:
      "will it evaluate and rebuild on every targeted system; module-option and type mismatches, missing or wrong imports, infinite recursion, platform guards (isNixOS vs isDarwin), agenix secret wiring, and submodule gitlink bumps that must be committed to deploy",
  },
  {
    key: "code-style",
    title: "Code style this repo enforces",
    focus:
      "zero comments anywhere, long descriptive names with no abbreviations, domain nesting rather than many prefixed sibling files, single responsibility, scripts over 10 lines extracted from nix string interpolation, no backward-compatible shims or aliases",
  },
  {
    key: "instruction-surface",
    title: "Instruction-surface quality",
    focus:
      "only if instruction files changed (core.md, CLAUDE.md, SKILL.md, agent definitions): density, evergreen pointers over copies, no stale references, and consistency with the rest of the agent instruction surface",
  },
  {
    key: "tests",
    title: "Tests and verification",
    focus:
      "new behavior without a test, a bug fix without a regression test, bash scripts without a shellcheck test, and whether tests/run.sh would still pass for the touched tier",
  },
  {
    key: "secrets-and-publicity",
    title: "Secrets and public-repo safety",
    focus:
      "committed secrets or tokens, and employer-identifying names or details, since this repo is public",
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

const reviewed = await pipeline(
  REVIEW_DIMENSIONS,
  (dimension) =>
    agent(
      `Review the dotfiles change under one lens only: ${dimension.title}. Look for ${dimension.focus}. Changed files: ${scope.changedFiles.join(
        ", ",
      )}. Diff digest:\n${scope.digest}\nOpen the actual files in the repository as needed. Report only real, actionable findings tied to changed lines with a concrete file and location and a fix suggestion. Skip style a formatter already handles and skip speculation.`,
      {
        label: `review:${dimension.key}`,
        phase: "Review",
        schema: FINDINGS_SCHEMA,
      },
    ),
  (review, dimension) =>
    parallel(
      (review?.findings ?? []).map(
        (finding) => () =>
          agent(
            `Adversarially verify this dotfiles review finding by reading the actual code, and try hard to REFUTE it. It holds only if it is a real defect in the changed code; default to holds=false when the path is unreachable, the concern is already handled, the evidence is weak, or it is mere preference. Finding: ${JSON.stringify(
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

const confirmedFindings = reviewed
  .flat()
  .filter(Boolean)
  .filter((finding) => finding.verdict && finding.verdict.holds);

phase("Synthesize");
const report = await agent(
  `Synthesize a dotfiles change-review report from these confirmed findings. Group by severity with critical first, deduplicate overlaps, and for each give file and location, the problem, and the suggested fix. End with a short "before you commit" list naming the one to three things most worth fixing first. If there are no confirmed findings, say the diff looks clean and note what was reviewed. Confirmed findings: ${JSON.stringify(
    confirmedFindings,
  )}. Files reviewed: ${scope.changedFiles.join(", ")}.`,
  { label: "synthesize", phase: "Synthesize" },
);

return report;
