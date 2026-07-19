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
- Loop length is derived, never authored: `totalCycleSeconds` is the sum of every
  composition's `durationSeconds ?? AMBIENT_CANVAS_ROTATION_SECONDS`. Every composition is
  entered exactly once per loop, and the recorder self-derives the capture length from it.
- `web/player.js` owns the segment walk. `resolveSegment(elapsed)` is a pure function
  returning `{ index, localElapsedSeconds }`, shared by the live loop and the recorder so cut
  points are identical. Renderers are built and torn down per segment, so live GL contexts are
  bounded by panes-per-composition rather than playlist length; each scene is driven by
  `localElapsedSeconds`, so it restarts cleanly on entry.
- `web/scenes/*.js` each register a scene factory on
  `window.AMBIENT_CANVAS_SCENE_FACTORIES[name]`. A factory is
  `(canvasElement, options) => { render(localElapsedSeconds), resize(width, height) }`, plus
  three optional members: `dispose()` to release GPU resources at segment teardown, `ready`
  (a promise) for scenes with assets to load, and `prepareFrame(localElapsedSeconds)` (a
  promise) for scenes whose frame cannot be produced synchronously. The record loop awaits
  both, which is what makes a video-backed scene deterministic.

To add eye candy: write `web/scenes/<name>.js` registering the factory, add its `<script>` to
`index.html`, then append one composition to `AMBIENT_CANVAS_PLAYLIST`. Scenes that call
`Math.random` at build time reseed per recording pass, so the recorded loop is not
pixel-seamless; boundaries are cuts and the loop is long enough that the seam is unobtrusive.

### Record and play

- `web/recorder.js` activates only when `index.html` is opened with `?record`. It drives a
  deterministic frame-stepped render rather than a real-time capture: for each frame index it
  resolves the playlist segment, rebuilds renderers at segment boundaries, awaits each pane's
  `prepareFrame`, composites every pane canvas into one canvas (WebGL panes honor the injected
  `preserveDrawingBuffer` option), and encodes it with an explicit timestamp through
  `VideoEncoder` into the vendored `mp4-muxer`, then POSTs the clip to a local receiver. Because
  the synthetic clock is `frameIndex / fps` rather than wall time, the output is exact CFR at a
  fixed 1920x1080 no matter how slowly a frame renders. `MediaRecorder` was replaced because it
  is real-time-only and could not hold 30fps at full resolution. The codec is H.264 in MP4 so
  the M-series media engine decodes the loop in hardware.
- `swift-sources/*.swift` compile to the 24/7 window: a native `AVQueuePlayer` + `AVPlayerLooper`
  behind an `AVPlayerLayer` (seamless loop, no restart flash), `videoGravity = .resizeAspect` so
  the loop is never cropped or zoomed. That only holds because the window is an
  `AmbientCanvasUnconstrainedScreensaverWindow`, an `NSWindow` subclass whose
  `constrainFrameRect` returns the proposed rect untouched. `workspace_grid_window_layout.lua`
  pins the window to `screen():fullFrame()`, but AppKit silently re-constrains a `.titled`
  window to the _visible_ frame about a second later, so on a 1920x1080 display the window
  settled at 1920x1050 and `.resizeAspect` fitted the 16:9 loop to 1866x1050, leaving a measured
  27px pillarbox on each side. With the clamp overridden the window is the loop's exact
  resolution, so the video decodes 1:1 with no pillarbox and no resampling; the menu bar simply
  draws over the top 30px. Reaching for `.resizeAspectFill` instead only hides the clamp, and it
  generalizes badly, cropping roughly 13% of the width on a non-16:9 display.
  There is also a visibility-gated playback controller that pauses decode whenever the window is not on the
  active Space, is covered, or the display sleeps (it observes both window occlusion and
  `NSWorkspace.activeSpaceDidChangeNotification`). The window title
  is `ambient-canvas-gpu-screensaver` so the Hammerspoon pin to workspace 11 is unchanged; it is a
  titled window with a hidden transparent titlebar so the title stays readable via accessibility.
  `compile-player.sh` builds it with the system `/usr/bin/swiftc` during home-manager activation,
  stamped so it only recompiles when the sources change, mirroring the application-launcher daemon.
- `scripts/ambient_canvas_media/` holds the Python: `ambient_canvas_browser` (shared record browser
  and geometry resolution), `recorded_loop_upload_server` (stdlib HTTP receiver that writes
  `loop.<ext>` atomically), `render_ambient_canvas_loop` (drives a throwaway Chrome record
  window), `display_ambient_canvas_loop` (spawns the native player binary detached), and
  `ensure_ambient_canvas_screensaver` (the launchd entry: regenerate if stale, then keep the
  window alive), plus `byte_range_request_handler` (HTTP Range support) and `scene_video_cache`
  (yt-dlp fetches for video-backed scenes). No external encoder is used, because the nixpkgs
  `ffmpeg` is AMFI-killed on the M-series host; the browser encodes the H.264 loop itself.

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

The recorded loop lives in `~/.local/state/ambient-canvas/` next to `loop.source`, which
records the `web/` nix store path it was rendered from. `ensure_ambient_canvas_screensaver`
compares that against the current store path, so any change to a scene changes the store path
and the next launchd tick regenerates the loop automatically. Force a rebuild by hand with
`ambient-canvas-render`. Pass no length: the recorder derives it from the playlist so one full
cycle is always captured. `--seconds N` remains a debug override for a short clip, and passing
it means compositions past that point are not recorded at all.

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
wrong platform is inert. Tests live in `tests/` and are wired into the flake checks via
`tests/nix-checks/default.nix`.
