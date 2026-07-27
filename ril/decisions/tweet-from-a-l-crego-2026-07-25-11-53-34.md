# Tweet from A. L. Crego — Extradiegetic .22

Capture: `ReadItLater Inbox/Tweet from A. L. Crego (2026-07-25 11-53-34).md`
Origin: https://x.com/ALCrego_/status/2080693489533137133
Verdict: **adopt**

## The origin as resolved

Read through the twitter skill (`twikit-cli tweet 2080693489533137133`), not a search. The tweet is three
words, `Extradiegetic .22`, plus one still image; posted 2026-07-24, 67 likes, 13 retweets, one reply that
returns empty. The media is a single 1456x2048 JPEG, fetched from the syndication endpoint at
`pbs.twimg.com/media/HOAbsBLWYAAU2Iz.jpg` and viewed directly. The author is A. L. Crego (@ALCrego_,
69k followers), who describes himself as `pic-vid-gif`; the vault already holds one of his pieces as
`A. L. Crego - The Link`.

## What it actually is

A monochrome halftone triptych, rendered entirely in dithered particle grain on pure black. Three stacked
panels: a bright skin-and-eyelid strip across the top that stops short of the right edge, a dark starfield
holding a glowing sphere cradled by a hand, and a blown-out eye with a dominant black pupil. Two hairline
vertical beams descend from bright origin dots in the top region, cross every panel boundary, and land on a
horizontal specular streak that cuts across the eye.

The title is the whole idea. *Extradiegetic* is the film-theory term for what sits outside the narrative
world: the beams belong to none of the three images, ignore the frames that separate them, and are the only
thing asserting that the three panels are one picture. The right-hand beam's origin dot floats in bare black
beside the top strip rather than inside any panel, which is the device stated outright.

## What it touches here

`home/base/desktop/screensaver/ambient-canvas/`, the darwin screensaver. Its scenes are the authoring surface
and the repo already treats captured artwork as scene source: `A. L. Crego - The Link` became
`web/scenes/the-link/` (PR #100), and the Kath Korevec and Natived captures each became a scene the same way.
This capture is the fourth in that established line, not a new capability.

Three wiring points, per `home/base/desktop/screensaver/README.md:83`:

- `web/scenes/extradiegetic/` — new, four files, 425 lines total. `extradiegetic_field_glsl.js` holds the
  uniforms, layout constants, `PlacedParticle` struct and the lattice/hash/pulse helpers;
  `extradiegetic_panel_glsl.js` places a particle for each of the five populations (beam, streak, top strip,
  middle band, eye); `extradiegetic_shaders.js` assembles the vertex program and owns the fragment shader;
  `extradiegetic_scene.js` is the WebGL renderer and the factory registration.
- `web/index.html:37-40` — the four `<script>` tags, in dependency order.
- `web/panes.js:9` — one composition, `{ panes: [{ scene: "extradiegetic" }] }`, placed directly after
  `the-link`.

It replaces and deletes nothing. It adds no dependency: no new nix input, no asset, no entry in
`web/scene-videos.json`, no yt-dlp fetch. The only ongoing cost is one more recorded segment.

## Reasoning

The piece is photographic collage, so the content cannot be regenerated and the source cannot be embedded
either: it is 1456x2048 portrait against a fixed 1920x1080 landscape loop, the same mismatch that made The
Link a reinterpretation rather than an embed. What survives that constraint is the part that carries the
title, which is procedural: beams that cross frame boundaries, and silhouette by density rather than by
outline, which is exactly the technique `the-link` already established here.

So the adopt is a reinterpretation at the loop's own resolution: the triptych rebuilt as one 340k-point field
where a hash assigns each particle to a panel, each panel dithers by density against its own luminance
function, and the beams are drawn as a population that ignores the panel bounds entirely. A pulse travels
down each beam and the streak flares as it lands, which is the one verb the piece needs; the sphere and the
pupil breathe on two incommensurate sines so the loop never visibly repeats.

The honest weakness is the top strip. The source's is a photograph and mine is a luminance function with an
eyelid crease and a lash line, which reads as structured grain rather than as skin. It is the panel that
would most benefit from being cut down or replaced, and the one to reject first.

Not a reference: the repo has a working pipeline for exactly this, and filing it as inspiration while the
three prior captures each shipped a scene would be the softer call, not the truer one.

## Drafted vault entry

To be written to `Second Brain/Inspiration/A. L. Crego - Extradiegetic 22.md` only after this lands, with the
poster saved to `_attachments/` and the wikilink added under `## By medium` → `### Generative` and
`## By use` → `### Screensaver / ambient` in `Design & Digital Art MOC`. Tags are all already in the Legend.

```markdown
---
title: "A. L. Crego - Extradiegetic .22"
type: inspiration
status: filed
source-url: https://x.com/ALCrego_/status/2080693489533137133
creator: A. L. Crego
platform: x
captured: 2026-07-25
rating: 4
license: reference-only
palette:
  - "#000000"
  - "#ffffff"
tags:
  - topic/digital-art
  - medium/generative
  - style/minimal
  - use/screensaver
---

![[crego-extradiegetic-22-poster.jpg|400]]

## Why it resonates
> Three unrelated images stacked into one frame, and two hairline beams that refuse to acknowledge the
> borders between them. The beams are the whole argument: without them this is a contact sheet, with them it
> is one picture in which an eye, a held sphere and a pupil are lit by the same light. The right beam starts
> in bare black beside the top panel rather than inside it, which says outright that the light belongs to no
> panel.

## What to steal
- A line that crosses the frame boundary is a composition device on its own. Panels do not have to share
  subject, palette or scale to read as one image; one element that ignores the gutter is enough.
- Put the origin of that element outside every panel. The beam starting in dead black is what turns a
  crossing line from an overlay into a claim about the whole frame.
- Halftone density carries the tonal range. Black is the absence of particles, white is saturation, and the
  midtones are just probability, so the same grain renders skin, a starfield and a blown-out sclera.
- Terminate the gesture. Both beams land on one horizontal streak, so the eye is given somewhere to stop
  rather than being left to drift off the bottom of the frame.

## Reuse for
[[Design & Digital Art MOC]]: multi-panel compositions, frame-crossing devices, monochrome dither fields.
```
