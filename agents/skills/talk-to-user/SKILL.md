---
name: talk-to-user
description: Speak to the user via PC speakers or send voice messages. Use when delivering audio briefings, status updates, alerts, or when the user requests spoken output.
---

<voice_config>
Each agent has a distinct voice configured via Nix. Read voice config from ~/@workspacePath@/tts.json. Default engine: edge-tts (Microsoft Edge, free, no API key).
</voice_config>

<when_to_speak>
Speak for: briefings, alerts, status updates, user requests. Stay silent for: routine housekeeping, trivial confirmations (text is fine for "done"), late night unless alerting. Never speak passwords, tokens, or sensitive data aloud.
</when_to_speak>

<conduct>
Be brief — 30 seconds max for status, 2 minutes max for briefings. Lead with the point. No filler phrases. Natural tone like a colleague. One topic per utterance. Context first for alerts: "The gateway went down 5 minutes ago — I restarted it, it's back."
</conduct>

<playback_trap>
Always use background: true for mpv — exec's 10s timeout sends SIGKILL mid-playback otherwise. Check volume before playing, unmute and set level via wpctl every time (XDG_RUNTIME_DIR=/run/user/1000).
</playback_trap>

<music_ducking>
If music is playing, lower the media stream volume before TTS, play at full system volume, then restore. Find stream IDs in wpctl status under Streams.
</music_ducking>

<voice_messages>
Generate audio with tts tool, then send via message tool to WhatsApp or Telegram with filePath and asVoice: true.
</voice_messages>

<troubleshooting>
No sound: check wpctl status for correct default sink and volume > 0. SIGKILL at ~10s: forgot background: true on mpv. Garbled audio: restart pipewire. Wrong voice: check tts.json config.
</troubleshooting>
