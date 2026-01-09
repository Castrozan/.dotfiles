# Tmux Documentation

## Resurrect

**Save**: `prefix + Ctrl-s` | **Restore**: `prefix + Ctrl-r`

### Restore from Backup

If you overwrote your session, restore from an older backup:

```bash
cd ~/.tmux/resurrect
ln -sf tmux_resurrect_YYYYMMDDTHHMMSS.txt last
# Then: prefix + Ctrl-r
```

Backups: `~/.tmux/resurrect/` | `last` symlink points to active backup.

## Shift+Enter in Kitty + Tmux

### The Problem

tmux doesn't support kitty's CSI-u keyboard protocol. When kitty sends CSI-u sequences like `\e[13;2u` for Shift+Enter, tmux shows "unknown key" errors. This is a fundamental incompatibility - there is no real solution, only workarounds.

### What We Tried

1. **CSI-u sequences in kitty**: Mapped Shift+Enter to `\e[13;2u` - tmux couldn't parse it, showed "unknown key" errors
2. **tmux extended-keys config**: Added `extended-keys on`, `xterm-kitty:extkeys` - didn't help, tmux still can't decode CSI-u
3. **tmux key bindings**: Tried binding CSI-u sequences directly in tmux - tmux parser doesn't accept arbitrary escape sequences
4. **Workaround**: Map Shift+Enter to plain newline (`\r`) in kitty - this works but loses modifier information

### Current Workaround

Nothing.

### Why There's No Real Solution

As the kitty developer states: kitty and tmux have fundamentally different approaches. tmux doesn't support kitty's keyboard protocol, and there's no plan to add it.

**References**:
- [tmux issue #3335](https://github.com/tmux/tmux/issues/3335) - kitty keyboard protocol support
- [kitty issue #391](https://github.com/kovidgoyal/kitty/issues/391#issuecomment-638320745) - kitty developer's comment on tmux compatibility
