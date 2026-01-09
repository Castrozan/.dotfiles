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

- ✅ **Shift+Enter support**: WezTerm natively supports CSI-u keyboard protocol
- ✅ **Extended keys in tmux**: Enabled `extended-keys` and `wezterm*:extkeys` in tmux config
- ✅ **Better keyboard handling**: No more "unknown key" errors

## Files Updated

1. `home/modules/wezterm.nix` - New WezTerm module
2. `.config/wezterm/wezterm.lua` - WezTerm configuration
3. `users/lucas.zanoni/home.nix` - Switched from kitty to wezterm module
4. `.config/tmux/settings.conf` - Added extended-keys support for WezTerm
5. `.config/fuzzel/fuzzel.ini` - Updated terminal from kitty to wezterm
6. `.config/xdg-terminals.list` - Updated default terminal

## Testing

After rebuilding:

1. **Test Shift+Enter in tmux**:
   ```bash
   tmux show-key -m
   # Press Shift+Enter - should show proper sequence
   ```

2. **Test in OpenCode**:
   - Shift+Enter should now work for multi-line input
   - No more "unknown key" errors

3. **Verify appearance**:
   - Font should be Fira Code
   - Colors should match Catppuccin Mocha
   - Wallpaper should be visible
   - Window should have no decorations

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
