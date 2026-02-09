#!/usr/bin/env bash
set -euo pipefail

GATEWAY_URL="http://localhost:@gatewayPort@"
GATEWAY_TOKEN="$(cat /run/agenix/openclaw-gateway-token 2>/dev/null || echo "")"
TTS_VOICE="@ttsVoice@"

whisp-away stop --clipboard true 2>/dev/null

TRANSCRIPTION="$(wl-paste 2>/dev/null || true)"

if [[ -z "$TRANSCRIPTION" ]]; then
  notify-send "Hey Clever" "No speech detected" 2>/dev/null || true
  exit 0
fi

notify-send "Hey Clever" "$TRANSCRIPTION" 2>/dev/null || true

RESPONSE=$(curl -s --max-time 120 "$GATEWAY_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GATEWAY_TOKEN" \
  -H "x-clawdbot-agent-id: main" \
  -d "$(jq -n --arg text "$TRANSCRIPTION" '{
    model: "@model@",
    user: "voice-@agentName@",
    messages: [{
      role: "user",
      content: ("[Voice input from microphone — respond concisely for TTS playback. Match the user'\''s language (English or Portuguese).]\n\n" + $text)
    }]
  }')" | jq -r '.choices[0].message.content // "Sorry, I could not process that."')

TMPFILE=$(mktemp /tmp/hey-clever-XXXXXX.mp3)
trap 'rm -f "$TMPFILE"' EXIT

edge-tts --text "$RESPONSE" --voice "$TTS_VOICE" --write-media "$TMPFILE" 2>/dev/null

wpctl set-mute @DEFAULT_AUDIO_SINK@ 0 2>/dev/null || true
mpv --no-video --ao=pipewire "$TMPFILE" 2>/dev/null
