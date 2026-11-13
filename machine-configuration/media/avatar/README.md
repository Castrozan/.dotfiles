# Avatar

The avatar runs locally and independently of an agent harness. Its VRM model, portrait assets and rendering libraries
are pinned by Nix and served locally. The characters come from
[VRoid's sample set](https://github.com/madjin/vrm-samples), each CC0 by its embedded VRM licence metadata, and are
declared with their cloud and local voices in `characters.nix`. A new one needs a VRM with VRoid's `Fcl_` face morphs,
which drive the mouth and blink. The first declared character shows at start, and `avatar-command character NAME` swaps
it and its voice while running. Start
the avatar with `avatar-start`, which also opens her voice and the default microphone. `avatar-command mode camera` opens the external camera with no prompt: the avatar-owned
browser loads only this local renderer, so it accepts camera requests by itself. `avatar-controls` chooses a camera by
hand.

Starting the avatar never takes over the screen: its output window opens on the hidden `special:avatar` Hyprland
workspace and keeps rendering there. Only `avatar-controls` opens a visible window.

## Desktop conversation

`avatar-talk` is the interface for talking with the avatar at the desk, with no meeting, virtual camera or virtual
device selected anywhere. It needs only a shell, so every harness reaches it the same way. On a Mac the same command
forwards over ssh to chise, where the avatar runs, and can seat the conversation at that Mac.

| Command | Result |
| --- | --- |
| `avatar-talk open [--language CODE] [--character NAME] [--seat room\|remote]` | Opens the microphone with the window hidden; repeating it keeps the conversation |
| `avatar-talk open --live [--character NAME]` | Opens the conversation on the live duplex voice instead of the local listener and ElevenLabs |
| `avatar-talk ask TEXT [EMOTION]` | Speaks and prints the reply; one verb per turn |
| `avatar-talk hear [--wait SECONDS]` | Blocks for the next complete utterance and prints it; prints nothing on silence |
| `avatar-talk follow` | Prints each utterance as a line, for harnesses with a background watcher; only one of `follow`, `hear` and `ask` listens at a time |
| `avatar-talk say TEXT [EMOTION] [--voice VOICE]` | Speaks aloud and reports `finished` or `interrupted` |
| `avatar-talk status` | Reports whether a conversation is open |
| `avatar-talk show` / `hide` | Brings the avatar window to the current workspace, or hides it again |
| `avatar-talk close` | Hides or stops the avatar and closes the microphone; a running meeting keeps its services and a meeting transcription keeps running |

`avatar-conversation.target` owns the pieces: `avatar-browser` holds the one renderer window, whether or not the
virtual camera is attached, and `avatar-room-microphone` is a private PipeWire process running
[echo cancellation](https://docs.pipewire.org/page_module_echo_cancel.html) in monitor mode. Its reference is everything
the default output plays, so neither the avatar's voice nor a video playing on the speakers reaches the transcript.
Only the wake listener below opens the physical microphone before a conversation; `close` or closing the window ends
the conversation's stream.
The window stays on the hidden `special:avatar` workspace until the agent shows it, because the user wants the avatar
on screen only when an agent chooses to show it.
Speaking for 0.6 seconds over the avatar stops it, so interrupting needs no agent turn.

A pause alone does not end the speaker's turn. After each pause, [Smart Turn](https://github.com/pipecat-ai/smart-turn)
v3.2 judges the turn's last 8 seconds of audio locally, and an unfinished turn holds the reply 2.5 seconds for the rest
of the sentence instead of 0.5. Each transcript entry records that verdict as `turn_finished`. Its Whisper log-mel input
is computed in numpy, matching `transformers` to 1e-6, because `transformers` would pull in torch. The listener runs on
the default Python rather than 3.12 because only the default Python's `onnxruntime` is in the binary cache; the 3.12
one compiles for hours.

The renderer presents its canvas only while an agent shows the window: a presented canvas in a hidden window intermittently
stalled the camera near one frame per second, while a hidden canvas held 60.

The window code is the Hyprland boundary in `scripts/conversation/desktop_window.py`; the rest of the conversation
depends only on the shared services. It addresses the first Hyprland instance by index, because a command forwarded
over ssh carries no `HYPRLAND_INSTANCE_SIGNATURE`. This module is NixOS only because its audio graph is PipeWire.

## Remote seat

A conversation has a seat: the machine whose microphone and speakers it uses. The `room` seat is chise. The `remote`
seat is a Mac, so the avatar can be talked to from any machine while it keeps running on chise, with one floor, one
transcript and one set of voices. `avatar-talk open` on a Mac asks for the remote seat when that Mac's keyboard or mouse
was used in the last five minutes, and for the room otherwise, so an agent working unattended on a Mac still speaks
where the user is. `--seat room` forces the room and `--seat remote` seats it at the Mac whatever its idle time.
`avatar-talk status` reports the seat.

| Piece | Runs on | Does |
| --- | --- | --- |
| `avatar-remote-seat.service` | chise | Serves the seat page and relays audio on `127.0.0.1:8769`; part of `avatar-conversation.target` |
| `AvatarRemoteMicrophone` | chise | Null sink the Mac's microphone plays into; the listener hears its monitor |
| `AvatarLipSync.monitor` | chise | The avatar's voice, which the relay sends to the Mac; speech uses the `remote` output, so chise's speakers stay silent |
| ssh tunnel | Mac | Forwards local port 8769 for as long as the service runs, then closes the browser |
| Headless Chrome | Mac | Captures the default microphone with echo cancellation and plays the voice; headless because a window manager shows a merely hidden window |

The page runs in Chrome because macOS grants the microphone to Chrome itself, asking once per machine, and because
Chrome cancels its own playback from the microphone and needs no audio tooling installed on the Mac. Only a page served from `localhost:8769` may open the audio
socket, and one machine holds the seat at a time.

The seat ends the conversation rather than leaving it deaf: the service stops when no machine attaches within 30
seconds or its machine stays gone for 10, and stopping it stops `avatar-conversation.target`. Closing from either side
closes the Mac's microphone, because the page ends capture when its socket drops. A Mac holds the seat for at most 12
hours.

`show` from a Mac holding the seat opens the window on that Mac and leaves chise's desktop alone. The same tunnel
forwards local port 8770 to the renderer page and 8765 to the control server, and the page loaded with `?viewer` joins
as a display copy: it receives everything the renderer receives and its own events are ignored, so the page on chise
stays the one renderer that feeds the camera and names the character. Microphone audio queued during a network stall
plays out late instead of being dropped.

`open --live` from a Mac names the agent that will receive the tasks as `--agent HOST:PANE`, built from the Mac's
hostname and the caller's herdr pane. Chise reads that pane's Servant from `a2a list` on the Mac, gives it the floor,
and sends each task there with `a2a ask` over ssh. With a remote seat the live voice hears `AvatarRemoteMicrophone`
and plays only into `AvatarLipSync`.

## Live voice

`avatar-talk open --live` puts the conversation on a cloud speech-to-speech model:
[GPT-Live](https://developers.openai.com/api/docs/guides/live-conversations) hears the room microphone and answers
within about a second, so it can listen and speak while work runs. Its own voice replaces the character's ElevenLabs
voice, and the room audio streams to OpenAI for as long as the conversation stays open. `avatar-live.service` runs the
bridge inside `avatar-conversation.target` in place of the listener and plays a second copy of the voice into
`AvatarLipSync` so the mouth moves.

The voice does no work itself. When a request needs the machine it delegates, and the bridge asks the session holding
the floor over `a2a ask`; the reply's last line goes back to the voice, which speaks it. Opening claims the floor for
the opening pane, and naming another live Servant hands it over as in any conversation, because the bridge writes each
finished turn to the shared transcript: the room's lines as `human`, its own as speaker `avatar`.

## Wake by name

`avatar-wake.service` keeps the default microphone open while any agent session with a Servant name is live, and closes
it while an avatar conversation runs, because that conversation's own listener then owns the room. Each utterance is
transcribed locally by Hex's Parakeet, and nothing is stored. One that starts with a greeting and a live Servant's first
name, such as "hey Voyager, check the build", is delivered to that session's pane with `herdr agent prompt`, which lands
even mid-turn, and the avatar conversation then opens, so the reply continues on ElevenLabs. Anyone in the room can say
a name, so the prompt marks the speaker as not verified. `systemctl --user stop avatar-wake` turns it off;
with the service stopped, `avatar-wake --dry-run` reports matches without delivering them.

On a Mac the same listener runs as the `avatar-wake` launchd agent, logging to `~/Library/Logs/avatar-wake.log`, with its
machine effects swapped in `mac_wake_boundaries.py`. `mac_microphone.py` serves a capture page on `127.0.0.1:8771`,
opens it in headless Chrome on the profile `~/.local/share/avatar/wake-browser` and writes the page's frames to stdout in
place of `parec`. The page opens the default input, or the built-in microphone when the default is Bluetooth, which
would otherwise force call-quality sound on everything the Mac plays. Each utterance goes to `avatar-transcribe` on
chise over ssh. A wake opens the conversation with `avatar-talk open --seat remote`, then `ssh chise avatar-claim-floor
--agent HOST:PANE` gives the woken session the floor. A seat held on the Mac pauses the wake, as an open conversation
does on chise; naming another Servant mid-conversation hands the room over only when it sits on chise.

During a conversation the wake reads that conversation's transcript instead of the microphone. Naming another live
Servant by the first or last word of a turn, with or without a greeting, hands the room to it: `addressee.json` in the
avatar runtime directory names the session now addressed, its `avatar-talk follow` starts after the words that named it,
and the previous session's `follow` prints that the room turned and exits. Only lines from the room's own microphone
prompt a session; a voice from a meeting moves the room without prompting anyone.

`addressee.json` is also the floor every speaking agent shares, in conversations and meetings alike. `avatar-command
speak` from a herdr pane first runs `avatar-claim-floor` under a lock: the holder speaks at once, a live holder silences
everyone else, and otherwise the first live Servant to claim takes it. A refused claim stops the speech and names the
holder. Starting a listener frees the floor, and without one anyone may speak.

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
fourth argument is an ElevenLabs voice ID. Spoken text and each captured utterance go to ElevenLabs; transcripts and
video stay on this machine.
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

Transcription posts each utterance to ElevenLabs [Scribe](https://elevenlabs.io/docs/capabilities/speech-to-text),
about one second each, through the key `media-speech` uses, which needs the Speech to Text permission. On room audio it
beat Hex's Parakeet and Whisper and invented nothing in silence; Parakeet ignores a pinned language and Whisper invents
"Obrigado." A failed request falls back to the running [Hex](https://github.com/anomalyco/hex) service's Parakeet v3.
`RECOGNIZED_TERMS` in `cloud_transcriber.py` are sent as
[keyterms](https://elevenlabs.io/docs/eleven-api/guides/how-to/speech-to-text/batch/keyterm-prompting), which add 20%
to the transcription cost and turned "X" and "Eleven Labs" into "Hex" and "ElevenLabs".

`avatar-listen start` transcribes what this computer plays as the `meeting` source and the default microphone as the
`human` source into a private transcript under the user runtime directory, and refuses while a desktop conversation is
open. `--microphone SOURCE` names another microphone. Pass `--language CODE` for a meeting in one language: detection
on short clips invents other languages.
The microphone is not echo-cancelled, so wear a headset: a phrase both sources hear within 15 seconds is kept once.
Entries carry a `speaker` name when a voice enrolled with `avatar-listen enroll NAME --first N --last M` (at least 3
segments) matches, else null; `avatar-listen voices` lists and `avatar-listen forget NAME` deletes profiles, stored as
embeddings only.

Capture ends rather than moves when its device disappears, then resumes on the current
default output, so a Bluetooth drop cannot redirect it to a real microphone. `avatar-listen read --since N --wait 30`
returns new entries and `avatar-listen follow --match NAME` streams them. `avatar-listen stop` or `avatar-stop` ends
capture. Starting again replaces the transcript. Other people in a call are being transcribed by ElevenLabs: tell them.
