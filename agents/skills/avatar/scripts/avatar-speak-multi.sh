#!/usr/bin/env bash
# Speak multiple segments with different emotions
# Usage: avatar-speak-multi.sh "emotion:text" "emotion:text" ...
# Example: avatar-speak-multi.sh "happy:Hello!" "surprised:Really?" "happy:Great!"
#
# Output destination (optional last arg): speakers (default), mic, both

set -euo pipefail

# Parse segments and output target
OUTPUT="speakers"
SEGMENTS=()

for arg in "$@"; do
  if [[ "$arg" == "speakers" || "$arg" == "mic" || "$arg" == "both" ]]; then
    OUTPUT="$arg"
  else
    SEGMENTS+=("$arg")
  fi
done

if [[ ${#SEGMENTS[@]} -eq 0 ]]; then
  echo "Usage: avatar-speak-multi.sh 'emotion:text' ['emotion:text' ...] [output]" >&2
  echo "  Emotions: happy, neutral, surprised, relaxed, sad, angry" >&2
  echo "  Output: speakers (default), mic, both" >&2
  echo "" >&2
  echo "Example:" >&2
  echo "  avatar-speak-multi.sh 'happy:Hello!' 'surprised:Really?' 'happy:Great!'" >&2
  exit 1
fi

# Parse each segment into emotion:text pairs
JS_SEGMENTS=""
for seg in "${SEGMENTS[@]}"; do
  if [[ "$seg" =~ ^([a-z]+):(.*)$ ]]; then
    EMOTION="${BASH_REMATCH[1]}"
    TEXT="${BASH_REMATCH[2]}"
    # Validate emotion
    case "$EMOTION" in
      neutral|happy|sad|angry|relaxed|surprised) ;;
      *) echo "Invalid emotion: $EMOTION" >&2; exit 1 ;;
    esac
    JS_SEGMENTS="$JS_SEGMENTS    { text: \"$TEXT\", emotion: \"$EMOTION\" },\n"
  else
    echo "Invalid format: '$seg' (expected emotion:text)" >&2
    exit 1
  fi
done

SERVER_DIR="@homePath@/@workspacePath@/skills/avatar/control-server"

if [[ ! -d "$SERVER_DIR" ]]; then
  echo "Error: Control server directory not found: $SERVER_DIR" >&2
  exit 1
fi

if ! curl -s http://localhost:8766/health > /dev/null 2>&1; then
  echo "Error: Control server not running" >&2
  echo "Start with: systemctl --user start avatar-control-server" >&2
  exit 1
fi

cd "$SERVER_DIR" && node -e "
const WebSocket = require('ws');
const segments = [
$JS_SEGMENTS];
const output = '$OUTPUT';

const ws = new WebSocket('ws://localhost:8765');

ws.on('error', (err) => {
  console.error('WebSocket error:', err.message);
  process.exit(1);
});

ws.on('open', () => {
  ws.send(JSON.stringify({ type: 'identify', role: 'agent', name: '@agentName@' }));
  setTimeout(() => speakSegment(0), 600);
});

function speakSegment(index) {
  if (index >= segments.length) {
    console.log('Done!');
    setTimeout(() => ws.close(), 500);
    return;
  }
  
  const seg = segments[index];
  console.log('[✓]', seg.emotion + ':', seg.text.substring(0, 40) + (seg.text.length > 40 ? '...' : ''));
  
  ws.send(JSON.stringify({
    type: 'speak',
    text: seg.text,
    emotion: seg.emotion,
    output: output
  }));
  
  // Wait for speakAck, then estimate duration + buffer
  let ackReceived = false;
  const next = () => {
    if (!ackReceived) {
      ackReceived = true;
      // Rough estimate: 150ms per word + 1500ms buffer
      const wordCount = seg.text.split(/\\s+/).length;
      const waitTime = Math.max(2000, wordCount * 150 + 1000);
      setTimeout(() => speakSegment(index + 1), waitTime);
    }
  };
  
  const handleMsg = (data) => {
    const msg = JSON.parse(data.toString());
    if (msg.type === 'speakAck') {
      ws.off('message', handleMsg);
      next();
    }
    if (msg.type === 'error') {
      console.error('Speak error:', msg.error);
    }
  };
  ws.on('message', handleMsg);
}
"
