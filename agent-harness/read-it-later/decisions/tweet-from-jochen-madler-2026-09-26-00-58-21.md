# Jochen Madler — SlopShape structural AI-text detection

Capture: `ReadItLater Inbox/Tweet from Jochen Madler (2026-09-26 00-58-21).md`
Origin: https://x.com/jochenmadler/status/2103530162318901673
Verdict: **learn**

## The origin as resolved

Read through the Twitter channel, not a topic search. `twikit-cli tweet 2103530162318901673` resolves the
2026-09-25 post by Jochen Madler, and `twikit-cli thread` adds the author's two demos. The post announces a
classifier for AI-written commercial blog posts and links to the paper. Its shortened link resolves to
Madler's *SlopShape: Identifying AI-Generated Commercial Web Content*, arXiv:2609.15369; the paper links its
verification package at https://github.com/pulse-energy-eu/slopshape.

The tweet says the model got 19 of 1,740 unseen posts wrong. The current paper is revision v3, dated
2026-09-28, and reports the comparable results more carefully: 0.9695 macro-F1 for the 176-feature
structure-only classifier and 0.9800 for all 203 features. This decision uses the revised paper and released
artifacts rather than treating the announcement's rounded claim as the result.

## What it actually is

This is a supervised classification study, not a general-purpose prose-quality rubric. It pairs 2,250
pre-ChatGPT human B2B blog posts from 268 company domains with 11,250 single-pass mirrors generated from the
same briefs by five 2025-2026 models. An LLM scores each post against a frozen 203-feature instrument; 176
features remain after excluding writing-style and format-sensitive features. An XGBoost classifier reaches
0.9695 macro-F1 on a company-domain-disjoint test split. Rewriting each AI test post with the model that
generated it changes about 73% of its 13-word spans but only reduces structural macro-F1 to 0.9606.

The useful result is that generator defaults appear above the word level. Nine core structural features alone
reach 0.9010 macro-F1. The strongest AI-leaning values include a summary or synthesis stage, a conclusion that
restates or reframes the thesis, no path for reader participation, modern-or-next-generation framing, and
confident institutional explanation. Those are correlations in this corpus, not defects by definition: a
mechanism-explanation stage also leans AI, while `no thesis before first unit` and `under 800 words` lean human.
Optimizing prose to look statistically human would therefore conflict with clarity in some cases.

The scope is narrow and stated plainly by the release: single-pass commercial posts from five models. It does
not establish detection of ordinary agent replies, technical decisions, human-edited AI prose, restructuring
attacks, or commercial humanizers. The human side also predates the generators; the year-control battery is
useful evidence against a simple era confound, but it is not a same-period human comparison. The author
discloses a commercial interest in content scoring. The analysis code is PolyForm Noncommercial, while the
instrument, prompts, artifacts, and documentation are all rights reserved beyond verification, so importing
the released instrument into this public repository is not licensed.

## What it touches here

It changes no module, skill, agent, host, or script.

- `agent-harness/agent-instructions/skills/writing/humanize/SKILL.md:8-11` already defines success in terms of
  what the reader can recover, rather than whether prose resembles a human reference corpus.
- `agent-harness/agent-instructions/skills/writing/humanize/SKILL.md:94-96` already asks for one reader need per
  paragraph and its main point first; the paper's human-leaning `no thesis before first unit` is not a reason
  to weaken that rule.
- `agent-harness/agent-instructions/skills/writing/humanize/SKILL.md:107-116` already removes repeated
  conclusions, promotional framing, inflated significance, vague authority, and other formulaic combinations
  that overlap the paper's strongest correlations without pretending that any one marker proves AI authorship.
- `agent-harness/agent-instructions/skills/writing/humanize/SKILL.md:118-128` owns semantic revision, which is
  the quality boundary a detector cannot replace.
- `agent-harness/quality/evaluations/evals/communication.yaml:105-199` tests observable communication outcomes
  such as separating evidence from inference and preserving measured scope. It does not test whether an answer
  can fool an authorship classifier, and this capture does not justify adding that target.

The pull request therefore carries this decision record alone. It adds no dependency, copies none of the
restricted instrument, replaces and deletes nothing, and leaves the Humanize policy and evaluations unchanged.
The learning value is methodological: it supplies a worked example for designing a future, independently
licensed corpus-level evaluation if repetition across whole responses becomes a measured problem here.

## Reasoning

**Learn**, because the transferable part is experimental practice rather than a product or prose rule:
separate structure from surface style, freeze the feature definition before reading outcomes, split by source
domain, audit format artifacts, validate LLM annotations against people, publish failure overlap, and attack the
result with rewording before claiming durability. The study entry below names those practices and keeps the
scope caveats beside them.

**Not adopt:** using the detector here would add an LLM-scoring and classifier pipeline for a domain the study
did not test, under licensing that does not permit copying the instrument. Turning its top correlations into
Humanize prohibitions would confuse authorship prediction with reader benefit and would directly reward some
weak behaviors.

**Not trial:** a faithful rebuild is estimated by the authors at about $1,650, requires gated per-document
artifacts or corpus reconstruction, and would test B2B blog classification rather than an unresolved behavior
of this harness. **Not reference:** filing only the headline would lose the part worth retaining—the concrete
evaluation controls to practice when constructing communication tests. **Not drop:** the design is unusually
auditable and provides a useful counterexample to treating surface-word bans as a complete anti-slop policy.

## Vault entry, drafted

On approval, create `Second Brain/Inspiration/Jochen Madler - SlopShape.md` and add its link under `## Notes`
in `AI Agent Skills MOC`. `topic/ai-agents` already exists in the Tag Legend; reference notes in this branch do
not invent a medium tag.

```markdown
---
title: "Jochen Madler - SlopShape"
type: reference
status: filed
source-url: https://arxiv.org/abs/2609.15369
creator: Jochen Madler
platform: arXiv
captured: 2026-09-26
rating: worth-studying
license: code PolyForm Noncommercial 1.0.0; instrument and artifacts all rights reserved
tags:
  - topic/ai-agents
---
Up: [[AI Agent Skills MOC]]

## Bottom line

SlopShape shows that single-pass AI-written B2B posts carry a detectable structure beyond word choice. A
176-feature structure-only classifier reaches 0.9695 macro-F1 on a company-domain-disjoint test split and
0.9606 after each generating model rewrites its own posts. That is strong evidence about this paired corpus,
not a general AI detector and not a prose-quality score.

## What the experiment measured

The study pairs 2,250 pre-ChatGPT human commercial blog posts from 268 domains with 11,250 mirrors generated
from the same briefs by five 2025-2026 models. An LLM applies a frozen 203-feature instrument; 176 features
remain after removing style and format-sensitive features. Nine structural features retain 0.9010 macro-F1.

The core correlations make the limit visible. Summary stages, thesis-restating conclusions, modern framing,
and confident institutional explanation lean AI in this corpus, but so does mechanism explanation. Short
posts and delaying the thesis lean human. These values predict origin; they do not say which prose helps a
reader.

## What to practice

- Separate the outcome being optimized—reader understanding, authorship, style, or task success—before
  defining features. Do not use authorship prediction as a proxy for quality.
- Freeze the rubric and exclusions before looking at labels. Keep style-only, structure-only, and combined
  variants so one result cannot hide what carries the signal.
- Split evaluation data by the unit that can leak identity. Here that means company domains rather than
  random posts; for agent communication it may mean task families or source repositories.
- Probe representation artifacts explicitly. Titles and Markdown differed between the human and generated
  corpora, so the paper rescored format variants and removed eleven sensitive structural features.
- Validate LLM-applied rubrics against human agreement, publish the disagreements, and keep missing evidence
  visible rather than treating automated labels as ground truth.
- Test durability against a transformation that targets the claimed level. Rewording probes whether surface
  edits erase structural signal; a stronger claim would also need human editing, restructuring, and
  detector-aware attacks.

## Limits to retain with the result

The claim covers single-pass commercial posts from five models. It does not cover ordinary assistant replies,
technical decisions, human-edited drafts, restructuring attacks, or commercial humanizers. Human samples
predate the models; a temporal control argues against a simple year effect but does not replace a same-period
comparison. The author discloses a commercial interest. The code is noncommercially licensed, while the
instrument, prompts, and artifacts are all rights reserved beyond verification.

## Fit here

The Humanize skill already optimizes reader-recoverable meaning, measured scope, natural register, and
semantic revision. Keep those goals. Use this paper as a study design when a corpus-level repetition problem
is observed and deserves a benchmark; do not copy its detector or add its correlations as universal writing
rules.
```
