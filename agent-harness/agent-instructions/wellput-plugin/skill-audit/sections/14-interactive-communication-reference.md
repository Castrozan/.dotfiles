# Interactive communication reference: sentence audit

Sentence IDs S66-S68. [Audit overview](../../skill-audit.md). [Full sentence review](../../skill-review.md#interactive-communication-reference).

## Section assessment

A short boundary between selected writing guidance and persistently injected chat rules is useful. The main hazard is
treating declared hook configuration as proof of delivery. The no-reload rule is correct only when the contract is
already present. Keep the link policy as a pointer and preserve its interactive-only scope; do not duplicate its syntax
or apply terminal preferences indiscriminately to artifacts.

Most useful content: the ownership pointer and avoiding redundant loads. Main repair: make delivery and trust
assumptions explicit and keep transport mechanics in manifests and integration checks. See F05 and F09.

## S66: Replace the universal delivery claim with a capability boundary

> Interactive harnesses inject `[interactive communication](references/interactive-communication.md)` separately
> because its response contract must remain available before Wellput is selected.

**Assessment:** Separate persistent delivery is the right architectural intent, but the sentence describes harness
mechanics rather than a writing action. A supported hook can inject the contract; merely having an interactive harness
does not prove that the plugin's hooks are enabled and trusted. The Codex documentation explicitly requires hook trust.

**Related:** S67 tells the agent not to reload the reference, while the exported SessionStart driver supplies it. The
portable verifier proves hook output, not every installed harness's delivery state.

**Recommendation:** Keep a brief boundary that applies when the contract has actually been injected. Let manifests and
integration checks own the mechanics and trust assumptions.

**Principles:** Runtime evidence; scope and horizon; no code narration.

## S67: Add the missing delivery condition

> Do not reload it during ordinary Wellput use.

**Assessment:** Avoiding duplicate loads is a useful token-economy rule, but 'ordinary' use is undefined and inherits
S66's delivery assumption. If the contract was never delivered, forbidding retrieval leaves the model with neither the
defaults nor the recovery path. Reloading after context loss is a separate case from repeatedly reading the same file.

**Related:** S66 states the assumed delivery, the injected loading policy handles compaction, and the public hook output
points to absolute skill paths.

**Recommendation:** Skip reloading a contract already present in context; load the reference when it was not delivered
or the needed policy is absent.

**Principles:** Conditional scope; progressive disclosure.

## S68: Keep the pointer, audit the target's fit

> Follow its `[link format](references/interactive-communication.md#link-format)` when writing interactive replies.

**Assessment:** Pointing to a canonical link policy is preferable to copying it into the writing skill. The target is
nevertheless a consumer preference: bare URLs are useful in terminals but may conflict with a requested article,
Markdown artifact, or interface-specific citation requirement. This sentence correctly says 'interactive replies', so
the artifact boundary should be preserved.

**Related:** The injected link policy and its deterministic checker own syntax; S11 protects requested transformations;
the artifact-writing policy governs durable Markdown.

**Recommendation:** Keep the channel boundary and make the target's precedence explicit for requested formats and
platform-required citations. Do not duplicate URL syntax here.

**Principles:** Canonical ownership; channel scope; request precedence.
