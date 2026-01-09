# Terminal + Multiplexer Alternatives

## Current Setup Analysis

**Kitty Usage**: Minimal - only basic features:
- Font (Fira Code), theme (Catppuccin-Mocha), wallpaper
- Window decorations, padding, startup session
- No advanced kitty features used

**Tmux Usage**: Heavy - core workflow:
- Sessions (screensaver, main), panes, windows
- Plugins: resurrect, yank, cpu, catppuccin
- Custom keybinds, auto-attach via fish
- Screensaver session management

**Problem**: Shift+Enter doesn't work in kitty+tmux due to CSI-u protocol incompatibility.

---

## Alternatives (Ordered by Closeness to Current Setup)

### 1. **WezTerm + Tmux** ⭐ Closest Match
**Why**: Terminal emulator with built-in multiplexer, but can still use tmux inside.

**Pros**:
- Modern Rust-based terminal (2024 active development)
- Built-in tabs/panes (can replace tmux if desired)
- Full CSI-u keyboard protocol support
- Can run tmux inside for full compatibility
- Excellent font rendering, GPU acceleration
- Cross-platform (Linux, macOS, Windows)
- Lua-based configuration (more powerful than kitty)

**Cons**:
- Different config format (Lua instead of kitty.conf)
- Built-in multiplexer is simpler than tmux (if you switch)
- Less mature ecosystem than tmux

**Migration Effort**: Low-Medium
- Keep tmux, just swap terminal emulator
- WezTerm config in Lua (different but similar concepts)
- Your tmux setup stays identical

**Shift+Enter Support**: ✅ Yes - WezTerm supports CSI-u and works with tmux extended-keys

**References**:
- [WezTerm](https://wezfurlong.org/wezterm/)
- [WezTerm + tmux](https://wezfurlong.org/wezterm/config/lua/config/term.html)

---

### 2. **Alacritty + Tmux** ⭐ Very Close
**Why**: Minimal terminal emulator, tmux-compatible, actively maintained.

**Pros**:
- Minimal, fast, GPU-accelerated
- Good extended keys support
- Works well with tmux
- Simple config (YAML/TOML)
- Active development (2024)

**Cons**:
- Very minimal features (no built-in tabs/panes)
- Less customization than kitty/wezterm
- No wallpaper support (but you can use compositor)

**Migration Effort**: Low
- Keep tmux exactly as-is
- Simple terminal swap
- Config is straightforward

**Shift+Enter Support**: ✅ Yes - Alacritty supports extended keys, works with tmux

**References**:
- [Alacritty](https://alacritty.org/)
- [Alacritty + tmux extended keys](https://github.com/alacritty/alacritty/issues/2233)

---

### 3. **Foot + Tmux** ⭐ Wayland Native
**Why**: Fast Wayland terminal, tmux-compatible, minimal overhead.

**Pros**:
- Wayland-native (if you're on Wayland/Hyprland)
- Very fast, minimal resource usage
- Good extended keys support
- Simple config
- Active development

**Cons**:
- Wayland-only (no X11)
- Less features than kitty/wezterm
- Smaller community

**Migration Effort**: Low
- Keep tmux as-is
- Simple terminal swap
- Works if you're on Wayland

**Shift+Enter Support**: ✅ Yes - Foot supports extended keys

**References**:
- [Foot](https://codeberg.org/dnkl/foot)

---

### 4. **Zellij** ⭐ Modern Tmux Alternative
**Why**: Rust-based tmux alternative with better keyboard protocol support.

**Pros**:
- Modern tmux replacement (Rust, 2024 active)
- Built-in layout system (no plugins needed)
- Better keyboard protocol support
- Session persistence built-in
- Plugin system (Rust-based)
- Works with any terminal emulator

**Cons**:
- Different workflow than tmux (learning curve)
- Plugin ecosystem smaller than tmux
- Need to migrate all keybinds/configs
- No direct tmux compatibility

**Migration Effort**: High
- Complete rewrite of multiplexer config
- Different keybind system
- Need to port screensaver setup
- Plugin migration (resurrect → built-in, yank → built-in)

**Shift+Enter Support**: ✅ Yes - Native support, no protocol issues

**References**:
- [Zellij](https://zellij.dev/)
- [Zellij vs tmux](https://zellij.dev/documentation/comparison-to-other-tools.html)

---

### 5. **WezTerm Built-in Multiplexer** ⭐ Bleeding Edge
**Why**: Use WezTerm's native multiplexer instead of tmux.

**Pros**:
- No external multiplexer needed
- Full CSI-u support (Shift+Enter works)
- Integrated tabs/panes/windows
- Lua-based config (very powerful)
- Session persistence
- Modern, actively developed

**Cons**:
- Different from tmux workflow
- Need to migrate all configs
- Smaller ecosystem than tmux
- No plugin compatibility

**Migration Effort**: High
- Complete multiplexer migration
- Rewrite screensaver setup
- Port all keybinds
- Learn new workflow

**Shift+Enter Support**: ✅ Yes - Native support

**References**:
- [WezTerm multiplexer](https://wezfurlong.org/wezterm/multiplexing.html)

---

### 6. **Warp Terminal** ⭐ AI-Powered (Future)
**Why**: Modern terminal with AI features, built-in multiplexer.

**Pros**:
- AI-powered features
- Modern UI/UX
- Built-in multiplexer
- Active development

**Cons**:
- Proprietary (not fully open source)
- Linux support still beta (2024)
- Different paradigm
- Requires subscription for some features

**Migration Effort**: Very High
- Completely different approach
- Limited Linux support

**Shift+Enter Support**: ✅ Likely - Modern terminal

**References**:
- [Warp](https://www.warp.dev/)

---

## Recommendation

**Best Option**: **WezTerm + Tmux** (Option 1)
- Keeps your tmux workflow intact
- Solves Shift+Enter issue
- Modern, actively developed
- Low migration effort
- Can explore WezTerm multiplexer later if desired

**If You Want Bleeding Edge**: **Zellij** (Option 4)
- Modern Rust-based
- Better keyboard support
- Different but potentially better workflow
- Higher migration effort but future-proof

**If You Want Minimal**: **Alacritty + Tmux** (Option 2)
- Fastest, most minimal
- Keeps tmux
- Simple migration

---

## Migration Checklist (WezTerm + Tmux)

1. Add WezTerm to `flake.nix`
2. Create `home/modules/wezterm.nix` (port kitty config)
3. Update `users/lucas.zanoni/home.nix` to use wezterm instead of kitty
4. Test tmux inside WezTerm
5. Verify Shift+Enter works
6. Update fuzzel config if needed
7. Remove kitty module

---

## Testing Shift+Enter

After switching, test with:
```bash
# In terminal (outside tmux)
kitten show-key  # or wezterm equivalent

# In tmux
tmux show-key -m
```

Press Shift+Enter and verify it shows a proper sequence (not just `^M`).
