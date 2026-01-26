# Super Key Alone - GNOME-like Launcher Behavior

## Problem Statement

We want GNOME-like Super key behavior in Hyprland:
- **Super alone** (tap and release) → opens fuzzel launcher
- **Super+X combos** (Super+Tab, Super+Return, etc.) → execute their actions, NOT fuzzel

## The Fundamental Challenge

Hyprland's `bindr = SUPER, Super_L` binding fires on Super key **release**, regardless of what keys were pressed while Super was held. This means:

1. Press Super
2. Press Tab (Super+Tab triggers window switcher)
3. Release Tab
4. Release Super → **fuzzel opens anyway** (unwanted!)

## Approaches Tried

### 1. Polling Approach (Original)
```bash
# Poll for 240ms to detect hyprshell or window change
for _ in 1 2 3 4 5 6 7 8; do
    sleep 0.03
    hyprctl layers -j | grep -q "hyprshell" && exit 0
    window_now=$(hyprctl activewindow -j | jq -r '.address')
    [[ "$window_before" != "$window_now" ]] && exit 0
done
```

**Problems:**
- Race condition with quick Super+Tab sequences
- Only handles Super+Tab, not all Super+X combos
- Adds latency to Super-alone case
- Hyprshell (GTK4) doesn't register as a layer, so layer check fails

### 2. Submap Approach
```
bind = SUPER, Super_L, submap, super_held
submap = super_held
bind = , Tab, exec, hyprshell toggle windowSwitcher
bind = , Tab, submap, reset
bindr = , Super_L, exec, omarchy-fuzzel
bindr = , Super_L, submap, reset
bind = , catchall, submap, reset
submap = reset
```

**Problem:** `bind = SUPER, Super_L` on key **press** doesn't fire reliably. Only the release binding works.

### 3. Flag File Approach
```bash
# In Hyprland config:
bindnd = SUPER, TAB, exec, touch /tmp/.super_combo_used

# In super-launcher:
if [[ -f /tmp/.super_combo_used ]]; then
    rm -f /tmp/.super_combo_used
    exit 0
fi
```

**Problems:**
- Requires modifying ALL Super+X bindings
- Race conditions between flag creation and checking
- Hyprshell plugin intercepts Super+Tab at XKB level, bypassing our binding

### 4. Interception-tools + dual-function-keys (Current Attempt)

This approach intercepts at the **input layer** (before Wayland):
```nix
services.interception-tools = {
  enable = true;
  plugins = [ pkgs.interception-tools-plugins.dual-function-keys ];
};

# Config: Super tap sends F13, Super hold acts as modifier
MAPPINGS:
  - KEY: KEY_LEFTMETA
    TAP: KEY_PROG1  # or KEY_F13
    HOLD: KEY_LEFTMETA
```

Then bind in Hyprland:
```
bindd = , XF86Launch1, exec, omarchy-super-launcher
```

**Problem:** The synthetic keys from `uinput` virtual device **don't reach Hyprland/Wayland**. This appears to be a fundamental limitation of how Wayland compositors handle virtual input devices from interception-tools.

Tested keys that don't work:
- KEY_F13
- KEY_PROG1 (XF86Launch1)
- KEY_F20

## Why This Is Hard

1. **Wayland isolation**: Unlike X11, Wayland compositors have strict input handling. Virtual devices from interception-tools may not be trusted for certain key events.

2. **Hyprland binding limitations**: The `bindr` (release) binding doesn't know what happened during the key hold.

3. **Plugin priority**: Hyprshell's plugin intercepts Super+Tab at XKB level, before our bindings.

4. **No press binding**: `bind = SUPER, Super_L` on press doesn't work for entering submaps.

## Potential Solutions (Not Yet Tried)

### 1. Use ydotool
Install `ydotool` and `ydotoold` service. Configure dual-function-keys to somehow trigger ydotool (may need wrapper script via a different interception tool).

### 2. Use Super+Space Instead
The cleanest solution - just use `Super+Space` for the launcher like GNOME's default. Avoids all conflicts:
```
bindd = SUPER, Space, exec, omarchy-super-launcher
```

### 3. Keyd or Kanata
Try alternative key remapping tools that might have better Wayland support.

### 4. Hyprland Plugin
Write a custom Hyprland plugin that properly tracks modifier-only key presses.

### 5. Accept Imperfection
Use the polling approach with longer timeout (500ms), accepting:
- Slight delay for Super-alone
- Occasional false trigger on very quick combos

## References

- [Hyprland Discussion #2506 - Bind Super key alone](https://github.com/hyprwm/Hyprland/discussions/2506)
- [dual-function-keys nix-config example](https://github.com/donovanglover/nix-config/commit/49a621f081191497494b57c8c5a92c68fea2e845)
- [Hyprland Issue #6946 - Super alone no longer works](https://github.com/hyprwm/Hyprland/issues/6946)

## Current Status

**Blocked** - The interception-tools approach doesn't work because synthetic keys don't reach Wayland. Need to either:
1. Find a way to make virtual input work with Hyprland
2. Use a different approach entirely
3. Accept using Super+Space instead
