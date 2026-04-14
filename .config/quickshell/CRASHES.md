# Quickshell Crash Tracking

Ongoing log of segfaults observed in the quickshell runtime, current mitigations, and how to keep an eye on them.

## Symptom

Random segfaults inside `libQt6Quick.so.6.10.x` while the bar is running. The in-process crash handler catches the fault, writes a minidump under `~/.cache/quickshell/crashes/`, and relaunches the shell automatically. Systemd (`quickshell-bar`, `quickshell-overview`, `quickshell-switcher`) also has `Restart=always` as a secondary safety net.

Kernel log signature:
```
.quickshell-wra[PID]: segfault at 0x1b8/0x200/... ip ... in libQt6Quick.so.6.10.x
```
Small fault addresses indicate a null or freed pointer plus a field offset, which matches the nullptr-guard patches that have been landing upstream since v0.2.1.

## Root cause

Upstream `quickshell` tag `v0.2.1` (2025-10-11) plus `Qt 6.10.x` exhibits use-after-free and nullptr deref in the scene-graph layer. No newer tagged release exists as of 2026-04-13; the fixes live on the `master` branch.

Relevant post-v0.2.1 commits:
- `d4c9297` i3/ipc: null monitor/workspace pointers on destroy
- `ad5fd91` wm: nullptr guard in `WindowManager::screenProjection`
- `7208f68` / `f0d0216b` `QS_DROP_EXPENSIVE_FONTS` pragma + env workaround for font-related crashes
- `9bf752a` add `std::terminate` handler
- `eb6eaf5` mutex around `stdoutStream`

## Current mitigations

1. **Flake input pinned to upstream master**: `flake.nix` has `quickshell.url = "git+https://git.outfoxxed.me/quickshell/quickshell?ref=master"` and all three service modules consume `inputs.quickshell.packages.${system}.quickshell` instead of `pkgs.quickshell`. Bump with:
   ```sh
   nix flake update quickshell
   rebuild
   ```
2. **`QS_DROP_EXPENSIVE_FONTS=1`** in the systemd Environment of every quickshell service. This is upstream's own workaround for font-related scene-graph crashes.
3. **`Restart=always`, `RestartSec=1s`** on all three services so tmux / Hyprland does not notice a user-visible gap when the in-process restarter fails.

## Monitoring

Check for new crashes:
```sh
ls -lat ~/.cache/quickshell/crashes | head
journalctl --since "2 days ago" | grep -E "Quickshell has crashed|segfault.*quickshell"
```

Inspect a specific crash:
```sh
cat ~/.cache/quickshell/crashes/<run-id>/info.txt     # build + runtime metadata
file ~/.cache/quickshell/crashes/<run-id>/minidump.dmp # needs minidump_stackwalk to decode
```

Running service state:
```sh
systemctl --user status quickshell-bar quickshell-overview quickshell-switcher
```

## Incident log

Append to the top when a new crash cluster shows up. Keep entries terse.

### 2026-04-13 - baseline before master pin
- 13 crashes in `~/.cache/quickshell/crashes/` going back to 2026-03-05, all on `tag-v0.2.1`.
- Three crashes on 2026-04-13 alone (12:05, 15:48, 16:23), hours apart, not tied to rebuilds.
- Action: switched flake input from `pkgs.quickshell` to upstream master, added `QS_DROP_EXPENSIVE_FONTS=1`. Expect the next entries to indicate whether crash frequency drops.

## Escalation

If crashes persist after pinning master and a `nix flake update quickshell`:
1. Decode the minidump with `minidump_stackwalk` to see which QML object triggered it.
2. File upstream at https://git.outfoxxed.me/quickshell/quickshell/issues with the stack trace and the QML path.
3. If a specific module is implicated, disable that module in `.config/quickshell/bar/Bar.qml` to confirm, then report.
