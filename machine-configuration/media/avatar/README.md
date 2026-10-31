# Avatar meeting media

The avatar runs locally and independently of an agent harness. Its recovered VRM model, portrait assets and rendering
libraries are pinned by Nix and served locally. Start it with `avatar-start`; open
[the local controls](http://localhost:3000/controls.html) for camera permission and video modes.

Both audio inputs start muted at 50%. `avatar-audio status` shows ownership, mute and level state. Send an application's
playback to `AvatarMic`, for example `PULSE_SINK=AvatarMic paplay generated.wav`, then use
`avatar-audio mute agent 0` to enable that channel. `avatar-audio volume agent 70` changes its level; `mute agent 1`
silences it. PulseAudio's volume percentage uses its normal nonlinear scale.

Inspect `pactl list short sources` and explicitly attach the intended human input with `avatar-audio attach SOURCE`.
`avatar-audio mute human 0` enables it; the human and agent mute/volume controls are independent. The meeting application
must select `AvatarMicrophone` as its microphone. No defaults or existing application streams are changed automatically.

A running application may need its own output selector or an explicitly selected PulseAudio sink-input moved to
`AvatarMic`. Setting an environment variable on a second launch does not reroute an existing application instance.
Keep meeting playback on headphones or the normal output; routing meeting playback into the mix creates feedback.
This generic audio route does not expose a voice session's internal audio API or provide an integration for a remote app
whose playback never reaches this computer.

Select `Avatar Cam` as the meeting camera after `avatar-start` is ready. The local controls request physical camera
permission; no physical camera is opened at startup. `avatar-command mode avatar`, `mode camera` and `mode composite`
request switching and wait for the renderer's result. Camera modes require a locally enabled camera first.
`avatar-command expression happy` changes expression; `avatar-command status` reports the control connection.
`avatar-command speak "Text" neutral mic` uses the existing Edge TTS provider and sends the text to that provider.
Playing an existing local audio file needs no TTS service.

Mute both channels and switch the meeting application's selected microphone/camera before `avatar-stop` removes the
virtual devices. Meeting applications can choose their own fallback device when a selected device disappears.
The avatar stop operation releases its camera, owned browser and audio modules, without stopping other applications.

The virtual camera uses [v4l2loopback's exclusive capture mode](https://github.com/v4l2loopback/v4l2loopback), so it appears
as a capture device only while its producer runs. A meeting application may need to refresh its device list.
Audio routing uses PipeWire's [loopback](https://docs.pipewire.org/page_pulse_module_loopback.html) and
[remapped source](https://docs.pipewire.org/page_pulse_module_remap_source.html) modules with explicit endpoints.
