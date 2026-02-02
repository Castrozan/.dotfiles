#!/usr/bin/env bash
#
# avatar-speak.sh - Send text to the avatar system for speech synthesis
#
# Usage:
#   avatar-speak.sh "Hello world"
#   avatar-speak.sh "I'm excited!" happy
#
# Arguments:
#   $1 - Text to speak (required)
#   $2 - Emotion (optional, default: neutral)
#        Valid: neutral, happy, sad, angry, relaxed, surprised
#
# Requirements:
#   - Control server running on ws://localhost:8765
#   - Node.js with WebSocket support
#

set -euo pipefail

# Parse arguments
TEXT="${1:?Usage: avatar-speak.sh 'text' [emotion]}"
EMOTION="${2:-neutral}"

# Validate emotion
case "$EMOTION" in
  neutral|happy|sad|angry|relaxed|surprised)
    ;;
  *)
    echo "Error: Invalid emotion '$EMOTION'" >&2
    echo "Valid emotions: neutral, happy, sad, angry, relaxed, surprised" >&2
    exit 1
    ;;
esac

# Project directory
SERVER_DIR="$HOME/openclaw/projects/night-shift-2026-02-02/avatar-control-server"

# Check if control server directory exists
if [[ ! -d "$SERVER_DIR" ]]; then
  echo "Error: Control server directory not found: $SERVER_DIR" >&2
  exit 1
fi

# Check if control server is running
if ! curl -s http://localhost:8766/status > /dev/null 2>&1; then
  echo "Error: Control server not running (port 8766 not responding)" >&2
  echo "Start it with: cd $SERVER_DIR && node server.js" >&2
  exit 1
fi

# Send speak command via WebSocket
cd "$SERVER_DIR" && node -e "
const WebSocket = require('ws');
const ws = new WebSocket('ws://localhost:8765');

ws.on('error', (err) => {
  console.error('WebSocket error:', err.message);
  process.exit(1);
});

ws.on('open', () => {
  // Step 1: Identify as agent
  ws.send(JSON.stringify({ 
    type: 'identify', 
    role: 'agent', 
    name: 'clever' 
  }));
  
  // Step 2: Wait a bit, then send speak command
  setTimeout(() => {
    ws.send(JSON.stringify({ 
      type: 'speak', 
      text: process.argv[1], 
      emotion: process.argv[2] 
    }));
  }, 500);
});

ws.on('message', (data) => {
  const msg = JSON.parse(data.toString());
  
  // Log received messages
  console.log('Received:', msg.type);
  
  // When we get speakAck, wait for duration + buffer, then exit
  if (msg.type === 'speakAck') {
    const duration = msg.duration || 10;  // Default 10s if no duration
    const bufferTime = 2000;               // 2s buffer for processing
    const waitTime = (duration * 1000) + bufferTime;
    
    console.log(\`Speaking for \${duration.toFixed(1)}s, waiting \${(waitTime/1000).toFixed(1)}s total...\`);
    
    setTimeout(() => {
      console.log('Done!');
      ws.close();
      process.exit(0);
    }, waitTime);
  }
});
" "$TEXT" "$EMOTION"
