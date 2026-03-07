# HEARTBEAT — Domain Restructure + Assertions + Policy Docs

## Objective
Deepen home/modules flat structure into domain directories. Add NixOS assertions to every domain with invariants worth protecting. Co-locate policy documentation with each domain. Clean code (remove comments, fix naming). Clean tests.

## Domain Grouping Plan

### home/modules/ restructure (flat → domain dirs)

| Domain Dir | Files Moving In | Status |
|---|---|---|
| `security/` | `agenix.nix`, `gpg.nix`, `password-store.nix` | done |
| `terminal/` | `fish.nix`, `kitty.nix`, `wezterm.nix`, `tmux.nix`, `atuin.nix`, `yazi.nix` | done |
| `editor/` | `neovim.nix`, `vscode/`, `cursor/`, `zed-editor.nix`, `jetbrains-idea.nix` | done |
| `browser/` | `chrome-global.nix`, `firefox.nix` | done |
| `media/` | `ani-cli.nix`, `bad-apple.nix`, `obs-studio.nix`, `youtube.nix`, `suwayomi-server.nix` | done |
| `desktop/` | `clipse.nix`, `fuzzel.nix`, `flameshot.nix`, `satty.nix`, `ksnip.nix`, `bananas.nix`, `fonts.nix` | done |
| `network/` | `network-optimization.nix`, `tailscale-daemon.nix`, `openfortivpn/` | done |
| `system/` | `ubuntu-system-tuning.nix`, `oom-protection.nix`, `lid-switch-ignore.nix` | done |
| `dev/` | `devenv.nix`, `glab.nix`, `lazygit.nix`, `bruno.nix`, `ccost.nix`, `mcporter.nix` | done |
| `voice/` | `hey-bot.nix`, `hey-bot-test.nix`, `voice-pipeline.nix`, `whisp-away.nix`, `voxtype.nix` | done |
| `gaming/` | `vesktop.nix`, `cmatrix.nix`, `cbonsai.nix`, `install-nothing.nix` | done |

### NixOS Assertions

| Module | Assertions | Status |
|---|---|---|
| `network-optimization.nix` | BBR, fq, WiFi powersave | done |
| `hosts/dellg15/configs/nvidia.nix` | PRIME sync, modesetting, LTS kernel | done |
| `hosts/dellg15/configs/audio.nix` | PipeWire enabled, PulseAudio disabled, rtkit, Bluetooth | done |
| `hosts/dellg15/configs/configuration.nix` | zram, earlyoom, swappiness, flakes enabled | done |
| `nixos/modules/tailscale.nix` | loose reverse path, trusted interfaces | done |
| `nixos/modules/virtualization.nix` | Docker on boot, libvirtd | done |

### Policy Docs (co-located)

| Domain | Doc | Status |
|---|---|---|
| `nixos/modules/network-policy.md` | Network | done |
| `hosts/dellg15/configs/nvidia-policy.md` | GPU/NVIDIA | done |
| `hosts/dellg15/configs/audio-policy.md` | NixOS audio | done |
| `home/modules/audio/audio-pipeline.md` | Audio pipeline | exists |

### Code Cleanup
- Remove all comments from modules — done for all nixos/modules/ and host configs
- home/modules/ comment cleanup — in progress

## Current Step
Running tests, then squash commits
