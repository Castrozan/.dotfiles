# Screensaver

Ambient eye-candy for an idle desktop. This domain owns both implementations of the
screensaver concern, one per platform, because each platform has a different renderer
whose cost profile forced a different choice.

| Platform | Implementation | Renderer | Trigger |
| --- | --- | --- | --- |
| darwin | `ambient-canvas/` (Chrome WebGL) | GPU, isolated Chrome process | `com.dotfiles.ambient-canvas` launchd keep-alive, pinned to Hammerspoon workspace 11 |
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
- Chrome `ambient-canvas`: ~52% CPU and ~862MB RSS in its own 7-process Chrome tree, GPU
  rendered, with zero wezterm impact. Higher raw numbers, but isolated from the terminal.

On darwin the isolation wins, so `ambient-canvas` is the darwin screensaver and the herdr
grid is gated to Linux.

## ambient-canvas (darwin GPU)

`ambient-canvas/web/index.html` loads a full-window WebGL canvas grid. Layout and panes are
declared data, one line per pane:

- `web/panes.js` declares `AMBIENT_CANVAS_LAYOUT` (a CSS `grid-template-areas` spec) and
  `AMBIENT_CANVAS_PANES` (each `{ area, scene }`).
- `web/player.js` builds the grid, instantiates one scene per pane, and drives their render
  loop.
- `web/scenes/*.js` each register a scene factory on
  `window.AMBIENT_CANVAS_SCENE_FACTORIES[name]`. A factory is
  `(canvasElement, options) => { render(elapsedSeconds), resize(width, height) }`.

To add a pane: write `web/scenes/<name>.js` registering the factory, add its `<script>` to
`index.html`, then add one `{ area, scene }` entry to `AMBIENT_CANVAS_PANES` and its area to
the layout grid.

`ambient-canvas/default.nix` packages the `ambient-canvas` launcher and, guarded by
`isDarwin`, installs the `com.dotfiles.ambient-canvas` launchd agent that relaunches the
window every 30s if it is not running. Hammerspoon pins the window (title prefix
`ambient-canvas-gpu-screensaver`) to workspace 11.

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
