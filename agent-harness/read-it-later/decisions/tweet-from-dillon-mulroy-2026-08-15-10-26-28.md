# Tweet from Dillon Mulroy — `anti-slop` Oxlint plugin

Capture: `ReadItLater Inbox/Tweet from Dillon Mulroy (2026-08-15 10-26-28).md`
Origin: https://x.com/dillon_mulroy/status/2087537790061850984
Linked source: https://github.com/dmmulroy/anti-slop
Verdict: **drop**

## The origin as resolved

Read the captured status itself through the Twitter route, not a search for the topic. `twikit-cli tweet
2087537790061850984` and `twikit-cli thread 2087537790061850984` both hit the client's known `'value'` parse error,
and the configured `grok-search` fallback is absent on this host, so the exact status was recovered through the
FxTwitter status endpoint. The 2026-08-12 post announces:

> available now
>
> npx skills add dmmulroy/anti-slop --skill install-anti-slop

Its first shortened link resolves to the GitHub repository above. The second resolves to the quoted post from the
same author, which describes an anti-slop Oxlint plugin and jokes about one agent identifying another agent's "type
laundering." The attached image is a code view of the initial plugin registration rather than a benchmark or a
before-and-after result.

The repository was created minutes before the announcement; commit
`b5d2288db1f00469a1d5f2e3b0e265e5a5676fd0` is the last revision at the tweet timestamp. The current source inspected
for this decision is `c44ef22ca116d0ba62a3ff663a0bd13a3f3fa40b`, so the verdict covers the maintained tool rather than only the
smaller launch-day snapshot.

## What it actually is

`anti-slop` is an opinionated, source-vendored Oxlint JavaScript plugin, not a published npm package. Its installation
skill copies the implementation into a target repository, pins `oxlint` and `@oxlint/plugins` to matching exact
versions, registers the plugin, enables every generic rule, and leaves the copy under local ownership.

The current generic set has 18 custom rules plus native `oxc/no-accumulating-spread`. It rejects selected assertion,
type-widening, `unknown`, dictionary, reflection, module-mocking, eager-array-pass, reducer-copy and runtime-`typeof`
patterns, and imposes a blank-line policy. A separate five-rule plugin adds Effect-specific architecture policy. The
analysis is deliberately same-file ESTree and lexical-scope analysis, not TypeScript type-checking; imported types and
cross-file signatures are outside its proof boundary.

A generic-only fresh install currently copies 31 source and provenance files totalling 4,072 lines before adding the
target repository's configuration and lockfile changes.

## What it touches here

Nothing should change.

The advertised `npx skills add` command is not a durable installation route for this machine. Skills are discovered
from the declarative public and private source directories at
`agent-harness/agent-instructions/interactive-skill-catalog/skill-set-builders.nix:8-27`, then mapped into managed
deployment destinations at `agent-harness/agent-instructions/interactive-skill-catalog/skill-set-builders.nix:53-90`.
A live package-manager install would be unmanaged drift; a real skill adoption would have to vendor and maintain the
installer inside that source tree.

Installing the lint policy is not a drop-in repository change either. The only owned TypeScript application is the
usage dashboard, whose package has build and test scripts but no lint command or Oxlint dependencies at
`agent-harness/measurement-and-reporting/dashboard/package.json:4-33`. The other JavaScript is spread across several
independent runtime packages and standalone scripts rather than one root Node project. A repository-wide adoption
would therefore first create a new shared lint/package boundary.

The repository already sends JavaScript and TypeScript through its declared SonarQube analysis scope at
`sonar-project.properties:4-18`, rejects every new issue at
`repository/verification/quality/sonarqube/cloud.json:7-30`, and runs that gate in
`.github/workflows/tests.yml:122-134`. `anti-slop` has narrower rules that SonarQube does not duplicate, but this
capture supplies no recurring defect or failed review that one of those rules would fix.

The full bundle also conflicts with local authority. Its `require-safety-comment-for-type-assertion` rule requires an
explanatory marker comment for every non-const assertion, while
`agent-harness/agent-instructions/core-rules/core.md:43-48` forbids adding explanatory comments to owned code. Its
`require-readable-spacing` rule independently imposes formatting policy across otherwise separate projects.

## Trial evidence

Ran the current generic plugin unpackaged from its own checkout against this worktree, with vendored and minified code
excluded:

- The dashboard alone: 24 files, 73 diagnostics in 14 files. Of those, 66 are readable-spacing findings, five require
  safety comments for assertions, and two report known-value widening.
- The repository's owned JavaScript and TypeScript surface: 135 files, 1,134 total Oxlint diagnostics in 114 files.
  The anti-slop rules account for 1,094: 1,064 readable-spacing findings, 20 runtime-`typeof` findings, five required
  safety comments, three conditional-empty-object-spread findings, and two known-value-widening findings. The remaining
  40 are Oxlint's enabled native defaults rather than claims made by this plugin.

This is evidence of a policy mismatch, not evidence that 1,094 defects exist. In particular, 97% of the plugin's
findings are its formatting preference, and the comment findings ask for a practice the repository explicitly rejects.

Three materially different adoptions were considered:

- Enable the complete generic bundle: adds a vendored 4,072-line policy implementation, two pinned dependencies, a
  new lint boundary, and immediate cleanup across most JavaScript/TypeScript files.
- Port only selected rules: creates a locally maintained policy fork and supporting plugin infrastructure for a small
  number of findings without an observed recurring failure.
- Install only the helper skill: adds permanent agent surface whose only job is to perform the two options above in
  some future repository, while it changes no current workflow here.

None replaces or deletes an existing dependency, script, instruction, or analyzer, and none unblocks current work.

## Reasoning

Drop this capture. The interesting part is the direction—turn precise low-evidence coding objections into executable
checks—but this repository already states that principle at `agent-harness/agent-instructions/core-rules/core.md:66-73`
and has a deterministic quality gate. The concrete policy is a poor fit: it assumes an Oxlint-centered TypeScript or
JavaScript project, carries a large vendored implementation, mostly reports formatting here, and conflicts with the
repository's comment policy.

Keeping it as a reference would preserve a tool with no present consumer and no decision it can change. Reconsider a
specific rule only when a repeated defect identifies its target and the owning package already has, or independently
needs, an Oxlint boundary; at that point compare that one check against SonarQube or a smaller local rule instead of
importing this bundle by default.

## Drafted vault entry

None. A drop creates no vault entry.
