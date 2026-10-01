# Google Flow — creative prompting with Gemini Omni

Capture: `ReadItLater Inbox/Tweet from Google Flow (2026-09-30 19-49-51).md`
Origin: https://x.com/FlowbyGoogle/status/2105398907702595802
Resolved article: https://x.com/i/article/2105378350352998400
Verdict: **reference**

## The origin as resolved

Read through the Twitter channel from the capture's first link, not a topic search. The capture is a link-only post by
Google Flow (@FlowbyGoogle), published 2026-09-30 at 20:46:30 UTC. Its `t.co` target is the X Article **Creative
prompting with Gemini Omni in Google Flow**, published by the same official account at the same time.

`twikit-cli tweet` exposes the post, article title and preview but not the body. An unauthenticated browser reaches X's
login shell. The authenticated Twitter `TweetResultByRestId` response with article rich content enabled returns the
complete article from that same status, including its ten sections, examples and media.

The article recommends a specific Flow workflow:

- give the model high-level constraints for environment, costume, texture, lighting, expression and camera treatment
  instead of specifying every object;
- anchor appearance and motion with first and last frames to reduce visual drift;
- name and tag images, characters, settings, style references, motion/audio clips and storyboards, then assign each
  reference a role in the prompt;
- adjust generated motion with explicit speed changes and timed ramps rather than only saying “fast” or “slow”;
- transfer pose, motion, materials, visual style and colour grading from different references;
- direct kinetic typography by naming its style, placement, alignment, reveal and rhythm;
- distinguish one continuous shot from a multi-shot sequence explicitly, because the model otherwise introduces cuts;
- describe transitions as ordered visual beats when cuts are wanted;
- keep conversational edits narrow and state that everything else must remain unchanged; and
- use timestamps for action and native-audio synchronization, plus negative constraints for dialogue, cuts, sound,
  texture or camera movement that should be absent.

## What it actually is

An official, product-specific prompt playbook for Gemini Omni Flash inside Google Flow. Its durable contribution is not
one magic prompt. It separates a video request into appearance anchors, reference roles, camera grammar, temporal
instructions, narrow edit scope and negative constraints. That is a useful checklist when authoring a first Flow
prompt packet.

It is not an API or automation guide. The article gives no endpoint, model identifier outside the Flow product,
pricing, credit cost, account requirement, output-resolution contract, safety-policy detail, reproducibility study or
comparison against another generator. The examples are vendor guidance, not evidence that the same wording behaves
identically in Runway, Wan, Veo outside Flow or a later Gemini release.

## What it touches here

No runtime file should change for this capture. This pull request adds only this decision record, replaces and deletes
nothing, adds no dependency or credential, and spends no generation credits.

The current repository boundaries explain why:

- `agent-harness/agent-instructions/skills/media/youtube/SKILL.md:3-15` owns YouTube search and playlist operations,
  not video generation, prompt authoring or publishing.
- `machine-configuration/media/video-production/obs-studio-home-manager.nix:10-31` packages OBS Studio for local
  recording. A hosted Flow prompt guide neither extends nor replaces that package.
- `agent-harness/harnesses/clawde/scripts/generate_agent_voice_note.py:26-35` uses a Gemini 2.5 Flash TTS endpoint for
  bounded voice notes. Its `gemini-api-key` does not establish Google Flow access or make this article's video workflow
  callable from an agent.

The materially adjacent repository decision is open PR #192. Its decision file proposes a bounded private trial of a
source-to-script-to-generated-video-to-YouTube pipeline and names the future YouTube command and producer-agent owners.
This article can inform a Flow-specific prompt packet if Flow is evaluated later, but it does not answer that trial's
questions about repeatable output, cost, factual support, assembly, upload or publishability. It should not revise or
pre-empt that pull request.

The reference therefore unblocks one narrower task: starting a future Flow evaluation with an official checklist for
anchors, tagged ingredients, shot continuity, edits, timecodes and negatives instead of rediscovering those controls.
It replaces no current workflow and makes no claim that the checklist transfers unchanged to another provider.

## Why reference

Reference is the strongest supported verdict because the source is an official guide with a clear future retrieval
cue, while no repository owner should absorb it today.

This is not an `adopt`: adding a Flow skill, provider integration or generic video-prompt policy would create a new
capability from UI advice that supplies neither an API surface nor local evidence. Copying the advice into the bitmap
image-generation tool would also blur the boundary between still-image generation and video editing.

This is not a `trial`: the capture presents techniques rather than a claim or project that needs a new experiment. The
separate end-to-end video trial on PR #192 already owns the costly question of whether automated generation earns
permanent wiring. A second trial here would duplicate that decision without credentials, a selected Flow use case or
acceptance criteria that differ from the existing trial.

This is not a `learn`: there is no current course of practice, feedback loop or recurring local task for Gemini Omni
in Flow. If Flow becomes the selected generator, applying the checklist to real clips becomes part of that evaluation,
not a standalone study item.

This is not a `drop`: the source preserves a compact set of concrete controls that are easy to forget when a future
Flow prompt is written, especially the difference between continuous-shot and directed-cut instructions, the use of
first/last-frame anchors, and the narrow-edit rule. Those make it more useful than a product announcement or a gallery
of attractive outputs.

## Verification

- `twikit-cli tweet 2105398907702595802` resolved the captured status, author, timestamp and exact short link.
- `curl -sSIL https://t.co/tXKgDJF13P` resolved the link to the captured X Article.
- PinchTab opened that exact article and confirmed the unauthenticated login boundary; no other browser page was used
  as a substitute source.
- The authenticated Twitter `TweetResultByRestId` query with article rich content enabled returned the title, complete
  content blocks, media entities and publication metadata from the captured status.
- A search on freshly fetched `origin/main` confirmed the YouTube, OBS and Gemini TTS boundaries above and found no
  Google Flow, Gemini Omni video or general video-generation integration.
- PR #192's body, full decision file and comment thread were read; it remains an unanswered trial proposal rather than
  an approved workflow this capture may modify.
- `git submodule update --init --recursive` completed in the fresh worktree before this file was written.

No Nix build or activation is warranted for a Markdown-only reference decision. The diff changes no evaluated
configuration, package, generated artifact or running behavior. Activation could prove nothing additional; only a
future authenticated Flow evaluation can test prompt adherence, generation cost and output quality.

## Drafted vault entry

After approval, save the article cover as
`Second Brain/Inspiration/_attachments/google-flow-gemini-omni-prompting.jpg`, create
`Second Brain/Inspiration/Google Flow - Creative prompting with Gemini Omni.md`, and link it under `## Notes` in
`Generative Media MOC`. `topic/generative-media` and `medium/product` already exist in the Tag Legend.

```markdown
---
title: "Google Flow - Creative prompting with Gemini Omni"
type: inspiration
status: filed
source-url: https://x.com/FlowbyGoogle/status/2105398907702595802
creator: Google Flow
platform: x
captured: 2026-09-30
rating: 4
license: reference-only
palette: []
tags:
  - topic/generative-media
  - medium/product
---

Up: [[Generative Media MOC]]

![[google-flow-gemini-omni-prompting.jpg|400]]

## Bottom line

Google's prompt guide for Gemini Omni Flash in Flow is most useful as a control checklist. Define appearance with
visual anchors and tagged references, define motion with camera grammar and time, and constrain edits and exclusions
explicitly. Treat the wording as Flow-specific vendor guidance and re-test it whenever the model changes.

## What to steal

- Use first and last frames to lock composition, palette and subject before asking the model to solve motion.
- Give each reference one named role: character, setting, style, motion, audio or ordered storyboard. Do not leave the
  model to infer why an asset was attached.
- State shot grammar. Ask explicitly for one continuous shot with no cuts, or describe the ordered cuts and
  transitions you do want.
- Direct tempo with measurable events: speed multipliers, time ramps, timestamps and beats. “Fast” and “slow” leave
  too much unspecified.
- Keep edits surgical. Name the one change, preserve character features when relevant, and say that everything else
  stays the same.
- Add structural negatives for unwanted dialogue, cuts, sound effects, materials and camera movement instead of only
  describing the desired content.

## Decision trigger

Use this checklist when Google Flow is selected for a real clip or compared in a bounded video-generation trial. Log
which controls the current model follows, the retries and credit cost, and any wording that no longer works. Do not add
a Flow integration or copy these rules into another provider's skill without that evidence.

## Reuse for

[[Generative Media MOC]]: Gemini Omni and Google Flow prompt design, visual anchors, reference-driven video, shot
continuity, conversational edits and timed audiovisual direction.
```
