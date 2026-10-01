# Simone Canc — AI character viral-video account

Capture: `ReadItLater Inbox/Tweet from Simone Canc (2026-09-30 23-51-30).md`
Origin: https://x.com/simonecanciello/status/2105317517665194490
Verdict: **drop**

## The origin as resolved

Read through the Twitter skill from the capture's first link, not a topic search. `twikit-cli tweet` and
`twikit-cli thread` resolve one post by Simone Canc (@simonecanciello), published 2026-09-30, with no
self-thread or quoted post. At inspection it reported about 3.6 million views, 9,763 likes, 415 reposts and
162 replies.

The post says a realistic AI character can reach 200,000 followers in one week by making a character sheet
and swapping that character into viral videos. Its two attached images are the whole supporting material:

- a TikTok profile screenshot for `Jean Phil` / `@jean_philanthrope`, showing 209.3K followers, 3.7M likes
  and seven visible posts with displayed view counts from 2M to 10.2M; and
- a 1254-by-1254 character sheet with five full-body angles and three close portraits of the same
  blond, moustached man in a brown suit.

The images support that the depicted account had reach and that a consistent character sheet existed. They
do not establish the account's age, the claimed one-week interval, which posts were generated, whether the
source videos were licensed, or any causal link between the sheet and the follower count. The source names
no image model, video-editing model, swap tool, prompt, settings, cost, failure rate or publishing workflow.

## What it actually is

A two-step content-growth sketch, not a reproducible tutorial or a tool:

1. establish a recognisable synthetic person with a multi-view character sheet;
2. replace the subject in already successful short-form videos so the character inherits familiar formats
   and distribution patterns.

The useful idea is continuity: a sheet gives an image or video model several views of one identity instead
of asking it to reconstruct that identity from prose on every generation. The rest of the proposal depends
on undisclosed generation and editing tools, platform operation, and permission to reuse the source videos.
The follower claim is an outcome screenshot, not evidence that another operator can reproduce the result.

## What it touches here

Nothing in the running configuration.

The two superficially adjacent owners have deliberately narrower jobs:

- `agent-harness/agent-instructions/skills/workstation/avatar/SKILL.md:2-20` controls the existing local
  VTuber renderer, virtual camera and virtual microphone. It does not generate character identities, edit
  source footage or publish social content.
- `agent-harness/agent-instructions/skills/media/youtube/SKILL.md:2-15` supports YouTube search and playlist
  management. It does not create, upload or schedule generated video, and the source is about a TikTok and
  Instagram account rather than a YouTube workflow.

A repository-wide search found no character-generation, video-generation, video identity-transfer,
TikTok, Instagram or social-publishing module to extend or replace. Adding one from this source would require
inventing every material boundary: model and host, input provenance, likeness policy, video assembly,
quality review, credentials, publishing authority, rate and spend limits, and platform-compliance checks.

It replaces nothing, deletes nothing and unblocks nothing. This pull request adds only this decision file,
the required reviewable audit trail for a no-code verdict.

## Reasoning

**Drop**, rather than adopt, trial, learn or reference.

The strongest version of the idea—use a multi-view sheet to hold a synthetic character's identity across a
batch—is already captured more concretely in the Second Brain's `Anime character post generation pipeline`.
That plan specifies a character LoRA, fixed identity prompt, optional IPAdapter FaceID, a still-image stage,
Wan image-to-video, compute choices, costs and lawful scope. This post adds no mechanism that would improve
that plan.

The remaining novelty is to swap the character into viral videos. That is a weak build target: the source
does not distinguish licensed templates from copied creators' footage, gives no transformation or
attribution standard, and supplies no evidence that the headline growth resulted from this method. A trial
would therefore test a content-copying strategy before it had a defensible input-rights boundary, while a
repository adoption would hard-code an operation the source never specifies.

It is not a learn because there is no missing skill here that the source teaches: it supplies neither a
repeatable identity-transfer technique nor exercises with measurable feedback. It is not a reference because
the one durable technique is already filed in a stronger reference, and keeping this would preserve an
unverified growth claim rather than new knowledge.

The cost of dropping it is only the loss of a striking outcome screenshot. The benefit is avoiding a
duplicate note and declining to turn an unsupported social-growth claim into a machine capability.

## Verification

- `twikit-cli tweet 2105317517665194490` and `twikit-cli thread 2105317517665194490` resolved the source and
  confirmed that it is a single post with no self-thread.
- Twikit's media objects resolved two attached JPEGs: 1014 by 2048 and 1254 by 1254. Both were downloaded
  from their `pbs.twimg.com` URLs and inspected at original resolution.
- A repository search on freshly fetched `origin/main` found no character-generation, face-swap,
  video-generation, TikTok, Instagram or social-publishing implementation.
- `git submodule update --init --recursive` completed in the isolated worktree before this file was written.
- No Nix build or activation is warranted for a Markdown-only drop decision. Activation could prove nothing
  about the unchanged machine.

## Drafted vault entry

None. A drop files nothing. The existing `Anime character post generation pipeline` remains the plan of
record for consistent-character image and video batches.
