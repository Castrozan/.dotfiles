# ElevenLabs — Eleven v4 and v4 Turbo

Capture: `ReadItLater Inbox/Tweet from ElevenLabs (2026-09-29 00-36-16).md`
Origin: https://x.com/ElevenLabs/status/2104572127617994917
Verdict: **reference**

## The origin as resolved

Read through the Twitter channel from the capture's first link, not a topic search. `twikit-cli tweet` and
`twikit-cli thread` resolve the 2026-09-28 announcement and its eight-post self-thread. ElevenLabs presents two
new API models: Eleven v4 for maximum quality and Eleven v4 Turbo for real-time speech. The thread claims more
faithful voice cloning, inline control of delivery, emotion, pacing, reactions and sound effects, 90+ languages,
IPA pronunciation control, natural multi-speaker dialogue, and about 100 ms median inference latency for Turbo.
The final post says both models are available in ElevenAPI, ElevenAgents and ElevenCreative.

The vendor's current primary documentation was checked on 2026-09-30 rather than taking the announcement's
rank claim as independent evidence:

- https://elevenlabs.io/docs/overview/capabilities/text-to-speech/eleven-v4 identifies the API model IDs as
  `eleven_v4` and `eleven_v4_turbo`, documents stability and similarity controls plus audio tags, and says that
  speed and style sliders and SSML are not supported. It also warns that the model is still being changed after
  launch and should be re-tested over time.
- https://elevenlabs.io/docs/overview/models describes v4 Turbo's roughly 100 ms number as model inference only,
  excluding network and application latency.
- https://elevenlabs.io/docs/api-reference/text-to-speech/convert-with-timestamps documents an endpoint that
  returns base64 audio and character-level alignment. That is the concrete capability relevant to this repo,
  because the avatar needs audio-to-text timing.
- https://elevenlabs.io/pricing/api listed v4 Turbo at $0.04 per 1,000 characters and v4 at $0.08 per 1,000
  characters, temporarily discounted to $0.011 and $0.022 respectively through 2026-10-12. The launch discount
  is not a durable reason to adopt a provider.

## What it actually is

A hosted, metered text-to-speech API with two variants over the same expressive model family. V4 is the
quality-first option for prepared audio; v4 Turbo trades some of that quality budget for interactive latency.
Both are materially more controllable than a plain voice selector: bracketed audio tags can direct performance,
and the timestamp endpoint can return actual character alignment rather than forcing a client to infer timings
from subtitle blocks.

It is not a drop-in model-name upgrade for anything configured here. ElevenLabs requires its own account, API
key and provider-specific voice ID. Its inference benchmark is not end-to-end playback latency from Brazil, and
its quality advantage is perceptual, voice-specific and explicitly something the vendor says to test on one's
own content. The captured post supplies no reproducible samples or evaluation that compare it with the providers
already in use here.

## What it touches here

No machine, skill, agent or script should change from this capture alone, but four existing speech paths bound a
future comparison:

- `agent-harness/agent-instructions/skills/workstation/avatar/scripts/control-server/speech/text-to-speech-generator.js:35-65`
  generates the avatar's MP3 and animation timings with Edge TTS. It reads WebVTT-style subtitle blocks and
  `speech-timing-parser.js:61-79` spreads each block's duration evenly across its words. ElevenLabs' alignment
  endpoint could replace both the Edge TTS subprocess and that approximation if its measured latency and voice
  quality win.
- `machine-configuration/voice/scripts/hey_bot/audio/speech_synthesizer.py:25-42` also shells out to Edge TTS,
  but it waits for a complete MP3 before playback. A v4 Turbo adoption here would need to measure end-to-end
  time-to-first-audio and probably stream; the vendor's inference-only number does not establish responsiveness.
- `agent-harness/harnesses/clawde/scripts/generate_agent_voice_note.py:26-35` already uses Gemini Flash TTS with
  a delivery instruction, a configured secret and a daily limit. V4 could replace that provider only after a
  blind quality comparison on the short Portuguese and English messages this tool actually emits.
- `agent-harness/agent-instructions/skills/workstation/notify/scripts/notify.sh:17-33` uses Edge TTS for brief
  status notifications. Expressive paid synthesis adds no demonstrated value to that path, so it should stay as
  it is even if another consumer later moves.

There is no ElevenLabs secret today. The public secret inventory at
`machine-configuration/security/secrets/public-secret-sources.nix:8-15` and chise's deployment at
`machine-configuration/machines/chise/system/secrets.nix:72-76` carry Gemini but no ElevenLabs key. An adoption
would therefore add a vendor account and encrypted secret, provider and voice configuration, request and response
handling, failure behavior, usage bounds and tests. It would replace one existing provider in one consumer, not
add a fourth overlapping TTS path and not migrate all consumers at once.

## Reasoning

**Reference**, because the timestamp endpoint plus v4 Turbo's expressive real-time target is a credible future
replacement for the avatar's current Edge TTS and approximate word-timing pair. That is a specific retrieval cue,
not merely a product-launch bookmark: return here when avatar delivery or lip-sync is the limiting behavior.

Not adopt: neither the launch thread nor vendor documentation proves an improvement over the live Edge and Gemini
voices on the repo's actual Portuguese/English lines, and this host has no credential with which to exercise the
API. Shipping integration code that can only be unit-tested would prove serialization while leaving voice quality,
network latency and failure behavior unknown.

Not trial yet: a fair trial requires an account/key and a deliberately chosen voice, which are external state this
run does not own. When that prerequisite and a real quality complaint exist, run an unpackaged A/B before touching
Nix: use the same 12 short lines across Brazilian Portuguese and English; compare Edge TTS, Gemini, v4 and v4 Turbo;
blind-rate intelligibility, naturalness and instruction following; record total request time and time to first
audio; and verify that returned alignment drives the avatar mouth cues correctly. Advance only if one ElevenLabs
variant wins the intended consumer enough to justify its recurring credential, network and character-billing cost.

Not learn: there is no technique to practice until that provider evaluation exists. Not drop: character-level
alignment is a concrete capability the current avatar synthesizer approximates, so preserving the evaluated option
has durable local value even though adopting it now would be premature.

This pull request adds only the decision record. It replaces and deletes nothing, adds no runtime dependency, and
requires no Nix build or activation.

## Verification

- `twikit-cli tweet 2104572127617994917` and `twikit-cli thread 2104572127617994917` resolved the source and its
  full self-thread.
- ElevenLabs' v4 capability, model, timestamp API and pricing pages were checked on 2026-09-30 for model IDs,
  limitations, latency scope, response shape and current cost.
- A repository search on freshly fetched `origin/main` located all existing TTS consumers and confirmed that no
  ElevenLabs integration or secret is declared.
- `git submodule update --init --recursive` completed in the isolated worktree before this file was written.
- No Nix build or activation is warranted for a Markdown-only reference decision. Activation could prove nothing
  additional because this pull request changes no generated or machine behavior.

## Vault entry, drafted

After approval, save the official launch artwork as
`Second Brain/Inspiration/_attachments/elevenlabs-eleven-v4.jpg`, create
`Second Brain/Inspiration/ElevenLabs - Eleven v4 and v4 Turbo.md`, and link it under `## Notes` in
`Generative Media MOC`. Both tags already exist in the Tag Legend.

```markdown
---
title: "ElevenLabs - Eleven v4 and v4 Turbo"
type: inspiration
status: filed
source-url: https://x.com/ElevenLabs/status/2104572127617994917
creator: ElevenLabs
platform: x
captured: 2026-09-29
rating: 3
license: reference-only
palette: []
tags:
  - topic/generative-media
  - medium/product
---
Up: [[Generative Media MOC]]

![[elevenlabs-eleven-v4.jpg|400]]

## Bottom line

Eleven v4 is ElevenLabs' quality-first expressive TTS model; v4 Turbo targets real-time agent speech. The locally
useful feature is not the launch ranking but the combination of audio-tag delivery control and character-level
alignment, which could replace the avatar's Edge TTS output plus approximate subtitle-to-word timing. Do not switch
providers without a blind comparison on the short Portuguese and English lines used here.

## What to steal

- Match the variant to the consumer: v4 for prepared voice notes, v4 Turbo for interactive speech. Treat the
  advertised ~100 ms as model inference, not time to first audible output.
- Prefer returned alignment over guessed word timing when an avatar must synchronize its mouth to generated speech.
- Compare providers with identical text, voice intent and playback conditions. Blind-rate intelligibility,
  naturalness and instruction following, then measure request and first-audio latency separately.
- Keep simple notifications on the free provider. A quality model earns its account, secret and metered dependency
  only on a path where expressive speech is perceptibly valuable.
- Re-test before adopting: ElevenLabs says v4 behavior will continue changing after launch, and the September launch
  price is a temporary discount rather than the operating cost.

## Decision trigger

Trial v4 and v4 Turbo only when avatar lip-sync or delivery, hey-bot responsiveness, or Gemini voice-note quality is
a measured limitation and an ElevenLabs key and chosen voice are available. Replace one provider in one consumer
only if that A/B wins; do not add a parallel provider switch that every speech path must understand.

## Reuse for

[[Generative Media MOC]]: hosted expressive speech, TTS provider evaluation, real-time agent voices, and avatar
alignment.
```
