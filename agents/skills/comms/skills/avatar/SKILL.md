---
name: avatar
description: Control the VTuber avatar — start and stop the renderer, virtual camera, and virtual mic; speak through the avatar with lip sync; respond to voice conversation when hey-bot is active.
---

<scripts>
All scripts live at @homePath@/@workspacePath@/skills/comms/skills/avatar/scripts/. Start all services with start-avatar.sh (opens visible browser). Stop with stop-avatar.sh. Speak with avatar-speak.sh or avatar-speak-multi.sh — run --help for usage.
</scripts>

<voice_conversation_mode>
When avatar is active with hey-bot daemon, set up a cron job polling transcription logs every 30s. On events: read tail of the transcription log, filter out noise (nonsensical text, self-TTS re-transcription, entries older than 60s), respond to genuine human speech via avatar-speak.sh. Keep responses concise. Respond via avatar, not Telegram.
</voice_conversation_mode>

<traps>
Virtual camera not in Meet: restart Meet (Chrome enumerates devices at join time, not dynamically). No audio in Meet: check pactl for AvatarMic sink, use "mic" output mode. Speak hangs: control server must be running (check health endpoint). Renderer won't start: npm install in the renderer directory.
</traps>
