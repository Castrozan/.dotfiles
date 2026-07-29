# Screensaver

Ambient eye-candy for an idle desktop. This domain owns both implementations of the
screensaver concern, one per platform, because each platform has a different renderer
whose cost profile forced a different choice.

| Platform | Implementation                                                   | Renderer                                                     | Trigger                                                                              |
| -------- | ---------------------------------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| darwin   | `ambient-canvas/` (WebGL scenes pre-recorded to a looping video) | native Swift `AVPlayer` window, VideoToolbox hardware decode | `com.dotfiles.ambient-canvas` launchd keep-alive, pinned to Hammerspoon workspace 11 |
| Linux    | herdr terminal grid (`scripts/launch_herdr_screensaver.py`)      | wezterm cell repaint                                         | manual: the `h` alias runs `herdr-screensaver`                                       |

## Why two implementations

The screensaver started as the herdr terminal grid: a herdr workspace split into panes
running `equation-art` (precompute-replayed), `cbonsai`, and `cmatrix`. On darwin that
was replaced by the Chrome `ambient-canvas` because rendering generative art into terminal
glyph cells forces wezterm to repaint thousands of cells every frame, and wezterm is the
single interactive GUI process, so the animation competes directly with the interactive
smoothness that is a hard requirement here. A GPU WebGL surface in its own Chrome process
never touches wezterm's frame budget.

### Measured cost (kira, M-series)

The terminal grid taxes wezterm even when its window is parked off-screen, because an
off-screen window is not "occluded" to macOS and wezterm never throttles it:

- Terminal grid, wezterm CPU: ~54% of a core parked off-screen, ~43% visible, ~0.1% once
  the herdr workspace is closed. The backend animation processes themselves are ~0.3% CPU
  and ~63MB. So the real cost is the wezterm repaint, not the scenes.
- Live-WebGL `ambient-canvas` (the previous darwin design): the isolated Chrome tree
  generated the animation every frame, which measured well over a full core (renderer plus
  a dedicated GPU process) 24/7, because the window is pinned across Spaces so macOS never
  occludes it into throttling. The generative art is the cost, and it is paid continuously.
- Recorded-loop `ambient-canvas` (the current darwin design): the native player sits at ~1% of
  a core and ~20MB of footprint while its workspace is on screen, and at exactly 0% while it is
  not, because the visibility gate stops decode. The compute moved to two one-off costs instead:
  a Chrome record pass that encodes only the compositions whose fingerprint changed, and the
  resident disk of the segments, which grows linearly with the recorded dwell and the playlist
  length.

The current darwin design pays the generative cost once. The WebGL scenes are recorded to a
short looping video and the 24/7 window is a native Swift `AVPlayer` (no browser at all), which
routes the loop through VideoToolbox for hardware decode, so the live per-frame compute
disappears. The player also pauses playback whenever its window is not actually on screen for the
viewer: when workspace 11 is not the active Space, when the window is fully covered, or when the
display sleeps. So it decodes zero frames when nobody is looking at it and resumes seamlessly on
return. A browser only runs offscreen for the ~30s record step that regenerates the loop. On darwin the isolation still wins over the
herdr grid, so `ambient-canvas` is the darwin screensaver and the herdr grid is gated to Linux.

## ambient-canvas (darwin)

The animation is authored as live WebGL/canvas scenes; those scenes are the source of truth.
A build step records them once into a looping video, and the 24/7 window plays that video.

### Scenes (authoring surface)

`ambient-canvas/web/index.html` loads a full-window canvas grid driven by a playlist. The
screensaver cycles whole-screen compositions, and adding eye candy is appending one object:

- `web/panes.js` declares `AMBIENT_CANVAS_ROTATION_SECONDS` (the default dwell) and
  `AMBIENT_CANVAS_PLAYLIST`, an ordered list of compositions. Each is
  `{ panes: [{ scene, options, area? }], durationSeconds?, layout? }`. `layout` is optional:
  a single-pane composition defaults to one full-screen cell, so the common case is one line.
  `options` is passed straight to the scene factory, which is how `variant` reaches yuruyurau
  and `videoId` reaches bad-apple.
- Loop length is derived, never authored: each composition's length is
  `durationSeconds ?? AMBIENT_CANVAS_ROTATION_SECONDS`, and every composition is recorded
  exactly once as its own file, so no total is authored anywhere.
- `web/player.js` owns the segment walk. `resolveSegment(elapsed)` is a pure function
  returning `{ index, localElapsedSeconds }` that drives the live page; the recorder walks the
  same playlist one composition at a time, and both drive a scene by `localElapsedSeconds`
  counted from zero at segment entry, so cut points are identical. Renderers are built and torn
  down per segment, so live GL contexts are bounded by panes-per-composition rather than
  playlist length, and each scene restarts cleanly on entry.
- `web/scenes/*.js` each register a scene factory on
  `window.AMBIENT_CANVAS_SCENE_FACTORIES[name]`. A factory is
  `(canvasElement, options) => { render(localElapsedSeconds), resize(width, height) }`, plus
  three optional members: `dispose()` to release GPU resources at segment teardown, `ready`
  (a promise) for scenes with assets to load, and `prepareFrame(localElapsedSeconds)` (a
  promise) for scenes whose frame cannot be produced synchronously. The record loop awaits
  both, which is what makes a video-backed scene deterministic.

### Adding a scene

Three wiring points, all three required, and each one fails differently when it is the one
missed. Write `web/scenes/<name>.js` registering the factory under the name you intend to use,
add its `<script>` to `index.html` (a missing tag leaves the factory undefined and the pane
renders nothing), then append one composition to `AMBIENT_CANVAS_PLAYLIST` in `panes.js` (a
scene wired but never listed is dead code the recorder never enters). Nothing else registers a
scene: there is no manifest and no directory scan, so the name in `panes.js` and the key in
`AMBIENT_CANVAS_SCENE_FACTORIES` must match exactly.

The factory signature is `(canvasElement, options) => renderer`. `options` is whatever the
composition declared, which is how `variant` reaches yuruyurau and `videoId` reaches bad-apple.
`render(localElapsedSeconds)` draws one frame, `resize(pixelWidthDevice, pixelHeightDevice)`
takes device pixels rather than CSS pixels, and the three optional members are `dispose()`,
`ready`, and `prepareFrame(localElapsedSeconds)` as described above.

A fourth requirement is not wiring but theme: **the background comes from
`web/ambient_canvas_palette.js`, never from a literal.** The playlist cuts between whole-screen
compositions with no crossfade, so a scene that clears to its own black flashes against every
neighbour that clears to the dark blue. The palette declares that blue once and derives every form
a scene needs from it: `backgroundHex` for a 2D `fillStyle`, `backgroundColorChannels` for an
`rgba(...)` built by concatenation, `backgroundGlColor` to spread into `gl.clearColor`, and
`backgroundGlslVector` to interpolate into a shader whose fragment stage paints its own field. It
also carries `accentOrangeColorChannels` for the orange the theme is built around, and
`luminanceSamplingFloorHex` for the one genuinely black surface here, bad-apple's offscreen
luminance-sampling canvas, which is a measurement reference rather than anything on screen.
`test_scene_background_palette.py` enforces this: it rejects any dark colour literal in a scene or
in `panes.js`, requires every registered scene to reference the palette, and checks that
`index.html` loads the palette before the first scene script and paints its CSS the same colour.

Retuning the theme is editing the one hex in the palette. That re-encodes every segment, which is
correct and is why the palette is a recording-pipeline digest input rather than a per-scene one: a
background change touches every composition, and a palette left out of the fingerprint would leave
the whole recorded loop stale on disk with no way to notice.

What actually breaks a new scene, in the order it tends to bite:

- **A scene whose fragment shader paints every pixel owns its own background.** `gl.clearColor` is
  dead code under a full-surface quad, so the palette has to reach the GLSL: interpolate
  `backgroundGlslVector` into the source and composite over it, additively where the scene emits
  light (`cube-lattice`) or through `mix` where a mask fades to nothing (`ascii-invader`'s bezel).
  Setting only the clear colour looks fixed in the source and records black.
- **A 2D scene that fades rather than clears must start from an opaque background.** `matrix`
  paints its trail fade at a tenth alpha, and composited onto a fresh transparent canvas that
  converges toward the background from below and settles several 8-bit steps short of it, off-theme
  against its neighbours. Filling the background once in `resize` gives the fade a correct base.
- **A WebGL scene must honor `options.preserveDrawingBuffer`** and pass it into `getContext`.
  The recorder injects it through `AMBIENT_CANVAS_RENDERER_OPTION_OVERRIDES`, because it
  composites each pane canvas into a separate encode canvas after `render` returns, and a
  context without a preserved drawing buffer has already been cleared by then. The live page
  looks perfect and the recorded loop comes out black, so this is the one trap that survives
  every manual check short of watching the recorded file.
- **Draw as a pure function of `localElapsedSeconds`.** The recorder frame-steps a synthetic
  clock at `frameIndex / fps`, so anything reading `performance.now()`, `Date.now()`, or a
  `requestAnimationFrame` delta records as a stutter or a still. State accumulated across
  `render` calls is equally unsafe: the same segment is rebuilt from scratch on every entry.
- **`Math.random` at build time reseeds per recording pass**, so the recorded loop is not
  pixel-seamless. Boundaries are cuts and the loop is long enough that the seam is unobtrusive,
  but a scene that wants a stable look across renders should hash its point index instead.
- **Hash carefully in GLSL.** ES 1.0 has no bit operations, and the usual
  `fract(sin(dot(...)))` degrades badly when it is fed a large point index in fixed linear
  steps: consecutive points walk a constant phase through `sin`, highp loses the low bits past
  roughly 1e5, and the result is visible moire rather than noise. Reduce the index to a small
  two-dimensional lattice first and hash that.
- **Release the context in `dispose()`.** Renderers are torn down at every segment boundary, so
  a scene that leaks a GL context exhausts the browser's context limit part way through a
  record pass and the rest of the loop renders empty.
- **Keep each file under 200 lines.** The repo hook enforces it. A scene that outgrows one file
  becomes a domain subfolder of flat siblings, `web/scenes/<name>/<name>_*.js`, with every
  file's `<script>` listed in dependency order; `scenes/bad-apple/` is the worked example.

Iterate against the live page rather than the recorded loop: serve `web/` and open
`index.html`, which walks the same playlist the recorder does, so what you see is what gets
captured except for `preserveDrawingBuffer`. Only then run `ambient-canvas-render`.

Every composition costs its dwell in file size at roughly 1.6MB per recorded second, so one
30s addition adds a ~48MB segment file. It costs only its own ~30s of encode, not the whole
playlist's, because the record pass is incremental: see Refresh.

### Record and play

- `web/recorder.js` activates only when `index.html` is opened with `?record`. It drives a
  deterministic frame-stepped render rather than a real-time capture, one composition at a time:
  it builds that composition's renderers, and for each frame index awaits every pane's
  `prepareFrame`, composites every pane canvas into one canvas (WebGL panes honor the injected
  `preserveDrawingBuffer` option), and encodes it with an explicit timestamp through
  `VideoEncoder` into a fresh vendored `mp4-muxer`, then POSTs that one segment to a local
  receiver. Because the synthetic clock is `frameIndex / fps` rather than wall time, the output
  is exact CFR no matter how slowly a frame renders. `MediaRecorder` was
  replaced because it is real-time-only and could not hold 30fps at full resolution. The codec
  is H.264 in MP4 so the M-series media engine decodes the loop in hardware.

  The capture resolution follows the display rather than being fixed, because the player fits
  the loop with `.resizeAspect` and any aspect the loop does not share with the panel comes back
  as bars. `resolve_capture_pixel_dimensions` holds the height at 1080 and derives the width from
  the screen, rounded to an even number for the encoder: a 1920x1080 panel resolves to 1920x1080
  unchanged, and a 3024x1964 MacBook XDR (1512x982 in points) resolves to 1662x1080. Recorded 16:9
  on that XDR the loop fitted to width at 1512x850 and left a 66pt letterbox above and below,
  which reads as a header and a footer framing the scene. The derivation is uniform and there is
  no per-host branch: each machine records its own segments, so each one resolves its own panel.
  The dimensions ride in the `width` and `height` record query parameters and land in the capture
  signature, so they are already fingerprint inputs and a machine that changes displays
  re-encodes on its own.

  The screen is read with `system_profiler SPDisplaysDataType -json`, taking
  `_spdisplays_resolution` off the entry flagged `spdisplays_main`, because that is the point
  resolution the player window occupies and it needs no permission. The obvious
  `osascript -e 'tell application "Finder" to get bounds of window of desktop'` cannot be used:
  it needs an Automation grant the record pass does not hold under launchd, so it fails straight
  through to the fallback, and over SSH it hangs indefinitely rather than erroring. That silent
  fallback costs more now than it used to. A wrong screen size no longer merely mis-sizes the
  throwaway record window, it bakes the wrong aspect into every segment, which is how the XDR
  first re-recorded its whole loop at 1728x1080, the 1.6 of the 1440x900 fallback. The read is
  also given a timeout for the same reason, so a wedged display query can never hang a pass.
- `swift-sources/*.swift` compile to the 24/7 window: a native `AVQueuePlayer` behind an
  `AVPlayerLayer`, `videoGravity = .resizeAspect` so
  the loop is never cropped or zoomed. That only holds because the window is an
  `AmbientCanvasUnconstrainedScreensaverWindow`, an `NSWindow` subclass whose
  `constrainFrameRect` returns the proposed rect untouched. `workspace_grid_window_layout.lua`
  pins the window to `screen():fullFrame()`, but AppKit silently re-constrains a `.titled`
  window to the _visible_ frame about a second later, so on a 1920x1080 display the window
  settled at 1920x1050 and `.resizeAspect` fitted the 16:9 loop to 1866x1050, leaving a measured
  27px pillarbox on each side. With the clamp overridden the window is the full screen frame, and
  because the capture resolution is derived from that same screen the video decodes with no
  letterbox and no resampling; the menu bar simply draws over the top 30px. Reaching for
  `.resizeAspectFill` instead only hides the clamp, and it generalizes badly, cropping roughly
  13% of the width on a non-16:9 display, which is exactly the panel the derived capture
  resolution exists to serve.

  Playback order is randomized, which is why there is no `AVPlayerLooper` on the live path. Each
  composition is its own file under `segments/`, ordered by the `loop.segments.json` manifest,
  and the player enqueues them in a fresh shuffled permutation, reshuffling once every segment
  has been used and never repeating one across the seam. Transitions are queue advances rather
  than seeks: `actionAtItemEnd = .advance` with two items kept queued ahead, KVO on `currentItem`
  to refill and to re-arm the dwell, so the next segment is already prepared when the current one
  ends and the swap costs no black frame. A boundary observer is armed only when the playback
  dwell override is shorter than the segment, and it just calls `advanceToNextItem`.
  `AVPlayerLooper` remains for the degenerate single-composition playlist. Pause and resume route
  through the shuffle object rather than the player, so a queue advance landing while the
  visibility gate has paused cannot silently resume decode.

  Dwell is retunable without re-recording. `AMBIENT_CANVAS_ROTATION_SECONDS` in `panes.js` is
  the _recorded_ dwell and still costs a render to change, because it decides how many frames
  exist. On top of it, writing a number of seconds to
  `~/.local/state/ambient-canvas/playback-dwell-seconds` shortens every segment at playback
  time, read fresh at each segment start so it takes effect within one dwell and needs no
  restart. Echoing a number of seconds into that path retunes the rotation; deleting the file
  restores the recorded length. The nix module seeds the file with its default only when the
  file is absent, the same mutable-seed pattern the Claude settings use, so a value tuned live
  survives every rebuild and only a deletion falls back to the recorded dwell. The value is
  clamped to a floor in `ambient-canvas-playback-dwell-override.swift` and never rises above the
  recorded dwell.
  Raising that ceiling means raising the recorded dwell and paying one render, which also grows
  the segment files proportionally at roughly 1.6MB per recorded second.

  There is also a visibility-gated playback controller that pauses decode whenever the window is not on the
  active Space, is covered, or the display sleeps (it observes both window occlusion and
  `NSWorkspace.activeSpaceDidChangeNotification`). The window title
  is `ambient-canvas-gpu-screensaver` so the Hammerspoon pin to workspace 11 is unchanged; it is a
  titled window with a hidden transparent titlebar so the title stays readable via accessibility.
  `compile-player.sh` builds it with the system `/usr/bin/swiftc` during home-manager activation,
  stamped so it only recompiles when the sources change, mirroring the application-launcher daemon.

- `scripts/ambient_canvas_media/` holds the Python: `ambient_canvas_browser` (shared record browser
  and geometry resolution), `recorded_segment_store` (the whole on-disk layout: atomic segment
  writes, both manifest shapes, presence checks, pruning), `scene_source_digests` (the
  per-scene and pipeline digests the fingerprint is built from), `recorded_loop_upload_server`
  (stdlib HTTP receiver, and the only thing that answers the browser's fingerprint queries),
  `render_ambient_canvas_loop` (drives a throwaway Chrome record window),
  `display_ambient_canvas_loop` (spawns the native player binary detached), and
  `ensure_ambient_canvas_screensaver` (the launchd entry: regenerate if stale, then keep the
  window alive), plus `byte_range_request_handler` (HTTP Range support) and `scene_video_cache`
  (yt-dlp fetches for video-backed scenes). No external encoder is used, because the nixpkgs
  `ffmpeg` is AMFI-killed on the M-series host; the browser encodes the H.264 segments itself.

### bad-apple (video-backed scene)

`web/scenes/bad-apple/` brings the terminal `bad-apple` toy into the screensaver, and this is
the right home for it: the chafa pipeline paid a luminance-to-braille conversion per frame
forever, whereas here it is paid once at record time and the 24/7 window only decodes video.
The port needs neither `ffmpeg` nor `chafa`. Chrome decodes the source and
`braille_frame_renderer` rasterises the braille itself, so the AMFI-killed `ffmpeg` is never
invoked; `scene_video_cache` asks yt-dlp for a pre-muxed format 18, so no stream merge is
needed either. Sources are declared in `web/scene-videos.json`, cached under
`~/.local/state/ambient-canvas/videos/`, and served to the record browser at
`/ambient-canvas-videos/`.

Two things are load-bearing and easy to regress. The record server **must** answer HTTP Range
requests: `SimpleHTTPRequestHandler` does not, and without `206` responses Chrome reports the
video as `seekable: [[0, 0]]`, so every seek silently no-ops and every frame captures the
opening black frame. And the scene is deterministic only through `prepareFrame`, which seeks
to the exact frame time and resolves on `seeked`; the braille grid is derived from the measured
glyph advance width, so dots stay square and the source is letterboxed rather than stretched.

Source framing follows the clip. Four of the six declared clips are 640x360 and fill the 16:9
frame edge to edge; `FtutLA63Cp8` and `djV11Xbc914` are 480x360, so they letterbox to 75% of
the frame width. That is intrinsic to a 4:3 source and is left alone deliberately: cropping
them to 16:9 costs 12.5% off the top and bottom, which clips heads in roughly two of every
five sampled frames. Swap the clip rather than crop it.

### Refresh

The recorded loop lives in `~/.local/state/ambient-canvas/` as one file per composition under
`segments/`, ordered by `loop.segments.json`, next to `loop.source`, which records the `web/`
nix store path it was rendered from. `ensure_ambient_canvas_screensaver` compares that against
the current store path, so any change under `web/` changes the store path and the next launchd
tick starts a record pass automatically. Force one by hand with `ambient-canvas-render`.

That store-path check is deliberately coarse, and the record pass is what makes it cheap. A
segment file is named by a fingerprint over the composition's own JSON, its resolved duration,
the digests of the scene files it references, the shared record pipeline, and the capture
settings. The browser asks the server which fingerprints already exist and re-encodes only the
ones missing, so adding a scene pays that one composition's ~30s of encode and every other
segment is left on disk untouched. Editing one scene re-encodes the compositions that use it;
editing `player.js` or the encoder changes the pipeline digest and re-encodes everything. The
manifest is written only after every segment it names is present on disk, and segments the new
manifest no longer names are pruned, so the state directory never accumulates orphans and the
player never sees a half-written playlist.

Pass no length: each segment's length comes from the playlist. `--seconds N` remains a debug
override that shortens every composition to N seconds; it is folded into the fingerprint, so a
short debug pass never poisons the real segments.

`ambient-canvas/default.nix` packages the `ambient-canvas` launcher and the
`ambient-canvas-render` command and, guarded by `isDarwin`, compiles the native player from
`swift-sources/` via a `compileAmbientCanvasPlayer` activation and installs the
`com.dotfiles.ambient-canvas` launchd agent that runs the ensure entry every 30s.

## herdr terminal grid (Linux)

`scripts/launch_herdr_screensaver.py` creates a herdr workspace labelled `screensaver` and
splits it into one pane per available command: `equation-art` (wrapped in `precompute-loop`
for cheap record-once/replay-forever playback), a companion (`cbonsai` or `cmatrix`), and a
second `cmatrix`. It composes the general terminal toys (`cbonsai`, `cmatrix`, `bad-apple`)
that live in the terminal domain via `PATH`; only the launcher and the screensaver-specific
scenes (`equation-art`, `precompute-loop`) live here.

To add a pane: append a command to `resolve_available_screensaver_commands` and, if it is
expensive, add its executable name to `PRECOMPUTE_LOOP_WRAPPED_COMMAND_MARKERS` so it is
replayed cheaply.

## Wiring

`default.nix` imports `./ambient-canvas` and packages the herdr launcher and scenes. It is
imported by `home/darwin/default.nix` (for ambient-canvas) and `home/hosts/linux/chise.nix`
(for the herdr grid); each half is platform-gated internally, so importing the domain on the
wrong platform is inert. Tests live in `__tests__/` and are wired into the flake checks via
`__tests__/nix-checks/default.nix`.
