# TOOLS-BASE.md - Base Tool Configuration

These are stable system configurations. For runtime notes and learned tips, see `TOOLS.md` in the workspace.

## Browser
- **Default profile**: `brave` (Lucas's Brave via CDP on port 9222)
- **Isolated profile**: `clawd` (managed browser on cdpPort 18800)
- Brave must be launched with `--remote-debugging-port=9222`

## Audio
- Local Whisper CLI transcription (Portuguese, small model)
- Path: `/run/current-system/sw/bin/whisper`
- First run downloads model (~461MB)

## System
- NixOS, Dell G15
- Dotfiles: `~/.dotfiles` (Flakes + Home Manager)
- Obsidian vault: `/home/zanoni/vault/`
- Setuid wrappers (sudo): `/run/wrappers/bin`
- System packages: `/run/current-system/sw/bin`
- User packages: `/etc/profiles/per-user/zanoni/bin`
