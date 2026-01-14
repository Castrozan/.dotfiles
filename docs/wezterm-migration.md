# WezTerm Migration Notes

## What Changed

- **Terminal**: Switched from `kitty` to `wezterm`
- **Config Format**: From `kitty.conf` (INI-like) to `wezterm.lua` (Lua)
- **Module**: `home/modules/kitty.nix` → `home/modules/wezterm.nix`
- **Config File**: `.config/kitty/` → `.config/wezterm/wezterm.lua`

## Ported Settings

All kitty settings have been ported to WezTerm:

- ✅ Font: Fira Code, size 16
- ✅ Theme: Catppuccin Mocha (colors ported)
- ✅ Wallpaper: Same wallpaper.png
- ✅ Window padding: 10px all sides
- ✅ Window decorations: Hidden
- ✅ Background opacity: 1.0
- ✅ Shell: fish
- ✅ Confirm before quit: Disabled

## New Features Enabled

- ✅ **Shift+Enter support**: Enabled CSI-u keyboard protocol for proper modifier key handling
- ✅ **Extended keys in tmux**: Enabled `extended-keys` with CSI-u format and passthrough
- ✅ **Better keyboard handling**: Applications can now distinguish Shift+Enter from Enter

## Non-NixOS OpenGL Fix

WezTerm requires OpenGL/EGL libraries which aren't available to Nix applications on non-NixOS.
The solution uses [nixGL](https://github.com/nix-community/nixGL) to wrap WezTerm:

- `nixGLIntel` provides Mesa OpenGL support (Intel/AMD GPUs)
- Previously required `--impure` flag (no longer needed - nixGL input is now a flake)
- Note: Changed from `nixGLDefault` to `nixGLIntel` to avoid ~3s IFD overhead
  (nixGLDefault does impure nvidia detection that rebuilds every evaluation)

## Files Updated

1. `home/modules/wezterm.nix` - WezTerm module with nixGL wrapper for OpenGL support
2. `.config/wezterm/wezterm.lua` - WezTerm configuration
3. `users/lucas.zanoni/home.nix` - Switched from kitty to wezterm module
4. `.config/tmux/settings.conf` - Added extended-keys support for WezTerm
5. `.config/fuzzel/fuzzel.ini` - Updated terminal from kitty to wezterm
6. `.config/xdg-terminals.list` - Updated default terminal
7. `flake.nix` - Added nixGL input for OpenGL support on non-NixOS
8. `bin/rebuild` - Previously added `--impure` flag (no longer needed)

## Shift+Enter Fix

### Problem
Shift+Enter was not working properly - it would submit prompts instead of adding newlines in applications like opencode.

### Solution
Enabled CSI-u (fixterms/kitty) keyboard protocol in WezTerm and configured explicit key bindings:

1. **WezTerm Configuration** (`.config/wezterm/wezterm.lua`):
   - `enable_csi_u_key_encoding = true` - Enables CSI-u protocol
   - Key bindings send proper escape sequences:
     - Shift+Enter → `\x1b[13;2u`
     - Ctrl+Enter → `\x1b[13;5u`
     - Alt+Enter → `\x1b[13;3u`

2. **Tmux Configuration** (`.config/tmux/settings.conf`):
   - `extended-keys on` - Enable extended key support
   - `extended-keys-format csi-u` - Use CSI-u format
   - `allow-passthrough on` - Allow sequences to pass through to applications

### Testing

After rebuilding and restarting WezTerm:

1. **Test outside tmux**:
   ```bash
   cat -v
   # Press Shift+Enter - should show: ^[[13;2u
   ```

2. **Test inside tmux** (reload config first):
   ```bash
   tmux source-file ~/.config/tmux/tmux.conf
   cat -v
   # Press Shift+Enter - should show: ^[[13;2u
   ```

3. **Test in OpenCode**:
   - Type some text, press Shift+Enter
   - Should add a newline (not submit)
   - Ctrl+J also works as fallback

4. **Verify appearance**:
   - Font should be Fira Code
   - Colors should match Catppuccin Mocha
   - Wallpaper should be visible
   - Window should have no decorations
   - Tab bar hidden when only one tab

## Rollback

If you need to rollback to kitty:

1. In `users/lucas.zanoni/home.nix`, change:
   ```nix
   ../../home/modules/wezterm.nix
   ```
   back to:
   ```nix
   ../../home/modules/kitty.nix
   ```

2. Revert `.config/fuzzel/fuzzel.ini` and `.config/xdg-terminals.list`

3. Rebuild: `./bin/rebuild`
