# Avatar

The avatar runs locally and independently of an agent harness. Its VRM model, portrait assets and rendering libraries
are pinned by Nix and served locally. The characters come from
[VRoid's sample set](https://github.com/madjin/vrm-samples), each CC0 by its embedded VRM licence metadata, and are
declared in `cast/`, where every character has one gender and its model and cloud, local and live voices all match it.
A new one needs a VRM with VRoid's `Fcl_` face morphs, which drive the mouth and blink. `cast/servant-characters.txt`
gives every Servant in the roster a character of its gender, and whoever takes the floor appears as that character, so
nobody picks one by hand. The first declared character shows at start, and `avatar-command character NAME` still swaps
it and its voice while running. Start
the avatar with `avatar-start`, which also opens her voice and the default microphone. `avatar-command mode camera` opens the external camera with no prompt: the avatar-owned
browser loads only this local renderer, so it accepts camera requests by itself. `avatar-controls` chooses a camera by
hand.

Starting the avatar never takes over the screen: its output window opens on the hidden `special:avatar` Hyprland
workspace and keeps rendering there. Only `avatar-controls` opens a visible window.

A rebuild leaves a running avatar alone: every avatar unit asks Home Manager to keep its old version, so a conversation
or meeting never drops when chise is rebuilt. New code runs only once a unit starts again: the conversation's
microphone, listener and live voice at the next conversation, and the audio, renderer, browser, camera, control server
and seat at the next `avatar-stop` and `avatar-start`, which is how a deployed change is made live once nobody listens.

## Health

`avatar-doctor` runs on every machine and checks each link the voice depends on, naming the broken one. On the avatar
host it checks Hex, the wake listener and a transcription round trip. On a Mac it first reaches the host, relays the
host's own findings, then checks the wake agent, its microphone page and this Mac's own transcription. It exits non-zero
when any link is broken, and `--json` prints the findings for another program. The host is named once, in
`home-manager/avatar-topology.nix`.

## Desktop conversation

`avatar-talk` is the interface for talking with the avatar at the desk, with no meeting, virtual camera or virtual
device selected anywhere. It needs only a shell, so every harness reaches it the same way. On a Mac the same command
holds a voice conversation on that Mac alone, described under [conversation on a Mac](#conversation-on-a-mac).

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

## Conversation on a Mac

Every `avatar-talk` verb on a Mac runs on that Mac and needs no other machine. `open` starts three launch agents and
`close` stops them: `com.dotfiles.avatar-control`, the same control server the avatar host runs;
`com.dotfiles.avatar-renderer`, which serves the avatar page on `127.0.0.1:3000`; and `com.dotfiles.avatar-conversation`,
the same listener the host runs. The listener captures through a headless Chrome page served on `127.0.0.1:8772`, which
also plays the voice, so Chrome cancels the avatar's own speech from the microphone.

`say` goes through the control server like on the host, so voices, emotions, the speaking queue and interruption behave
the same. Only the player differs: on a Mac the control server plays through the conversation page, or through the
speakers when no conversation is open, and moves the mouth from the loudness of the recording it is playing. With no
conversation open, `say` raises the control server for that one sentence. `show` opens the avatar window on the Mac and
`hide` closes it. Sustained speech from the room hushes the avatar mid-sentence, and `close` deletes the transcript.

Meetings and the live voice stay with the avatar host, reached with `--seat` and `--live`; opening one of those ends the
conversation the Mac holds, because both use port 8765.

