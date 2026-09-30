# Tweet from Dillon Mulroy — anti-slop Oxlint plugin

Capture: `ReadItLater Inbox/Tweet from Dillon Mulroy (2026-08-13 21-22-06).md`
Origin: https://x.com/dillon_mulroy/status/2087531327000117630
Verdict: **drop**

## The origin as resolved

Opened the captured status itself, not a search. `twikit-cli tweet 2087531327000117630` currently fails with
its known `'value'` parser error and the documented `grok-search` fallback is not installed, so the exact
canonical URL was opened in the unattended PinchTab browser instead. It resolves to Dillon Mulroy's post
from 2026-08-12:

> ive been working on an anti-slop oxlint plugin. just had one agent accuse another agent of "type
> laundering" after reviewing/linting changes with it lmao

The post links only its screenshot, not a repository. Research after reading the origin resolved the released
artifact to [dmmulroy/anti-slop](https://github.com/dmmulroy/anti-slop), whose README describes the same
"anti-slop" Oxlint work and identifies it as the author's opinionated ruleset. At inspected revision
`c44ef22ca116d0ba62a3ff663a0bd13a3f3fa40b`, it is MIT-licensed, has no official npm package, and explicitly
expects consumers to vendor, read, customize, and maintain its source.

## What it actually is

A set of custom Oxlint rules for JavaScript and TypeScript, plus an agent installation skill. The generic
rules reject patterns such as chained assertions, widening known values into broad dictionary contracts,
ad-hoc runtime `typeof` checks, module mocking, conditional empty-object spreads, and assertions without a
nearby `SAFETY:` justification. It also includes a formatting-policy rule that inserts blank lines between
declarations and around control flow.

This is not an AI-output detector and it does not prove that code was generated badly. It is a syntactic,
same-file policy layer over Oxlint's ESTree and scope APIs. Upstream states that it does not infer imported
types or cross-file call signatures, and calls the rules the author's taste rather than a universal coding
standard.

## What it touches here

There is no single JavaScript/TypeScript lint owner to extend:

- `agent-harness/measurement-and-reporting/dashboard/package.json:4-9` owns the Angular dashboard commands;
  it has build and test scripts but no lint script or Oxlint dependency.
- `agent-harness/quality/evaluations/node-provider-runtime/package.json:9-10` separately owns the provider
  runtime and exposes only its Node test command.
- `sonar-project.properties:4-18` is the repository-wide static-analysis gate and includes TypeScript config
  discovery, but it deliberately excludes JS/TS coverage and does not provide a local JS/TS lint command.

Adopting upstream as designed would therefore add a new root JavaScript toolchain or duplicate exact Oxlint
and `@oxlint/plugins` dependencies across independent package roots, vendor the plugin source, add configs
and scripts, and establish a new update responsibility. It would replace no existing lint command, delete
nothing, and does not unblock an already-planned change.

The potentially useful findings landed in existing modules rather than revealing a missing integration:

- `agent-harness/measurement-and-reporting/dashboard/src/app/services/usage-aggregation/token-aggregation.ts:18-30`
  has two assertions for keys discovered through `Object.entries`; the plugin demands safety comments.
- `agent-harness/quality/evaluations/node-provider-runtime/provider-adapters.mjs:120-134` conditionally omits
  optional OpenCode fields, which the plugin rejects even though omission is the intended wire shape.
- `agent-harness/quality/evaluations/node-provider-runtime/provider-runtime.mjs:29-35` deliberately reports
  the runtime type of a dynamically resolved SDK symbol; `no-runtime-typeof` diagnoses that observation as
  if it were ad-hoc boundary narrowing.

## Evidence and cost

The upstream repository was cloned outside the worktree, dependencies were installed from its lockfile, and
all generic rules were run against the dashboard source, the Node provider runtime, and the research-pulse
JavaScript. The default ruleset reported 181 problems. Disabling only `require-readable-spacing` reduced that
to 16: 13 anti-slop findings and three native unused-variable warnings. Thus 165 of 181 findings (91%) were
the plugin's blank-line policy, not evidence or type safety.

The remaining findings are a mixture: safety comments on assertions may be useful, but the dictionary-return
diagnostics reject named public contracts, the `typeof` diagnostics include deliberate runtime inspection,
and the conditional-spread diagnostics reject concise construction of optional SDK inputs. Making this fit
would mean starting with most of the advertised policy disabled or overridden, while still retaining a
vendored plugin and exact-version Oxlint pair.

## Reasoning

Drop it. A good adoption here would give every owned JS/TS surface one low-noise command and catch defects
that the existing build, tests, and Sonar analysis miss. This plugin does neither without first creating a
repository-wide Node lint boundary that does not currently exist. The direct trial's strongest result was
format churn, and the non-format rules repeatedly treated intentional contracts and boundary code as the
very anti-patterns they ban.

Selective ideas from it—especially requiring justification for unsafe type assertions—remain reasonable,
but that is evidence for a future project-local rule when one package gains a lint owner, not a reason to
vendor this ruleset now. Keep the decision here rather than filing the tool as a reference: the source is
easy to rediscover, and the actionable local conclusion is that its default policy does not fit this repo.

## Drafted vault entry

None. A drop files nothing in the vault; this decision file is the durable record of the evaluated source,
the trial, and why it was rejected.
