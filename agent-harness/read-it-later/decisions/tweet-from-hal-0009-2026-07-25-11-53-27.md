# Tweet from hal_0009 — ASCII Invader

Capture: `ReadItLater Inbox/Tweet from hal_0009 (2026-07-25 11-53-27).md`
Origin: https://x.com/hal_chemy/status/2080784856007491718
Verdict: **adopt**

## The origin as resolved

Read through the twitter skill (`twikit-cli tweet 2080784856007491718`), not a search. Posted 2026-07-24, two
words of text, `ASCII Invader`, 146 likes, 22 retweets, 6 replies, single tweet with no thread. The author is
hal_0009 (@hal_chemy, 6k followers), bio `The finite gives reality a shape. / The infinite gives it a chance.`

The media is an animated GIF, served as `video.twimg.com/tweet_video/HOBtejsW0AARC-Z.mp4`: 1080x1080, 25fps,
100 frames, exactly 4.0s. Downloaded it and stepped through it with ffmpeg rather than judging the poster
frame, which matters here because the defining behaviour only shows up across frames.

## What it actually is

A CRT terminal showing a slowly tumbling shell of coloured ASCII glyphs. Concretely:

- The screen is a barrel-distorted rounded square with a dark grey field, a vignette, and fine scanlines,
  sitting on pure black. Not a flat canvas: the curvature is visible at every edge.
- Glyphs are drawn from a small punctuation set (`@ # * + = - % :`) in saturated RGB phosphor colours, each
  with its own bloom halo, snapped to a character grid so they form horizontal runs of adjacent characters.
  That grid is what makes it read as ASCII art rather than as scattered symbols.
- The glyphs sit on a curved 3D surface that tumbles on more than one axis, so most frames show a large arc
  rather than a readable sprite.
- Sparse single-pixel stars fill the rest of the screen, and a short row of white dots sits at the bottom
  left like a status readout.
- Roughly one frame in five is a glitch burst: horizontal colour bands, per-row horizontal tearing, and RGB
  channel separation. Frames 0 and 30 of the 100 are the clearest examples.

## What it touches here

`home/base/desktop/screensaver/ambient-canvas/`, the darwin screensaver, on the same path as `the-link`
(PR #100), Kath Korevec and Natived. Three wiring points, per `home/base/desktop/screensaver/README.md:83`:

- `web/scenes/ascii-invader/` — new, four files, 566 lines. `ascii_invader_shell.js` holds the invader sprite
  bitmap, the mapping of its lit pixels onto a spherical shell, and the tumble; `ascii_invader_glyph_field.js`
  rasterises the grid-snapped glyph field, stars and status row into an offscreen 2D canvas;
  `ascii_invader_crt_shaders.js` is the CRT pass; `ascii_invader_scene.js` is the renderer and the factory.
- `web/index.html:43-46` — the four `<script>` tags, in dependency order.
- `web/panes.js:13` — one composition, after `matrix`.

It replaces and deletes nothing, and adds no dependency: no nix input, no asset, no `scene-videos.json` entry.

Two things here are genuinely absent from the repo today rather than variations on what exists. The scenes
render flat, so there is no CRT treatment anywhere: no curvature, vignette, scanlines or channel separation.
And the only glyph rendering is monochrome, `bad-apple/braille_frame_renderer.js` downsampling video
luminance into braille, plus `matrix_rain.js`; per-glyph saturated colour with bloom is new.

## Reasoning

Unlike the Crego capture worked earlier today, nothing here is photographic. The whole piece is glyphs and
screen-space effects, so this is a faithful rebuild rather than a reinterpretation, which makes it a stronger
adopt than that one was.

The build is a two-stage renderer, which is what the CRT treatment demands: rasterise the glyph field into an
offscreen 2D canvas where `fillText` is cheap, upload it as a texture, then draw one fullscreen quad whose
fragment shader does the barrel distortion, bezel mask, bloom, scanlines, vignette and glitch. The tumbling
form is the Space Invader sprite mapped onto a spherical shell, six glyphs scattered per lit sprite pixel, so
the title is honoured and the curve produces the source's arcs; the sprite reads when it faces the viewer and
dissolves into an arc when it does not. Glyphs snap to a character grid with nearest-depth-wins occupancy per
cell, which is what produces the runs of adjacent characters and also does the hidden-surface removal for
free.

The CRT pass is deliberately scene-local rather than shared. Making it a pipeline stage every scene could opt
into would be the more valuable change, but it would touch `player.js` or the compositor, and per
`README.md:243` that changes the pipeline digest and re-encodes **every** segment rather than just this one.
That is a much larger, much more expensive decision and it should be made deliberately, not smuggled in
behind a capture.

Two honest weaknesses. The glitch burst rate is tuned to roughly one slot in five at 2.4 slots per second,
which is my reading of the source's cadence and not a measurement of it. And the star field is static apart
from a twinkle, where the source's may drift; at this density it is hard to tell from the GIF either way.

## Drafted vault entry

To be written to `Second Brain/Inspiration/hal_0009 - ASCII Invader.md` only after this lands, with the poster
saved to `_attachments/` and the wikilink added under `## By medium` → `### Generative` and `## By use` →
`### Screensaver / ambient` in `Design & Digital Art MOC`. Tags are all already in the Legend.

```markdown
---
title: "hal_0009 - ASCII Invader"
type: inspiration
status: filed
source-url: https://x.com/hal_chemy/status/2080784856007491718
creator: hal_0009
platform: x
captured: 2026-07-25
rating: 4
license: reference-only
palette:
  - "#000000"
  - "#171717"
  - "#ff3d47"
  - "#47ff6b"
  - "#57e0f5"
tags:
  - topic/digital-art
  - medium/generative
  - style/retro
  - use/screensaver
---

![[hal-0009-ascii-invader-poster.jpg|400]]

## Why it resonates
> A tumbling shell of coloured punctuation on a curved CRT, where the screen itself is doing as much work as
> the subject. The glyphs never resolve into anything for long, and that is the point: the form is legible
> for a moment as it turns through the viewer and then goes back to being an arc of characters.

## What to steal
- Snap glyphs to a character grid and the same scatter reads as ASCII art instead of as symbols. The runs of
  adjacent characters are the whole tell; unsnapped, identical content looks like confetti.
- The screen is a material. Barrel distortion, vignette, scanlines and a dark grey field do more for the
  retro read than the content does, and they cost one fullscreen pass over whatever you already drew.
- Colour per glyph, not per scene. A small saturated phosphor palette assigned per character, each with its
  own bloom, gives depth to a flat grid without any actual shading.
- Break it on a schedule. Roughly one frame in five tears: colour bands, row displacement, channel split.
  Constant glitch is noise, occasional glitch is a machine that is nearly holding together.
- Let the subject be unreadable most of the time. The sprite is recognisable in maybe a fifth of the loop,
  which is what makes the moment it faces you worth waiting for.

## Reuse for
[[Design & Digital Art MOC]]: CRT and terminal aesthetics, glyph-grid rendering, glitch punctuation.
```
