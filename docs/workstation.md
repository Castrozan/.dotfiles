Peripheral and hardware configuration follows a layered pattern: NixOS modules in `nixos/modules/` handle kernel-level concerns (udev rules, sysctl, kernel modules), host-specific configs in `hosts/<hostname>/configs/` handle machine-dependent hardware (GPU, touchpad quirks, audio cards), and home-manager scripts in `home/scripts/` provide user-facing CLI tools. User-specific overrides live in `users/<username>/`.

## Input Devices

Mice requiring custom polling rates or firmware configuration get a NixOS module for udev permissions (group `input`, mode `0660`) and a CLI script in `bin/` wrapped through `home/scripts/`. The ATK protocol (vendor `373b`) uses HID feature reports on interface 1 — the `mouse-poll-rate` script handles EEPROM read/write for rate changes. Polling rates above 1000Hz require USB High Speed (480 Mbps); Full Speed (12 Mbps) caps at 1000Hz regardless of EEPROM setting. Some dongles re-enumerate with a different USB PID when switching speed modes — udev rules must cover all PIDs. In 8K mode, the config interface is flooded with mouse movement reports, so config reads must filter by HID report ID.

Touchpad quirks go in `hosts/<hostname>/configs/libinput-quirks.nix` as `/etc/libinput/local-overrides.quirks`. Libinput acceleration, tapping, and palm detection are configured per-host in the `services.libinput.touchpad` block.

Keyboard layout is `br` with `nodeadkeys` variant, set at both NixOS level (`services.xserver.xkb`) and console level (`console.keyMap = "br-abnt2"`). Keyboard firmware tools like Vial get their own home-manager module (`home/modules/vial.nix`).

## Audio

PipeWire is the audio server. Applications must use PulseAudio protocol (`ao=pulse`), never `ao=pipewire` directly — Nix's bundled libpipewire version can ABI-mismatch the system daemon, causing silence. The PulseAudio protocol is version-independent via pipewire-pulse. Bluetooth codec policy lives in `home/modules/audio/bluetooth-policy.nix` as single source of truth. A systemd service auto-switches the default sink on Bluetooth connect/disconnect. Host-specific audio card disabling (HDMI outputs, unused interfaces) goes in `hosts/<hostname>/configs/audio.nix`.

## Networking

WiFi power saving is disabled (`wifi.powersave = false`). The home network profile forces 5GHz band (`band = "a"`) and uses a WPA-PSK stored via agenix (`secrets/wifi-psk-zanoni.age`). TCP uses BBR congestion control with enlarged buffers and fast open enabled — configured in `nixos/modules/network-optimization.nix`. Tailscale provides the mesh VPN (`nixos/modules/tailscale.nix`). Firewall is on with only SSH (port 22) allowed inbound.

## Window Manager

Hyprland is the primary compositor, with GNOME/GDM as fallback display manager. Hyprland is sourced from the flake input (not nixpkgs) for latest features. XWayland is enabled. Monitor configuration is per-user in `users/<username>/home/hyprland.nix` via `hypr-host/monitors.conf`. The built-in laptop display (`eDP-1`) is disabled when docked — only the external monitor is used. Hypridle is masked (no auto-lock), hyprlock is available for manual locking. XDG portals for screen sharing use a custom module (`nixos/modules/xdg-portal.nix`).

## Browser

Brave is the daily browser (no special Nix config — managed outside dotfiles). Firefox has a home-manager module (`home/modules/firefox.nix`). Agent browser automation uses a dedicated Chrome profile via Pinchtab at `~/.pinchtab/chrome-profile/`, separate from the user's browsing — sessions persist across restarts.

## GPU

NVIDIA configuration is host-specific (`hosts/<hostname>/configs/nvidia.nix`). GPU clock locking for desktop performance goes in the host config. Virtual camera support (v4l2loopback) is enabled at NixOS level for avatar/streaming use.

## Adding New Device Support

New peripherals follow the pattern: (1) NixOS module in `nixos/modules/` for udev rules and kernel config, (2) CLI script in `bin/` for device interaction, (3) Nix wrapper in `home/scripts/<name>.nix` with PATH dependencies, (4) import the wrapper in `home/scripts/default.nix`, (5) import the NixOS module in `users/<username>/nixos.nix`. The user must be added to the relevant group (usually `input`) in the NixOS module.
