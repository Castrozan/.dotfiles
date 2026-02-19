---
name: talk-to-user
description: Speak to the user via PC speakers or send voice messages. Use when delivering audio briefings, status updates, alerts, or when the user requests spoken output.
---

<voice_config>
Each agent has a distinct voice configured via Nix (openclaw.tts option). Read voice config from ~/@workspacePath@/tts.json. Default engine: edge-tts (Microsoft Edge, free, no API key).
</voice_config>

<when_to_speak>
Speak for: briefings, alerts, status updates, user requests ("tell me about...", "read this to me"). Stay silent for: routine housekeeping, trivial confirmations (text is fine for "done"), late night unless alerting. Never speak passwords, tokens, or sensitive data aloud.
</when_to_speak>

<conduct>
Be brief — 30 seconds max for status, 2 minutes max for briefings. Lead with the point. No filler phrases. Natural tone like a colleague. One topic per utterance. Context first for alerts: "The gateway went down 5 minutes ago — I restarted it, it's back."
</conduct>

<pc_speakers_flow>
Generate audio with tts tool, then unmute and set volume via wpctl (XDG_RUNTIME_DIR=/run/user/1000), then play with mpv --no-video --ao=pulse using background: true and yieldMs: 20000. Always background: true for mpv — exec's 10s timeout sends SIGKILL mid-playback otherwise. Check volume before playing, unmute and set level every time.
</pc_speakers_flow>

<music_ducking>
If music is playing, lower the media stream volume via wpctl set-volume on the stream ID, play TTS at full system volume, then restore the stream volume. Find stream IDs in wpctl status under Streams.
</music_ducking>

<voice_messages>
Generate audio with tts tool, then send via message tool to WhatsApp (target: 554899768269) or Telegram (target: 8128478854) with filePath and asVoice: true.
</voice_messages>

<custom_voice>
For custom voices: edge-tts --voice "en-GB-RyanNeural" --text "Hello" --write-media /tmp/custom-voice.mp3, then play with mpv as above. List available voices with edge-tts --list-voices.
</custom_voice>

<troubleshooting>
No sound: check wpctl status for correct default sink and volume > 0. SIGKILL at ~10s: forgot background: true on mpv. Garbled audio: restart pipewire (systemctl --user restart pipewire). Wrong voice: check edge-tts --list-voices.
</troubleshooting>
