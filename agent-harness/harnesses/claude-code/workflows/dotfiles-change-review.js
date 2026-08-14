export const meta = {
  name: "dotfiles-change-review",
  description:
    "Two-pass review of the current dotfiles working diff: find actionable defects across every repository risk, then independently refute and synthesize them.",
  whenToUse:
    "Before committing a substantive change to the dotfiles repo. It checks correctness, nix rebuild safety, code style, instruction quality, test coverage, and public-repo safety with at most two model calls.",
  phases: [
    {
      title: "Review",
      detail: "inspect the diff across every repository risk",
    },
    {
      title: "Verify",
      detail: "independently refute candidates and synthesize the report",
    },
  ],
};

const reviewScope = typeof args === "string" ? args : (args && args.ref) || "";
const scopeInstruction = reviewScope
  ? `Follow this review scope: "${reviewScope}".`
  : "Review uncommitted changes, including untracked files, plus commits on the current branch that are absent from the steward base. Compare with the merge-base of HEAD and origin/main, falling back to main.";

const CANDIDATE_SCHEMA = {
  type: "object",
  properties: {
    changedFiles: { type: "array", items: { type: "string" } },
    findings: {
      type: "array",
      maxItems: 6,
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
  required: ["changedFiles", "findings"],
};

phase("Review");
const candidates = await agent(
  `Review the current change in the dotfiles repository. ${scopeInstruction} Inspect the actual diff, changed files, surrounding callers, tests, and repository rules. Apply every relevant lens in one pass: logic, option values, references, edge cases, and silent no-ops; nix evaluation, imports, recursion, platform guards, secrets, rebuild safety, and expensive work repeated inside loops; no comments, descriptive names, domain nesting, single responsibility, extracted long scripts, and no compatibility shims; instruction density, routing, authority, and stale references; missing regression tests, shell checks, or deployment evidence; and secrets or identifying data in this public repository. Try to refute each concern before returning it. Report at most six actionable findings tied to changed lines, with a concrete location and fix. Skip formatter concerns, preference, and speculation. Keep each detail under 80 words.`,
  {
    label: "review",
    phase: "Review",
    schema: CANDIDATE_SCHEMA,
    model: "haiku",
    maxTurns: 8,
  },
);

if (
  !candidates ||
  !(candidates.changedFiles && candidates.changedFiles.length)
) {
  return { target: reviewScope, result: "No diff to review." };
}

phase("Verify");
const report = await agent(
  `Independently inspect the actual dotfiles diff under this scope: ${scopeInstruction} Try hard to refute every candidate below. Keep a finding only when the changed code proves a real defect; reject unreachable paths, handled concerns, weak evidence, and preference. Check for a missed critical or high-severity defect across the same six lenses, but add one only with direct evidence. Return a concise markdown report under 350 words with no more than five confirmed findings, ordered by severity. Each finding must name the file and location, defect, evidence, and smallest fix. If none survive, say the diff looks clean and name the files and lenses reviewed. Candidate findings: ${JSON.stringify(candidates.findings)}. Files: ${candidates.changedFiles.join(", ")}.`,
  {
    label: "verify",
    phase: "Verify",
    model: "sonnet",
    maxTurns: 8,
  },
);

return report;
