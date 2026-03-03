# Audio Pipeline

PipeWire is the audio server on all platforms. WirePlumber is the session manager. All user-facing tools speak PulseAudio protocol via the `pipewire-pulse` bridge — never the native PipeWire API. This is a hard constraint: Nix-installed binaries link against the Nix store's `libpipewire`, which has an ABI mismatch with the system `libpipewire` on Ubuntu. PulseAudio protocol is version-independent, so `pactl` and `mpv --ao=pulse` work everywhere without breakage.

The same constraint applies to `xdg-desktop-portal-hyprland` on Ubuntu, which needs the system `libpipewire` for screen sharing. It uses `LD_PRELOAD` to force the system library.


## Platform Split

NixOS configures PipeWire and WirePlumber at the system level through `hosts/*/configs/audio.nix` using declarative options (`services.pipewire`, `wireplumber.extraConfig`). Ubuntu configures them at the user level through `xdg.configFile` drop-ins in `~/.config/pipewire/pipewire.conf.d/` and `~/.config/wireplumber/`. The home-manager audio module at `home/modules/audio/` handles this split with `lib.mkIf (!isNixOS)` — the `xdg.configFile` block only activates on Ubuntu.

Both platforms share the same Bluetooth policy values. `home/modules/audio/bluetooth-policy.nix` is a plain Nix attrset (not a module) that both the Ubuntu Lua configs and the NixOS declarative configs import directly. This prevents drift between platforms. Codec preference, auto-connect profiles, priority values, and headset autoswitch behavior are defined once there.

WirePlumber config format differs by platform because Ubuntu ships WirePlumber 0.4 (Lua-based `table.insert` into monitor rules) while NixOS uses WirePlumber 0.5 (declarative `monitor.*.rules` attrsets). The semantics are identical, only the syntax changes.


## Bluetooth Audio Takeover

Two independent mechanisms guarantee Bluetooth becomes the default output the moment it connects.

WirePlumber's priority system is the first layer. Bluetooth output nodes get session priority 3000 (from `bluetooth-policy.nix`), which beats every ALSA output (~1000 default). WirePlumber auto-selects the highest-priority available node, so BT wins by policy.

The `bluetooth-audio-autoswitch` systemd service is the second layer. It runs `pactl subscribe` in a loop, watching for both `'new' on sink` and `'remove' on sink` events. When a new sink appears with a name matching `bluez_output.*`, it calls `pactl set-default-sink` and then moves all existing streams to the new sink. When any sink is removed (e.g. BT disconnect), it moves all streams to the new default sink. This explicit stream migration is necessary because streams can get pinned to specific sinks — WirePlumber's `follow` policy only moves unpinned streams. The service runs on both NixOS and Ubuntu via PulseAudio protocol.

Profile toggling between A2DP (stereo, no mic) and HFP (mono, mic enabled) is done through `bin/hypr/bluetooth`, which calls `pactl set-card-profile` on the `bluez_card.*` device. WirePlumber also supports automatic headset profile switching when a VoIP app requests a source, controlled by the `autoswitchToHeadsetProfile` policy value.


## Node Priority Hierarchy

All priority values flow from `bluetooth-policy.nix` or platform-specific WirePlumber rules.

Bluetooth output sits at 3000, making it always preferred when connected. The Realtek built-in mic (`HiFi__Mic1`) is at 2500 on NixOS, making it the preferred capture source over other Realtek inputs (2000). Generic ALSA inputs are at 2000 on both platforms. ALSA outputs use their default priority (~1000). The AMD HDMI audio card (`pci-0000_05_00.5`) is fully disabled on NixOS to prevent a phantom output from appearing.


## Stream Target Restore

WirePlumber's `restore-target` is disabled on both platforms (`bluetooth-policy.nix` sets `restoreStreamTarget = false`). Without this, WirePlumber re-pins streams to their last-used sink via its restore-stream database, which prevents them from following default sink changes. With `restore-target = false`, all streams always follow the default sink — no streams get pinned. The one-time cleanup step is deleting `~/.local/state/wireplumber/restore-stream` to clear stale pins from before the config change.


## Output Switching

The `bin/audio-output-switch` script cycles through available hardware sinks. It lists all non-monitor sinks, finds the current default, advances to the next one in the list, calls `pactl set-default-sink`, and then explicitly moves all playing streams to the new sink. It sends a desktop notification showing the new device's human-readable description. Bound to `SHIFT + XF86AudioStop` in `bindings.conf`.


## Volume Control

The `bin/volume` script is the single entry point for all volume operations. It prefers the default sink when it's RUNNING, then falls back to any running sink, then `@DEFAULT_SINK@`. This matters because when multiple sinks are active (e.g. BT headphones + laptop speakers), the default sink reflects the user's intent (set by the autoswitch service or manual selection). All operations use `pactl`.

OSD notifications go through a Unix socket at `/tmp/quickshell-osd.sock` as JSON messages. The Quickshell bar's OSD component listens on this socket and renders a vertical slider. Direct drag/scroll on the OSD sends `pactl set-sink-volume` commands.


## Virtual Audio Devices

The avatar system creates ephemeral virtual devices via `pactl load-module`: a null sink (`AvatarSpeaker`) where TTS audio plays, linked through `pw-link` to a virtual microphone (`AvatarMic`) that appears as a real source in Google Meet/Zoom via `module-remap-source`.


## Clock and Scheduling

The global clock rate is 48000 Hz with 44100 Hz allowed as an alternative. PipeWire resamples as needed. Real-time scheduling uses `rtkit` on NixOS and the `libpipewire-module-rt` drop-in on Ubuntu (nice level -11, RT priority 88).
