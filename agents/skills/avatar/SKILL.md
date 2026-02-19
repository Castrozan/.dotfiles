---
name: avatar
description: Control the VTuber avatar with lip sync and expressions. Use when user asks to speak through the avatar, change facial expressions, route audio to speakers or Google Meet, or animate the character during presentations or streams.
---

<scripts>
All scripts live at @homePath@/@workspacePath@/skills/avatar/scripts/. Start all services with start-avatar.sh (opens visible browser). Stop with stop-avatar.sh.
</scripts>

<speaking>
Single segment: avatar-speak.sh "text" [emotion] [output]. Multi-segment: avatar-speak-multi.sh "emotion:text" "emotion:text" [output]. Output defaults to speakers. Append "mic" for virtual mic (calls) or "both" for speakers + mic.
</speaking>

<emotions>
Available: neutral (default), happy, sad, angry, relaxed, surprised.
</emotions>

<audio_output>
speakers: system sink for room audio. mic: AvatarMic virtual sink for Meet/calls. both: speakers + mic simultaneously.
</audio_output>

<voice_conversation_mode>
When avatar is active with hey-bot daemon, set up a cron job polling transcription logs every 30s. On hey-bot-monitor events: read tail -15 of the transcription log, filter out noise (nonsensical text, self-TTS re-transcription, entries older than 60s), respond to genuine human speech via avatar-speak.sh. Keep responses concise (2-3 sentences). Respond via avatar, not Telegram.
</voice_conversation_mode>

<ports>
8765: WebSocket control. 8766: HTTP audio + health. 3000: Renderer browser. /dev/video*: Virtual camera (auto-detected).
</ports>

<troubleshooting>
Can't see avatar: start-avatar.sh opens --headed. No audio in Meet: check pactl for AvatarMic sink, use output "mic". Speak hangs: control server must be running (curl localhost:8766/health). Virtual camera not in Meet: restart Meet (Chrome enumerates at join). Renderer won't start: npm install in the renderer directory.
</troubleshooting>
