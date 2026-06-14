# WezTerm window-teardown stress (manual, darwin-only)

Reproduces the path of the macOS segfault where Cmd-W (close window) crashed
`wezterm-gui` inside an Objective-C autorelease-pool drain on a worker thread
exiting. Launches an isolated GUI instance (its own `--class`, own socket, off
the user's session), proves which GPU backend is active, then drives many window
open/close cycles asserting the process never segfaults.

Not wired into `tests/run.sh` or `checks.nix`: it needs a live macOS window
server and opens real windows, so it cannot run in the Linux CI sandbox. The
headless regression guard that the config stays on WebGpu lives in
`../checks.nix` (`domain-terminal-wezterm-webgpu-front-end`).

## Run

```
cd home/base/terminal/tests/e2e
python3 wezterm_window_teardown_stress.py --both --cycles 200
```

- `--front-end WebGpu|OpenGL` runs one backend; `--both` runs OpenGL (control)
  then WebGpu.
- Backend proof is deterministic: the OpenGL front_end loads the
  `AppleMetalOpenGLRenderer` shim (the component in the crash report's image
  list); WebGpu loads zero handles of it.
- The stress loop is robustness evidence, not proof the original race is gone:
  the real crash needed days of uptime, so rapid cycling does not reproduce it
  on either backend. Windows flash at the screen corner while it runs.
