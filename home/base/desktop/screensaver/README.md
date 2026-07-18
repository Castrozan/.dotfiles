# Screensaver

Ambient eye-candy for an idle desktop. This domain owns both implementations of the
screensaver concern, one per platform, because each platform has a different renderer
whose cost profile forced a different choice.

| Platform | Implementation | Renderer | Trigger |
| --- | --- | --- | --- |
| darwin | `ambient-canvas/` (WebGL scenes pre-recorded to a looping video) | HTML5 `<video>` hardware-decoded in a Chrome app window | `com.dotfiles.ambient-canvas` launchd keep-alive, pinned to Hammerspoon workspace 11 |
| Linux | herdr terminal grid (`scripts/launch_herdr_screensaver.py`) | wezterm cell repaint | manual: the `h` alias runs `herdr-screensaver` |

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
short looping video and the 24/7 window just plays that video, hardware-decoded, so the live
per-frame compute disappears. On darwin the isolation still wins over the herdr grid, so
`ambient-canvas` is the darwin screensaver and the herdr grid is gated to Linux.

## ambient-canvas (darwin)

The animation is authored as live WebGL/canvas scenes; those scenes are the source of truth.
A build step records them once into a looping video, and the 24/7 window plays that video.

### Scenes (authoring surface)

`ambient-canvas/web/index.html` loads a full-window canvas grid. Layout and panes are declared
data, one line per pane:

- `web/panes.js` declares `AMBIENT_CANVAS_LAYOUT` (a CSS `grid-template-areas` spec) and
  `AMBIENT_CANVAS_PANES` (each `{ area, scene }`).
- `web/player.js` builds the grid, instantiates one scene per pane, and drives their render
  loop. After each frame it calls `window.AMBIENT_CANVAS_FRAME_OBSERVER` if present, and it
  merges `window.AMBIENT_CANVAS_RENDERER_OPTION_OVERRIDES` into every scene's options.
- `web/scenes/*.js` each register a scene factory on
  `window.AMBIENT_CANVAS_SCENE_FACTORIES[name]`. A factory is
  `(canvasElement, options) => { render(elapsedSeconds), resize(width, height) }`.

To add a pane: write `web/scenes/<name>.js` registering the factory, add its `<script>` to
`index.html`, then add one `{ area, scene }` entry to `AMBIENT_CANVAS_PANES` and its area to
the layout grid. The scenes use `Math.random`, so the recorded loop is not pixel-seamless;
the loop is long enough that the seam is unobtrusive.

### Record and play

- `web/recorder.js` activates only when `index.html` is opened with `?record`. It composites
  every pane canvas into one canvas per frame (WebGL panes honor the injected
  `preserveDrawingBuffer` option), runs a `MediaRecorder`, and POSTs the encoded clip to a
  local receiver. It prefers an H.264 MP4 container so the M-series media engine can decode
  the loop in hardware.
- `web/player-video.html` is the 24/7 window: a single `<video>` that plays the recorded loop
  and restarts itself on `ended` (JS-driven, not the `loop` attribute, so container quirks
  can't break looping). Its title stays `ambient-canvas-gpu-screensaver` so the Hammerspoon
  pin to workspace 11 is unchanged.
- `scripts/ambient_canvas_media/` holds the Python: `ambient_canvas_browser` (shared browser
  and geometry resolution), `recorded_loop_upload_server` (stdlib HTTP receiver that writes
  `loop.<ext>` atomically), `render_ambient_canvas_loop` (drives a throwaway Chrome record
  window), `display_ambient_canvas_loop` (launches the video window), and
  `ensure_ambient_canvas_screensaver` (the launchd entry: regenerate if stale, then keep the
  window alive). No external encoder is used, because the nixpkgs `ffmpeg` is AMFI-killed on
  the M-series host.

### Refresh

The recorded loop lives in `~/.local/state/ambient-canvas/` next to `loop.source`, which
records the `web/` nix store path it was rendered from. `ensure_ambient_canvas_screensaver`
compares that against the current store path, so any change to a scene changes the store path
and the next launchd tick regenerates the loop automatically. Force a rebuild by hand with
`ambient-canvas-render` (optionally `--seconds N`).

`ambient-canvas/default.nix` packages the `ambient-canvas` launcher and the
`ambient-canvas-render` command and, guarded by `isDarwin`, installs the
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
