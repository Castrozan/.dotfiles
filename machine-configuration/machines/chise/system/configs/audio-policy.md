# Audio Policy

This module configures the NixOS-level audio stack: PipeWire, WirePlumber, Bluetooth, and ALSA device management. The home-manager `audio/` module handles user-space audio tools. NixOS assertions enforce PipeWire exclusivity, rtkit scheduling, and Bluetooth availability.


## PipeWire and PulseAudio Exclusivity

PipeWire replaces PulseAudio as the audio server. PulseAudio must be explicitly disabled (`services.pulseaudio.enable = false`) because NixOS does not automatically disable it when PipeWire is enabled — both can be active simultaneously, fighting over the PulseAudio socket. PipeWire provides its own PulseAudio compatibility layer (`pulse.enable = true`) so all PulseAudio clients work transparently.

JACK compatibility is enabled (`jack.enable = true`) for pro-audio tools that use the JACK protocol. ALSA support includes 32-bit compatibility for Wine and older applications.


## Clock Rate Configuration

The PipeWire clock is set to 48000 Hz default with 44100 and 48000 as allowed rates. 48000 Hz matches the native rate of most USB audio devices and Bluetooth codecs. Allowing 44100 Hz prevents unnecessary resampling when playing CD-quality audio. PipeWire's sample rate switching happens at the graph level — when all clients on the graph use 44100, PipeWire switches the hardware to 44100 to avoid resampling entirely.


## Real-Time Scheduling

rtkit (RealtimeKit) is enabled to allow PipeWire to acquire real-time scheduling priority without running as root. PipeWire's audio processing thread needs to run every quantum period (typically 1024/48000 = 21.3ms) without being preempted. Under heavy CPU load (Nix builds, CUDA training), a normal-priority audio thread gets preempted causing audible glitches (clicks, pops, dropouts). rtkit grants SCHED_RR priority through a D-Bus API with per-user limits.


## Bluetooth Audio

Bluetooth is enabled with `powerOnBoot = true` so headsets reconnect automatically after boot. The `Source,Sink,Media,Socket` capabilities and `Experimental = true` enable the full BlueZ5 audio profile stack including battery reporting and codec negotiation.

WirePlumber handles Bluetooth policy through `monitor.bluez.rules`. The codec preference list (`bluez5.codecs`) from `bluetooth-policy.nix` orders codecs by quality: SBC-XQ and AAC before baseline SBC. `autoswitch-to-headset-profile` controls whether WirePlumber automatically switches from A2DP (high-quality output) to HSP/HFP (bidirectional with microphone) when an application opens a recording stream.

Bluetooth sink priority is set higher than the laptop speakers so audio automatically routes to the headset when connected. The laptop mic priority is set lower so the Bluetooth headset mic takes precedence.


## ALSA Device Filtering

Three ALSA cards are disabled in WirePlumber: `pci-0000_05_00.5` (unused AMD audio controller), `pci-0000_01_00.1` (NVIDIA HDMI audio), and `pci-0000_05_00.1` (another HDMI output). These devices create phantom sinks in PipeWire that confuse application routing and appear in volume controls. Only the Realtek ALC256 (`pci-0000_05_00.6`) remains active as the laptop's built-in audio.

The Realtek source priority is tuned so `Mic1` (internal microphone with noise cancellation) ranks above the generic input, ensuring voice applications default to the correct input without manual selection.


## Stream Restore Target

`stream.restore-target` from `bluetooth-policy.nix` controls whether PipeWire remembers which output device each application was using. This prevents the common annoyance where disconnecting Bluetooth headphones leaves applications silently routing to a nonexistent sink.
