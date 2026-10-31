# Avatar meeting media

The avatar runs locally and independently of an agent harness. Its recovered VRM model, portrait assets and rendering
libraries are pinned by Nix and served locally. Start it with `avatar-start`; run
`avatar-controls` for camera permission and video modes. The controls must use the avatar-owned browser profile so their
permission flow can reach the output window.

Starting the avatar never takes over the screen: its output window opens on the hidden `special:avatar` Hyprland
workspace and keeps rendering there. Only `avatar-controls` opens a visible window.

Both audio inputs start muted at unity gain. `avatar-audio status` shows ownership, mute and level state. Send an application's
playback to `AvatarMic`, for example `PULSE_SINK=AvatarMic paplay --client-name=agent generated.wav`, then use
`avatar-audio mute agent 0` to enable that channel. `avatar-audio volume agent 70` changes its level; `mute agent 1`
silences it. PulseAudio's volume percentage uses its normal nonlinear scale.

Inspect `pactl list short sources` and explicitly attach the intended human input with `avatar-audio attach SOURCE`.
`avatar-audio mute human 0` enables it; the human and agent mute/volume controls are independent. The meeting application
must select `AvatarMicrophone` as its microphone. No defaults or existing application streams are changed automatically.

A running application may need its own output selector or an explicitly selected PulseAudio sink-input moved to
`AvatarMic`. Setting an environment variable on a second launch does not reroute an existing application instance.
Streams routed to `AvatarMic` stay there: desktop audio switching only moves streams on hardware sinks.
Keep meeting playback on headphones or the normal output; routing meeting playback into the mix creates feedback.
This generic audio route does not expose a voice session's internal audio API or provide an integration for a remote app
whose playback never reaches this computer.

Select `Avatar Cam` as the meeting camera after `avatar-start` is ready. The local controls request physical camera
permission; no physical camera is opened at startup. `avatar-command mode avatar`, `mode camera` and `mode composite`
request switching and wait for the renderer's result. Camera modes require a locally enabled camera first.
`avatar-command expression happy` changes expression; `avatar-command status` reports the control connection.
`avatar-command speak "Text" neutral mic` speaks with a local Piper voice into the meeting mix; nothing leaves the
machine. Speech from every agent shares one floor: turns run in arrival order, the agent channel opens only for a turn
and returns to its previous mute state, and the command returns when the speech has finished or was cut off.
`avatar-command stop-speaking` ends the current turn and drops the waiting ones. Pass a voice file name from
`speech-voices.nix` as the fourth argument to change language. Applications playing local audio need no speech service.

Stop agent playback, mute both channels and switch the meeting application's selected microphone/camera before `avatar-stop` removes the
virtual devices. Meeting applications can choose their own fallback device when a selected device disappears.
WirePlumber restores saved volume per client name, so a client saved at zero plays silently into the mix.
Teardown refuses to remove an input sink that still has agent playback connected, keeping the inputs muted so that
playback cannot fall back to speakers. Stop that playback, then run `avatar-audio stop` to finish cleanup.
The avatar stop operation releases its camera, owned browser and audio modules, without stopping other applications.

The virtual camera uses [v4l2loopback's exclusive capture mode](https://github.com/v4l2loopback/v4l2loopback), so it appears
as a capture device only while its producer runs. A meeting application may need to refresh its device list.
The agent audio path is buffered to match the local camera pipeline; the human path stays low latency.
Meeting applications can add their own processing delay, so local alignment is not a guarantee for every remote client.

Audio routing uses PipeWire's [loopback](https://docs.pipewire.org/page_pulse_module_loopback.html) and
[remapped source](https://docs.pipewire.org/page_pulse_module_remap_source.html) modules with explicit endpoints.

`avatar-listen start` transcribes what this computer plays, locally, into a private transcript under the user runtime
directory, in the language spoken. No microphone is opened unless named with `--microphone SOURCE`, which adds your
voice as the `human` source. Capture ends rather than moves when its device disappears, then resumes on the current
default output, so a Bluetooth drop cannot redirect it to a real microphone. `avatar-listen read --since N --wait 30`
returns new entries and `avatar-listen follow --match NAME` streams them. `avatar-listen stop` or `avatar-stop` ends
capture. Starting again replaces the transcript. Other people in a call are being transcribed: tell them.
