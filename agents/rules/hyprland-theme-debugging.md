---
description: Debugging Hyprland theme switching, Wayland crashes, and service coordination
alwaysApply: false
globs:
  - "bin/omarchy/*theme*"
  - "bin/omarchy/*restart*"
  - "bin/omarchy/monitor-*"
  - "home/modules/hyprland/*.nix"
  - ".config/hypr/**/*"
---
<!-- @agent-architect owns this file. Delegate changes, don't edit directly. -->

# Hyprland Theme Switching & Wayland Debugging

Knowledge gained from debugging theme switching crashes, window loss, and service coordination issues.

## Symptoms and Root Causes

### Windows/Applications Disappearing During Theme Change

**Symptoms:** Browser, terminal, or other windows close unexpectedly when changing themes.

**Investigation steps:**
1. Check Hyprland logs: `tail -100 /run/user/$(id -u)/hypr/*/hyprland.log`
2. Look for repeated modesetting: `drm: Modesetting`, `drm: Disabling output`
3. Check for DRM errors: `ERR from aquamarine: drm: Cannot commit when a page-flip is awaiting`

**Common causes:**
- Multiple instances of background daemon (swaybg) causing DRM conflicts
- Monitor-switch daemon repeatedly applying same config
- Service restarts breaking Wayland connections

### Repeated Modesetting / Monitor Flashing

**Root cause:** Something is triggering `hyprctl keyword monitor` commands repeatedly.

**Check monitor-switch daemon:**
```bash
pgrep -af monitor-switch
```

**Problem pattern:** Daemon applies config on every event without checking current state:
```bash
# BAD: Always runs hyprctl even if already in desired state
apply_config() {
  if is_monitor_connected "$EXTERNAL"; then
    hyprctl keyword monitor "$INTERNAL,disable"
  fi
}
```

**Fix:** Check state before applying:
```bash
# GOOD: Only act when state differs
apply_config() {
  if is_monitor_connected "$EXTERNAL"; then
    if ! is_monitor_disabled "$INTERNAL"; then
      hyprctl keyword monitor "$INTERNAL,disable"
    fi
  fi
}
```

### Multiple swaybg Instances

**Check:** `pgrep -a swaybg` - should show only 1 process.

**Problem:** `pkill -x swaybg` may not kill processes fast enough before new one starts.

**Fix:** Use SIGKILL and add delay:
```bash
pkill -9 swaybg 2>/dev/null || true
sleep 0.3
setsid swaybg -i "$BACKGROUND" -m fill &
```

### Service Crashes with "Broken pipe" or "Error flushing display"

**Cause:** Wayland connection lost during restart, often due to DRM conflicts from other issues.

**Pattern to avoid:** Don't restart Wayland services during theme changes if they have file watchers.

**Check for file watchers:**
```bash
journalctl --user -u hyprshell | grep -i "reload listener"
# Shows: "Starting hyprshell css reload listener"
```

If service has CSS reload listener, skip restart - it auto-reloads.

## Debugging Commands

### Check Running Services
```bash
systemctl --user status waybar swaync hyprshell swayosd hypridle
```

### Watch Hyprland Events
```bash
nc -U "$XDG_RUNTIME_DIR/hypr/$HYPRLAND_INSTANCE_SIGNATURE/.socket2.sock"
```

### Check for Process Accumulation
```bash
pgrep -c swaybg    # Should be 1
pgrep -c waybar    # Should be 1
pgrep -af monitor-switch
```

### Check DRM/Display Errors
```bash
tail -100 /run/user/$(id -u)/hypr/*/hyprland.log | grep -E "ERR|Modesetting|Disabling"
```

### Check Service Logs
```bash
journalctl --user -u SERVICE --since "5 minutes ago" --no-pager
```

## Anti-Patterns to Avoid

### 1. Restarting Services That Have File Watchers
```bash
# BAD: Causes crashes, unnecessary
systemctl --user restart hyprshell

# GOOD: Let CSS reload listener handle it
# (just update the CSS file, service watches it)
```

### 2. Using Regular Signals to Kill Background Daemons
```bash
# BAD: May not kill fast enough, causes accumulation
pkill -x swaybg
swaybg -i "$BG" &

# GOOD: SIGKILL + delay ensures clean state
pkill -9 swaybg 2>/dev/null || true
sleep 0.3
swaybg -i "$BG" &
```

### 3. Applying Monitor Config Without State Check
```bash
# BAD: Triggers modesetting even when unnecessary
hyprctl keyword monitor "eDP-1,disable"

# GOOD: Check first
if ! is_monitor_disabled "eDP-1"; then
  hyprctl keyword monitor "eDP-1,disable"
fi
```

### 4. Using SIGUSR2 for Waybar with @import CSS
```bash
# BAD: SIGUSR2 reload doesn't re-fetch @imported files
pkill -USR2 waybar

# GOOD: Full restart re-parses everything
systemctl --user restart waybar
```

### 5. Nix-Managed Files and Touch/Modify
```bash
# BAD: Nix store files are read-only
touch ~/.config/waybar/style.css  # Permission denied

# Files are symlinks to /nix/store/...
# Can't modify to trigger inotify watchers
```

## Service Coordination Patterns

### Safe Theme Change Sequence
1. Update theme files (templates → current/theme/)
2. Update background (kill old swaybg with -9, delay, start new)
3. Apply Hyprland colors via `hyprctl keyword` (safe, no reload)
4. Restart waybar (needed for @import CSS)
5. Reload swaync CSS via `swaync-client -rs` (no restart needed)
6. Let hyprshell auto-reload via file watcher
7. Update GNOME settings (gsettings)

### Component Reload Methods
| Component | Method | Command |
|-----------|--------|---------|
| Waybar | Restart service | `systemctl --user restart waybar` |
| SwayNC | Client reload | `swaync-client -rs` |
| Hyprshell | File watcher | Auto-reloads CSS |
| SwayOSD | No reload | Needs service restart (risky) |
| Hyprland | Keyword | `hyprctl keyword general:col.active_border` |
| swaybg | Replace process | `pkill -9 swaybg && swaybg ...` |

### systemd Service Dependencies
```nix
# Services should NOT use PartOf=graphical-session.target
# It causes them to stop during home-manager reload

# GOOD pattern:
Unit = {
  After = [ "graphical-session.target" ];
  ConditionEnvironment = "WAYLAND_DISPLAY";
};
# No PartOf, no WantedBy graphical-session.target in Unit section
```

### Startup Wait Scripts
Some services crash if started before Hyprland IPC is ready:
```bash
# Wait for Hyprland to be ready
for i in $(seq 1 30); do
  if hyprctl monitors &>/dev/null; then
    break
  fi
  sleep 0.2
done
exec service-binary
```

## Lessons Learned

1. **Stale HYPRLAND_INSTANCE_SIGNATURE after crash/logout** - If hyprctl commands fail with "Couldn't connect to socket", check if there are multiple Hyprland instances:
   ```bash
   ls /run/user/$(id -u)/hypr/
   ```
   If multiple exist, terminal has stale env var. Fix: restart terminal or update var manually.

2. **Multiple daemon instances cause DRM conflicts** - Always verify single instance with `pgrep -c`

2. **SIGUSR2 doesn't re-fetch CSS @imports** - Waybar needs full restart for theme changes

3. **Monitor-switch daemons can cause feedback loops** - Must check state before applying

4. **Wayland services with file watchers don't need restart** - Check logs for "reload listener"

5. **pkill timing is unreliable** - Use SIGKILL (-9) + sleep for clean replacement

6. **Nix-managed configs are immutable** - Can't use touch/inotify tricks on symlinked files

7. **PartOf= in systemd causes reload issues** - Services stop when target reloads

8. **hyprctl keyword is safer than hyprctl reload** - Keyword changes specific values, reload can cause disruption

9. **nixpkgs hyprshot bundles old hyprland** - Override with flake version:
   ```nix
   hyprshot-fixed = pkgs.hyprshot.override {
     hyprland = inputs.hyprland.packages.${pkgs.system}.hyprland;
   };
   ```
