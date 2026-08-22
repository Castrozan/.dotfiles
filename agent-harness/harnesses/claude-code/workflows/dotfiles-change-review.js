export const meta = {
  name: "dotfiles-change-review",
  description:
    "Two-pass review of the current dotfiles working diff: find actionable defects across every repository risk, then independently refute and synthesize them.",
  whenToUse:
    "Before committing a change the dotfiles repo counts as substantive, which its change-review-scope rule defines by semantic risk rather than by diff size. It checks correctness, nix rebuild safety, code style, instruction quality, test coverage, and public-repo safety with at most two model calls.",
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

const LENSES = [
  "logic",
  "nix",
  "style",
  "instructions",
  "coverage",
  "exposure",
];

const parseArguments = (value) => {
  if (!value) return {};
  if (typeof value !== "string") return value;
  const trimmed = value.trim();
  if (!trimmed.startsWith("{")) return { ref: trimmed };
  try {
    return JSON.parse(trimmed);
  } catch {
    return { ref: trimmed };
  }
};

const reviewArguments = parseArguments(args);
const reviewScope = reviewArguments.ref || "";
const reviewRoot = reviewArguments.root || "";
const scopeInstruction = reviewScope
  ? `Follow this review scope: "${reviewScope}".`
  : "Review uncommitted changes, including untracked files, plus commits on the current branch that are absent from the steward base.";
const ANCHOR = reviewRoot
  ? `Start by running \`cd "${reviewRoot}"\`.`
  : `Start by running \`cd\` to the working directory you were given: the shell can start in a sibling checkout of this repository, and reviewing the wrong one reports a clean tree that proves nothing.`;

const GATHER = `Collect the change in one Bash call, then read it. Run exactly: base=$(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD main); patch=$(mktemp /tmp/dotfiles-change-review-XXXXXXXX); git --no-pager diff "$base" > "$patch"; git rev-parse --show-toplevel; git --no-pager diff --stat "$base"; git ls-files --others --exclude-standard; echo "$patch". Substitute the base when the scope above names a different one, but keep that shape. Then Read that patch, which holds every tracked change, and Read any untracked file the listing named. Never diff one file at a time: each costs a round trip and the patch already holds them all. Report the repository root that command printed, the diffstat paths as the tracked changes, and the paths the untracked listing printed as the untracked ones, never the patch path. Anchor every later command at that root, because this machine holds sibling checkouts of this repository.`;

const LENS_RULES = `Apply all six lenses to the changed lines in one pass and name the lens each finding came from. logic: wrong condition or option value, broken reference, unhandled edge case, silent no-op. nix: evaluation and import errors, infinite recursion, missing platform guard, rebuild breakage, expensive work repeated in a loop. style: comments, vague names, wrong domain nesting, mixed responsibilities, long scripts inlined in nix, compatibility shims. instructions: density, routing, authority, stale references. coverage: behavior changed without a regression test, script without a check, claim without deployment evidence. exposure: secrets or identifying data reaching this public repository.`;

const EVIDENCE = `A suspicion you cannot confirm at a file and line dies unreported. Skip formatter output, preference, and speculation. Spend at most eight tool calls.`;

const anchorRule = (repoRoot) =>
  `This machine holds sibling checkouts of this repository, so anchor every command at ${repoRoot} with \`git -C\` or an absolute \`cd\`; a command that runs in the wrong one reports a defect that is not in this change.`;

const CANDIDATE_SCHEMA = {
  type: "object",
  required: [
    "repoRoot",
    "changedFiles",
    "untrackedFiles",
    "patchPath",
    "findings",
  ],
  properties: {
    repoRoot: {
      type: "string",
      description: "absolute path git rev-parse --show-toplevel returned",
    },
    changedFiles: {
      type: "array",
      items: { type: "string" },
      description:
        "repository-relative tracked paths the diffstat listed, never the patch path",
    },
    untrackedFiles: {
      type: "array",
      items: { type: "string" },
      description:
        "repository-relative paths the untracked listing printed, which the patch does not contain",
    },
    patchPath: { type: "string" },
    findings: {
      type: "array",
      maxItems: 6,
      items: {
        type: "object",
        required: ["file", "lens", "severity", "title", "detail"],
        properties: {
          file: { type: "string" },
          line: { type: "string" },
          lens: { enum: LENSES },
          severity: { enum: ["critical", "high", "medium", "low"] },
          title: { type: "string" },
          detail: { type: "string" },
          suggestion: { type: "string" },
        },
      },
    },
  },
};

phase("Review");
const candidates = await agent(
  `Review the current change in the dotfiles repository. ${ANCHOR} ${scopeInstruction} ${GATHER} ${LENS_RULES} ${EVIDENCE} Report at most six actionable findings, each with a concrete location and fix, and return the patch path you wrote alongside both file lists. Keep each detail under 80 words.`,
  {
    label: "review",
    phase: "Review",
    schema: CANDIDATE_SCHEMA,
    model: "haiku",
    effort: "low",
  },
);

const trackedFiles = candidates?.changedFiles ?? [];
const untrackedFiles = candidates?.untrackedFiles ?? [];

if (!candidates || (!trackedFiles.length && !untrackedFiles.length)) {
  return {
    target: reviewScope,
    repoRoot: candidates?.repoRoot,
    result: `No diff to review in ${candidates?.repoRoot ?? "the checkout the review pass reached"}: it holds neither a tracked change nor an untracked file. Confirm that is the checkout you changed before reading this as a clean tree.`,
  };
}

phase("Verify");
const report = await agent(
  `Independently inspect the dotfiles change under this scope: ${scopeInstruction} Read the patch at ${candidates.patchPath}, which already holds every tracked change; regenerate it with one whole-diff command for this scope only if that file is missing, and never diff one file at a time. Read each untracked file named below as well, because no patch holds a file git is not tracking yet. ${anchorRule(candidates.repoRoot)} ${EVIDENCE} Try hard to refute every candidate below: keep a finding only when the changed code proves a real defect, and reject unreachable paths, handled concerns, weak evidence, and preference. Add a missed critical or high-severity defect across the same lenses (${LENSES.join(", ")}) only on direct evidence. Return a markdown report under 350 words with at most five confirmed findings, worst first, each naming file and location, defect, evidence, and smallest fix. If none survive, say the diff looks clean and name the files and lenses reviewed. Candidates: ${JSON.stringify(candidates.findings)}. Tracked files: ${trackedFiles.join(", ") || "none"}. Untracked files: ${untrackedFiles.join(", ") || "none"}.`,
  {
    label: "verify",
    phase: "Verify",
    model: "sonnet",
    effort: "medium",
  },
);

return report;
