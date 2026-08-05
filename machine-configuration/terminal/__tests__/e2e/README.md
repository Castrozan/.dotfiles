# WezTerm window-teardown stress (manual, darwin-only)

Reproduces the path of the macOS segfault where Cmd-W (close window) crashed
`wezterm-gui` inside an Objective-C autorelease-pool drain on a worker thread
exiting. Launches an isolated GUI instance (its own `--class`, own socket, off
the user's session), proves which GPU backend is active, then drives many window
open/close cycles asserting the process never segfaults.

Not wired into `repository/verification/run.sh` or `checks.nix`: it needs a live macOS window
server and opens real windows, so it cannot run in the Linux CI sandbox. The
headless regression guard that the config stays on WebGpu lives in
`../checks.nix` (`domain-terminal-wezterm-webgpu-front-end`).

## Run

```
cd machine-configuration/terminal/emulators/wezterm/__tests__/e2e
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

# herdr tab startup benchmark (manual, needs a live herdr server)

Decomposes the wall time from `herdr tab create` until the new pane's bash is
writable into client, server, shell-spawn, shell-exec, and prompt-render
phases. The writable phase is measured in-band (the shell prints its own
`date +%s%N` when it executes the first queued command), so client polling
latency does not pollute it. Server phases come from the append-only
`~/.config/herdr/herdr-server.log`, matched by tab id.

Non-invasive: creates its own `perf-bench-*` tabs, always closes them, never
focuses a window by default, and touches no config, environment, or profile.
Skips cleanly when no herdr server is running, so it is safe on any host.

Not wired into `repository/verification/run.sh` or `checks.nix`: it needs a live herdr
server and real pane spawns. The unit-level guard for the same latency lives
in `machine-configuration/terminal/shell/bash/__tests__/unit/test_bash_login_pty_startup_latency.py`.

```
cd machine-configuration/terminal/workspace-manager/herdr/__tests__/e2e
python3 herdr_tab_startup_benchmark.py --runs 12
```

- `--runs N` iterations; `--focus` creates the tab focused (defaults to
  backgrounded); `--warm` splits into an existing tab instead of a new one.
- The measured findings that drove `machine-configuration/terminal/shell/bash/bash-home-manager.nix`: flyline's
  inline viewport issues a cursor position query (DSR) that herdr's emulator
  answers only ~190ms late, and flyline v1.3.0's startup PATH cache scan held
  a lock that blocked the first prompt by ~0.4s more. The v1.4.0 upgrade moved
  the scan off the critical path; the unit guard lives in
  `machine-configuration/terminal/shell/bash/__tests__/unit/test_bash_login_pty_startup_latency.py`.

