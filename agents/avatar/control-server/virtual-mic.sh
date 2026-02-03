#!/usr/bin/env bash
# Virtual Microphone Pipeline
# Creates a PipeWire virtual microphone that captures audio from the avatar browser
#
# Usage: ./virtual-mic.sh [start|stop|status]

export XDG_RUNTIME_DIR=/run/user/1000

ACTION="${1:-start}"

SINK_NAME="avatar-virtual-mic"
SINK_DESC="Avatar Virtual Microphone"

case "$ACTION" in
  start)
    echo "🎤 Creating virtual microphone sink..."
    
    # Create a virtual sink (acts as both sink and source)
    # Audio sent to this sink appears as a microphone source
    pactl load-module module-null-sink sink_name="$SINK_NAME" sink_properties=device.description="$SINK_DESC" 2>/dev/null
    
    if [ $? -eq 0 ]; then
      echo "✅ Virtual mic created: $SINK_NAME"
      echo "   Sink (output): $SINK_NAME"
      echo "   Source (mic):   ${SINK_NAME}.monitor"
      echo ""
      echo "📋 To use in Google Meet:"
      echo "   1. Open Meet settings → Audio"
      echo "   2. Select '${SINK_DESC}' as microphone"
      echo ""
      echo "📋 To route browser audio to virtual mic:"
      echo "   Use pavucontrol or: pw-link <browser-output> ${SINK_NAME}:playback_FL"
    else
      echo "⚠️  Sink may already exist. Checking..."
      pactl list short sinks | grep "$SINK_NAME" && echo "✅ Already running"
    fi
    ;;
    
  stop)
    echo "🛑 Removing virtual microphone..."
    MODULE_ID=$(pactl list short modules | grep "$SINK_NAME" | awk '{print $1}')
    if [ -n "$MODULE_ID" ]; then
      pactl unload-module "$MODULE_ID"
      echo "✅ Virtual mic removed"
    else
      echo "⚠️  Virtual mic not found"
    fi
    ;;
    
  status)
    echo "🔍 Virtual mic status:"
    pactl list short sinks | grep "$SINK_NAME"
    if [ $? -eq 0 ]; then
      echo "✅ Active"
      echo ""
      echo "Monitor source:"
      pactl list short sources | grep "$SINK_NAME"
    else
      echo "❌ Not active"
    fi
    ;;
    
  *)
    echo "Usage: $0 [start|stop|status]"
    exit 1
    ;;
esac
