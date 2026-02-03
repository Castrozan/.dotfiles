#!/usr/bin/env bash
# Setup virtual audio devices for avatar TTS pipeline
# Creates a virtual speaker sink and virtual microphone source
# TTS audio -> AvatarSpeaker -> AvatarMic (monitor) -> Meet/Zoom/etc

set -euo pipefail

echo "Setting up virtual audio devices for Avatar..."

# Create virtual speaker sink (TTS audio goes here)
echo "Creating AvatarSpeaker sink..."
SPEAKER_ID=$(pactl load-module module-null-sink \
  sink_name=AvatarSpeaker \
  sink_properties=device.description="Avatar_Speaker")
echo "  AvatarSpeaker created (module ID: $SPEAKER_ID)"

# Create virtual mic source
echo "Creating AvatarMic source..."
MIC_ID=$(pactl load-module module-null-sink \
  media.class=Audio/Source/Virtual \
  sink_name=AvatarMic \
  sink_properties=device.description="Avatar_Mic")
echo "  AvatarMic created (module ID: $MIC_ID)"

sleep 1

# Link speaker monitor to virtual mic
echo "Linking AvatarSpeaker monitor to AvatarMic..."
pw-link AvatarSpeaker:monitor_FL AvatarMic:input_FL 2>/dev/null || echo "  Left channel link failed (may already exist)"
pw-link AvatarSpeaker:monitor_FR AvatarMic:input_FR 2>/dev/null || echo "  Right channel link failed (may already exist)"

echo ""
echo "Virtual devices ready!"
echo ""
echo "Usage:"
echo "  1. Play TTS audio to 'Avatar_Speaker' sink:"
echo "     paplay --device=AvatarSpeaker audio.wav"
echo "     mpv --audio-device=pipewire/AvatarSpeaker audio.mp3"
echo ""
echo "  2. Select 'Avatar_Mic' as microphone input in Meet/Zoom/Teams"
echo ""
echo "To remove devices:"
echo "  pactl unload-module $SPEAKER_ID"
echo "  pactl unload-module $MIC_ID"
