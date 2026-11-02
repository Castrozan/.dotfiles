# Avatar

The avatar runs locally and independently of an agent harness. Its VRM model, portrait assets and rendering libraries
are pinned by Nix and served locally. The model is Darkness Shibu from
[VRoid's sample set](https://github.com/madjin/vrm-samples), CC0 by its embedded VRM licence metadata. Start it with `avatar-start`, which also opens her voice
and the default microphone. `avatar-command mode camera` opens the external camera with no prompt: the avatar-owned
browser loads only this local renderer, so it accepts camera requests by itself. `avatar-controls` chooses a camera by
hand.

Starting the avatar never takes over the screen: its output window opens on the hidden `special:avatar` Hyprland
workspace and keeps rendering there. Only `avatar-controls` opens a visible window.

## Desktop conversation

`avatar-talk` is the interface for talking with the avatar at the desk, with no meeting, virtual camera or virtual
device selected anywhere. It needs only a shell, so every harness reaches it the same way. On a Mac the same command
forwards over ssh to chise, where the avatar and microphone live.

| Command | Result |
| --- | --- |
| `avatar-talk open [--language CODE]` | Shows the window and opens the microphone; repeating it keeps the conversation |
| `avatar-talk ask TEXT [EMOTION]` | Speaks and prints the reply; one verb per turn |
| `avatar-talk hear [--wait SECONDS]` | Blocks for the next complete utterance and prints it; prints nothing on silence |
| `avatar-talk follow` | Prints each utterance as a line, for harnesses with a background watcher |
| `avatar-talk say TEXT [EMOTION] [--voice VOICE]` | Speaks aloud and reports `finished` or `interrupted` |
| `avatar-talk status` | Reports whether a conversation is open |
| `avatar-talk close` | Hides or stops the avatar and closes the microphone; a running meeting keeps its services |

`avatar-conversation.target` owns the pieces: `avatar-browser` holds the one renderer window, whether or not the
virtual camera is attached, `avatar-window` moves it onto the current workspace in a pinned corner, and
`avatar-room-microphone` is a private PipeWire process running
[echo cancellation](https://docs.pipewire.org/page_module_echo_cancel.html) in monitor mode. Its reference is everything
the default output plays, so neither the avatar's voice nor a video playing on the speakers reaches the transcript.
Nothing opens the physical microphone until a conversation opens, and `close` or closing the window ends that stream.
Speaking for 0.6 seconds over the avatar stops it, so interrupting needs no agent turn.

The renderer presents its canvas only during a conversation: a presented canvas in a hidden window intermittently
stalled the camera near one frame per second, while a hidden canvas held 60.

The window code is the Hyprland boundary in `scripts/conversation/desktop_window.py`; the rest of the conversation
depends only on the shared services. This module is NixOS only because its audio graph is PipeWire.

## Meetings

The audio graph starts muted at unity gain, and `avatar-start` then runs `avatar-audio open`: it attaches the default
microphone and unmutes both inputs, so a meeting that selects `AvatarMicrophone` hears the avatar and the user with no
further step. Nothing reaches a meeting until it selects that source. `avatar-audio status` shows ownership, mute and
level state.

To use another microphone, run `avatar-audio attach SOURCE` before `avatar-audio open`. The human and agent mute and
volume controls are independent: `avatar-audio mute human 1` silences the user alone, and `avatar-audio volume agent 70`
changes the avatar's level on PulseAudio's nonlinear scale. Send other playback to `AvatarMic` with
`PULSE_SINK=AvatarMic paplay --client-name=agent generated.wav`.

`avatar-command mode camera` and `mode composite` open the external camera, falling back to the built-in one, and
`mode avatar` releases it. In camera mode the avatar replaces the camera while she speaks, then the camera returns.

A running application may need its own output selector or an explicitly selected PulseAudio sink-input moved to
`AvatarMic`. Setting an environment variable on a second launch does not reroute an existing application instance.
Streams routed to `AvatarMic` stay there: desktop audio switching only moves streams on hardware sinks.
Keep meeting playback on headphones or the normal output; routing meeting playback into the mix creates feedback.
This generic audio route does not expose a voice session's internal audio API or provide an integration for a remote app
whose playback never reaches this computer.

Select `Avatar Cam` as the meeting camera after `avatar-start` is ready. The local controls request physical camera
permission; no physical camera is opened at startup. `avatar-command mode avatar`, `mode camera` and `mode composite`
request switching and wait for the renderer's result. Camera modes require a locally enabled camera first.
`avatar-command capabilities` lists what the avatar can do. `expression NAME [INTENSITY]` sets the face, `gesture NAME`
plays a motion, `pose NAME` holds a body pose, `look TARGET` moves the eyes and head, `idle MODE` sets the resting motion,
and `avatar-command status` reports the control connection. An unknown name fails with an error. An expression keeps its
brows and eyes during speech while speech owns the mouth; `speak` restores the previous expression when the turn ends.

`avatar-command speak "Text" happy` plays to the meeting and to your own output, since a meeting never returns your own
microphone to you, and sends that text to ElevenLabs through `media-speech`, with the emotion mapped to a
delivery direction, then plays it into the meeting mix. Character timing shapes the mouth to the spoken vowels. The
default voice is Jessica. If the cloud fails or takes over 15 seconds, the same turn uses the local Kokoro voice
`pf_dora`, which is also female and takes longer to start. Piper speaks only when Kokoro fails too, and every Portuguese
Piper voice is male. A fourth argument of `pf_dora` or a Piper voice from `speech-voices.nix` stays local; any other
fourth argument is an ElevenLabs voice ID. Only the text an agent chooses to speak leaves the machine: captured audio,
transcripts and video never do.
Speech from every agent shares one floor: turns run in arrival order, the agent channel opens only for a turn
and returns to its previous mute state, and the command returns when the speech has finished or was cut off.
`avatar-command stop-speaking` ends the current turn and drops the waiting ones. Applications playing local audio need
no speech service.

Stop agent playback, mute both channels and switch the meeting application's selected microphone/camera before `avatar-stop` removes the
virtual devices. Meeting applications can choose their own fallback device when a selected device disappears.
WirePlumber restores saved volume per client name, so a client saved at zero plays silently into the mix.
Teardown refuses to remove an input sink that still has agent playback connected, keeping the inputs muted so that
playback cannot fall back to speakers. Stop that playback, then run `avatar-audio stop` to finish cleanup.
The avatar stop operation releases its camera, owned browser and audio modules, without stopping other applications.

The virtual camera uses [v4l2loopback's exclusive capture mode](https://github.com/v4l2loopback/v4l2loopback), so it appears
as a capture device only while its producer runs. A meeting application may need to refresh its device list.
The renderer sends raw frames to the camera over a local socket at 60 frames per second; JPEG through DevTools capped it
near 54.
The agent audio path is buffered to match the local camera pipeline; the human path stays low latency.
Meeting applications can add their own processing delay, so local alignment is not a guarantee for every remote client.

Audio routing uses PipeWire's [loopback](https://docs.pipewire.org/page_pulse_module_loopback.html) and
[remapped source](https://docs.pipewire.org/page_pulse_module_remap_source.html) modules with explicit endpoints.

Local transcription uses whisper.cpp's Vulkan build with the quantized small model: about one second per utterance on
this machine's integrated GPU with a pinned language, and about a second more with language detection.

`avatar-listen start` transcribes what this computer plays as the `meeting` source and the default microphone as the
`human` source, locally, into a private transcript under the user runtime directory. `--microphone SOURCE` names another
microphone. Pass `--language CODE` for a meeting in one language: detection on short clips invents other languages.
The microphone is not echo-cancelled, so wear a headset or the meeting is transcribed twice.

Capture ends rather than moves when its device disappears, then resumes on the current
default output, so a Bluetooth drop cannot redirect it to a real microphone. `avatar-listen read --since N --wait 30`
returns new entries and `avatar-listen follow --match NAME` streams them. `avatar-listen stop` or `avatar-stop` ends
capture. Starting again replaces the transcript. Other people in a call are being transcribed: tell them.
