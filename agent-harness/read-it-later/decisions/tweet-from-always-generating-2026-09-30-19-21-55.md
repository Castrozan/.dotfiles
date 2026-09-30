# Always Generating — automated YouTube Shorts channel

Capture: `ReadItLater Inbox/Tweet from Always Generating (2026-09-30 19-21-55).md`
Origin: https://x.com/notiansans/status/2104676565829505527
Verdict: **trial**

## The origin as resolved

Read through the Twitter skill from the capture's first link, not a topic search. `twikit-cli tweet` and
`twikit-cli thread` resolve a single post from Always Generating (@notiansans), published 2026-09-28. It says that
Claude Opus 5.5 is especially effective at motion design when paired with Runway MCP and offers a bracketed prompt for
a 60-second explainer about the history of ice cream. The thread contains no additional instructions. Replies include
one person saying repeated attempts did not reproduce the result, one reproduction made without Runway, and another
made with different image, voice and orchestration tools. They are anecdotes, not a repeatable pipeline.

The attached example matters more than the truncated tweet text, so I resolved it with `nix run nixpkgs#yt-dlp`,
downloaded it, inspected six frames across the full duration, and probed the media. It is a 60.05-second, 24 fps,
1920x1080 **landscape** explainer with AAC audio. It moves through a scrapbook-like illustrated timeline of ice cream:
ancient China, seventeenth-century Paris, the 1843 hand-cranked freezer patent, the 1904 World's Fair, and modern
varieties. The piece is polished, but it is not a YouTube Short's 9:16 composition and it demonstrates one generated
artifact, not niche research, factual sourcing, brand creation, repeatable assembly, upload, scheduling, or channel
operation.

Runway's own current documentation confirms that its generation MCP is real and hosted at
https://mcp.runwayml.com/mcp. It uses interactive OAuth, consumes the connected Runway account's credits, and exposes
image and video models. That establishes a viable generation surface, not the economics or repeatability of this
specific workflow. Runway's developer pricing at https://docs.dev.runwayml.com/guides/pricing/ is model-, duration-
and resolution-dependent, so retries are part of the operating cost rather than a free creative loop.

YouTube's official `videos.insert` documentation at
https://developers.google.com/youtube/v3/docs/videos/insert confirms that an API client can upload the rendered file.
It also says uploads from unverified API projects created after 2020-07-28 are restricted to private viewing until the
project passes a compliance audit. YouTube's spam policy at https://support.google.com/youtube/answer/2801973 also
bars automated or synthetic mass production that floods the platform with minimally changed content, while its
monetization policy at https://support.google.com/youtube/answer/1311392 excludes generic, repetitive or templated
mass-produced work. A technically successful uploader is therefore not proof that an unattended channel is a sound
product.

## What it touches here

This pull request changes no runtime file. It replaces and deletes nothing; its decision record is the only diff.

A successful trial would justify one narrow follow-up adoption, using existing owners instead of inventing a parallel
stack:

- `agent-harness/agent-instructions/skills/media/youtube/SKILL.md:3-15` currently promises search and playlist
  management only. It would document private upload, processing-status inspection and the audit restriction.
- `agent-harness/agent-instructions/skills/media/youtube/scripts/youtube-cli.py:16-80` has no `upload` command, while
  `youtube_videos.py:52-73` only reads video information. Those are the places to add resumable `videos.insert` and a
  processing-status read. The existing broad OAuth scope in
  `youtube_authentication.py:6-13` already covers uploads, so a second authentication mechanism should not be added.
- A dedicated producer would belong under `agent-harness/harnesses/clawde/agents/` and be imported beside the other
  host agents at `machine-configuration/machines/chise/home.nix:7-17`. Its Runway connector, budget and publishing
  authority should be scoped to that agent, not added to the shared production plugin at
  `agent-harness/agent-instructions/production-plugin/mcp-servers.nix:18-29` where every agent would inherit a metered
  generator.

No such files should be added before the trial. This host currently has neither YouTube CLI OAuth credentials/token nor
a Runway declaration or secret. More importantly, code with mocked providers would prove request serialization while
leaving generation quality, credit burn, OAuth renewal, YouTube processing and policy-safe editorial variation
untested.

## Why trial

The captured note asks for proof, and the source does not provide it. The first plausible implementation—wire Runway
to a scheduled agent and add YouTube upload—would be operationally complete but evidentially empty. The uncertain part
is not whether Python can call two APIs; it is whether the system can repeatedly make accurate, distinct, watchable
vertical videos at an acceptable cost without hand editing.

Run one unpackaged experiment before permanent Nix or agent wiring:

1. Use the working niche **the hidden history of everyday objects**. It fits the source's explanatory style, has
   abundant primary references, and makes factual quality auditable. Treat **Everyday in 60** as a disposable trial
   label, not an account name to register before checking availability.
2. Produce three episodes—ice cream, the zipper and the ballpoint pen—from source packet to script, shot list, narration,
   generated visual assets, 9:16 assembly, captions, thumbnail and description without hand-editing the media.
3. Upload all three through `videos.insert` as **private**, never public. Record the Runway model, generations and
   retries, credits and dollar cost, wall time, failed stages, source URLs, output checksum and YouTube processing
   result for each episode.
4. Require all three files to be 1080x1920, 45-60 seconds, intelligible with sound off, factually supported by the
   supplied sources, visibly distinct from one another, and successfully playable after YouTube processing. Cap the
   whole experiment at US$30 and US$10 per accepted episode; stop rather than silently exceed either bound.
5. Have a human review the three private URLs once. The trial passes only if all three needed no media edit, contain no
   unsupported factual claim, avoid repeated template footage, and are good enough that the reviewer would publish at
   least two unchanged. This review judges the output; it is not a hidden manual production stage.
6. Only after that pass, add the upload command and a dedicated producer agent. Public scheduling remains disabled
   until the Google API project is audited, the channel identity is chosen, and the operator explicitly activates the
   agent. A failed trial leaves the current repo unchanged and records which stage failed.

This is not an `adopt`: no live end-to-end evidence exists and the required accounts are absent. It is not a
`reference`: the capture carries a concrete project request and a falsifiable experiment can settle it. It is not a
`learn`: the goal is a runnable commercial/creative workflow, not a practice exercise. It is not a `drop`: Runway MCP
plus YouTube's upload API can cover the two external ends of the pipeline, and the missing middle is testable at
bounded cost.

The trial replaces no current capability. It unblocks the narrower decision of whether a permanent producer agent and
upload command have earned their maintenance and policy burden.

## Verification

- `twikit-cli tweet 2104676565829505527`, `thread`, and `replies` resolved the source, its lack of a self-thread, and
  the available reproduction context.
- `nix run nixpkgs#yt-dlp -- --dump-single-json ...` resolved a 60-second source video; the downloaded 640x360 variant
  was probed with `ffprobe` and sampled with `ffmpeg`. The source also exposes a 1920x1080 variant.
- Runway's official MCP connection guide, developer pricing guide, and YouTube's official upload, spam and monetization
  documentation were checked on 2026-09-30.
- A repository search on freshly fetched `origin/main` confirmed that the YouTube skill supports search, information
  and playlists but not upload, and that no Runway integration is declared.
- Presence checks confirmed that `~/.config/youtube-cli/credentials.json`, its token, and the expected local Runway
  secret paths are absent. No authentication flow was started and no account, channel or public post was created.
- `git submodule update --init --recursive` completed in the isolated worktree before this file was written.
- No Nix build or activation is warranted for a Markdown-only trial decision. Activation could prove nothing about the
  unchanged machine; only a later authenticated private-upload trial can prove the external workflow.

## Drafted vault entry

After approval, write `Second Brain/Inspiration/Always Generating - Automated YouTube Shorts trial.md` and link it under
`## Notes` in `Generative Media MOC`. `topic/generative-media` already exists in the Tag Legend; no new tag is needed.

```markdown
---
title: "Always Generating - Automated YouTube Shorts trial"
type: reference
status: filed
source-url: https://x.com/notiansans/status/2104676565829505527
creator: Always Generating
platform: x
captured: 2026-09-30
rating: trial
license: reference-only
tags:
  - topic/generative-media
---
Up: [[Generative Media MOC]]

## What the source proves

Runway MCP plus a frontier coding agent can produce a polished 60-second motion-graphic explainer. The example is a
landscape history of ice cream, not a vertical Short, and it proves neither repeatability nor an automated channel.

## Trial to run

Use “the hidden history of everyday objects” as the niche and create three 45-60 second, 1080x1920 episodes: ice cream,
the zipper and the ballpoint pen. Automate source packet to script, shot list, narration, generated visuals, assembly,
captions, thumbnail, description and private YouTube upload. Keep each factual claim tied to a supplied source and
record generations, retries, credits, dollar cost, wall time, failures and output checksum.

The experiment is capped at US$30 total and US$10 per accepted episode. It passes only if all three private uploads
process and play, all three need no media edit, none contains an unsupported factual claim or repetitive template
footage, and a human reviewer would publish at least two unchanged. Public scheduling is a separate decision after
Google's API audit and explicit activation.

## What to steal

- Treat generation, assembly and distribution as separate measured stages; one attractive sample proves only the first.
- Prove full automation against private uploads, where OAuth and YouTube processing are real but a bad output cannot
  reach an audience.
- Make retries and rejected generations visible costs. Cost per accepted episode matters more than the advertised
  price of one successful clip.
- Bind every factual line to the source packet before narration and visual generation, so style cannot launder a
  hallucination into a confident explainer.
- Require meaningful episode-to-episode variation. A template with swapped nouns is not a channel and may violate
  YouTube's spam or monetization rules.

## Reuse for

[[Generative Media MOC]]: deciding whether an automated short-form video pipeline has earned permanent agent wiring.
```
