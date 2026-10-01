# Traveler — AI-assisted game reverse engineering

Capture: `ReadItLater Inbox/Tweet from Traveler (2026-09-30 23-53-42).md`
Origin: https://x.com/Traveler2000AD/status/2105451146856829412
Parent: https://x.com/Vinci_x3/status/2105380351095017687
Verdict: **learn**

## The origin as resolved

Read through the Twitter channel from the capture's exact first link, not from a topic search. The CLI's ordinary
serializer exposed only the legacy-length prefix, so I read the same post's `full_text` field and confirmed it in the
unattended browser. There is no self-thread or quoted post. The target is a long-form reply by Traveler on 2026-10-01
UTC to Vinci's question: can an old childhood game be decompiled, ported, given a level editor, and extended, and how
would one start?

Traveler's simplified sequence is:

1. Install a real reverse-engineering suite, starting with Ghidra and optionally adding IDA Pro or radare2.
2. Supply capable cloud agents/models, or local Ollama models when the machine has enough resources.
3. Put them behind an agent harness such as Grok Build or OpenCode.
4. Start with a small game and expect substantial configuration, model selection, and benchmarking rather than a magic
   prompt.

That final qualification is the useful claim. The post is not a turnkey tool, agent integration, benchmark, or
reproducible game-porting recipe; it is a compact map of the tool categories a real experiment would need.

## What it actually is

A starting curriculum for agent-assisted binary analysis: give an agent a decompiler/disassembler rather than asking
it to infer a program from raw bytes, choose the model and harness deliberately, and learn on a small target. Ghidra is
the concrete center of the advice; IDA Pro and radare2 are alternatives or complements, not requirements to install as
a bundle.

The post does not identify a target binary, platform, architecture, desired modification, acceptance test, or lawful
redistribution path. Those omissions matter because they determine whether static decompilation is enough, whether a
debugger or emulator is needed, which loader and language support matter, and whether the output should be a patch,
clean-room reimplementation, or only notes.

## What it touches here

This pull request changes no executable configuration.

- `machine-configuration/machines/chise/home.nix:20-28` already installs Claude Code, Clawde, Codex, OpenCode, Pi, and
  Hermes on the Linux host. That covers the source's harness category; adding another generic harness would duplicate
  an existing capability.
- `agent-harness/harnesses/opencode/config.nix:38-49` already declares a full-access OpenCode build agent. The capture
  supplies no reverse-engineering-specific instructions or tool protocol to add there.
- `machine-configuration/machines/chise/home.nix:53-59` is the nearby development-tool import surface. A proven local
  workflow could eventually add a narrowly named reverse-engineering module there, but no such module exists today and
  no current project consumes one.
- `machine-configuration/development/local-language-models/ollama-home-manager.nix:34-55` packages Ollama and its user
  service, but chise does not import that module. The capture does not establish that a local model is necessary, and
  adding a persistent model service before selecting a workload would solve the wrong uncertainty.

The locked package set does make experimentation cheap to start and cheap to abandon. Ghidra 11.4.2 is available for
chise without writing a package, while `nix path-info` estimates 368.48 MiB downloaded and 731.47 MiB unpacked for its
closure. radare2 6.1.2 is also available and estimates 7.85 MiB downloaded and 40.93 MiB unpacked. Those figures argue
for an on-demand exercise first, not for permanently widening every chise generation.

Nothing is replaced or deleted. A successful exercise would unblock a later decision about whether a persistent tool,
an isolated project dev shell, or an agent skill is actually the right owner.

## Why learn

**Learn**, because the transferable value is a practice that has not yet earned machine state: pair one capable agent
with one real reverse-engineering tool on one bounded, legally usable target, then measure whether the combination
reduces analysis work without inventing program behavior.

**Not adopt:** installing Ghidra globally would commit a large GUI/JDK closure without a named consumer or acceptance
test. Installing Ghidra, IDA Pro, and radare2 together would be worse: more tools are useful only when their distinct
strengths answer an observed need. The repo already supplies several harnesses, so there is no missing generic agent
surface to implement from this post.

**Not trial:** a trial needs something concrete to run. With no game, architecture, desired change, or legal boundary,
launching Ghidra would test only that a packaged GUI starts. That is weaker evidence than the decision needs.

**Not reference:** the post is too schematic to serve as an operational reference, but it does name a worthwhile
hands-on progression. **Not drop:** using a decompiler as the agent's evidence surface, and starting on a small program,
are sound constraints worth retaining.

The learning exercise is:

1. Choose one small open-source game or deliberately published reverse-engineering challenge whose build can serve as
   ground truth. State one narrow goal, such as locating the score update and explaining its callers.
2. Enter an ephemeral environment with Ghidra only. Record import settings, architecture detection, discovered symbols,
   and every place where the decompiler's output remains ambiguous.
3. Give an existing Codex or OpenCode session the project context and exported analysis, but require every claim to
   point back to disassembly, decompiler output, cross-references, or a runtime observation.
4. Validate one hypothesis against the known source or a black-box behavior test. Track elapsed time, false claims,
   manual corrections, and which Ghidra operations the agent could not perform.
5. Repeat on a second session before packaging anything. Add a project dev shell if reproducibility is the only gap; add
   a reusable skill only if the interaction protocol repeats; install a host-wide tool only if multiple projects need it.

That exercise distinguishes a useful workflow from a merely impressive demo and tells the repository which boundary,
if any, should own the eventual change.

## Drafted vault entry

To be written to `Second Brain/Inspiration/Traveler - AI-assisted game reverse engineering.md` only after approval and
linked under `## Notes` in `Developer Tooling MOC`. `topic/dev-tools` already exists in the Tag Legend; no new tag is
needed.

```markdown
---
title: "Traveler - AI-assisted game reverse engineering"
type: reference
status: filed
source-url: https://x.com/Traveler2000AD/status/2105451146856829412
creator: Traveler (@Traveler2000AD)
platform: X
captured: 2026-09-30
rating: practice
license: reference-only
tags:
  - topic/dev-tools
---
Up: [[Developer Tooling MOC]]

## Bottom line

Agent-assisted reverse engineering still needs a real evidence surface. Start with Ghidra, pair it with an existing
capable agent harness, and learn on one small program. The agent can accelerate navigation and hypothesis formation;
disassembly, decompiler output, cross-references, and observed behavior remain the evidence.

## The workflow to practice

1. Choose a small open-source game or published reverse-engineering challenge, with a known build as ground truth and
   one narrow question to answer.
2. Import it into Ghidra and record the architecture, loader choices, symbols, functions, data references, and ambiguous
   decompiler output before asking an agent to explain it.
3. Give Codex or OpenCode the project context and exported analysis. Require each claim to cite the exact function,
   address, cross-reference, or runtime observation supporting it.
4. Test one hypothesis against source or black-box behavior. Record elapsed time, hallucinated claims, corrections, and
   operations that still needed a human in Ghidra.
5. Repeat once before making the environment permanent. Use a project dev shell for one project, a skill for a repeated
   agent protocol, and a host package only when several projects need the GUI.

## What to retain

- A capable model cannot replace the reverse-engineering tool; it reasons over evidence the tool exposes.
- More tools do not automatically improve the workflow. Add IDA Pro, radare2, a debugger, or an emulator only when the
  target exposes a limitation that the current tool cannot answer.
- A successful decompilation is not yet a port. Rebuilding assets, platform APIs, timing, input, rendering, and lawful
  redistribution are separate workstreams.
- Start small enough that the original source or deterministic behavior can falsify the agent's explanation.

## Local fit

The dotfiles already provide Codex and OpenCode on chise. Use Ghidra ephemerally for the first exercise; let repeated
work determine whether the durable owner should be a project environment, a reverse-engineering skill, or a host-wide
package.

## Reuse for

[[Developer Tooling MOC]]: designing evidence-backed agent workflows for binary analysis and deciding when an
experiment has earned declarative tooling.
```
