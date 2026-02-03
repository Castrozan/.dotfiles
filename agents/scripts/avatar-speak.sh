#!/usr/bin/env bash
# Send text to the avatar system for speech synthesis
#
# Usage:
#   avatar-speak.sh "Hello world"
#   avatar-speak.sh "I'm excited!" happy
#   avatar-speak.sh "Hello Meet!" neutral mic
#
# Arguments:
#   $1 - Text to speak (required)
#   $2 - Emotion (optional, default: neutral)
#        Valid: neutral, happy, sad, angry, relaxed, surprised
#   $3 - Output (optional, default: speakers)
#        speakers = room audio, mic = virtual mic (Meet), both = both

set -euo pipefail

TEXT="${1:?Usage: avatar-speak.sh 'text' [emotion] [output]}"
EMOTION="${2:-neutral}"
OUTPUT="${3:-speakers}"

case "$EMOTION" in
  neutral|happy|sad|angry|relaxed|surprised)
    ;;
  *)
    echo "Error: Invalid emotion '$EMOTION'" >&2
    echo "Valid emotions: neutral, happy, sad, angry, relaxed, surprised" >&2
    exit 1
    ;;
esac

case "$OUTPUT" in
  speakers|mic|both)
    ;;
  *)
    echo "Error: Invalid output '$OUTPUT'" >&2
    echo "Valid outputs: speakers (room), mic (Meet), both" >&2
    exit 1
    ;;
esac

SERVER_DIR="@homePath@/@workspacePath@/avatar/control-server"

if [[ ! -d "$SERVER_DIR" ]]; then
  echo "Error: Control server directory not found: $SERVER_DIR" >&2
  exit 1
fi

if ! curl -s http://localhost:8766/health > /dev/null 2>&1; then
  echo "Error: Control server not running (port 8766 not responding)" >&2
  echo "Start it with: systemctl --user start avatar-control-server" >&2
  exit 1
fi

cd "$SERVER_DIR" && node -e "
const WebSocket = require('ws');
const ws = new WebSocket('ws://localhost:8765');

ws.on('error', (err) => {
  console.error('WebSocket error:', err.message);
  process.exit(1);
});

ws.on('open', () => {
  ws.send(JSON.stringify({
    type: 'identify',
    role: 'agent',
    name: '@agentName@'
  }));

  setTimeout(() => {
    ws.send(JSON.stringify({
      type: 'speak',
      text: process.argv[1],
      emotion: process.argv[2],
      output: process.argv[3]
    }));
  }, 500);
});

ws.on('message', (data) => {
  const msg = JSON.parse(data.toString());
  console.log('Received:', msg.type);

  if (msg.type === 'speakAck') {
    const duration = msg.duration || 10;
    const bufferTime = 2000;
    const waitTime = (duration * 1000) + bufferTime;

    console.log(\`Speaking for \${duration.toFixed(1)}s, waiting \${(waitTime/1000).toFixed(1)}s total...\`);

    setTimeout(() => {
      console.log('Done!');
      ws.close();
      process.exit(0);
    }, waitTime);
  }
});
" "$TEXT" "$EMOTION" "$OUTPUT"
