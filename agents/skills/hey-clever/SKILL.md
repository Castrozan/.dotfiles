---
name: hey-clever
description: Always-on voice assistant with keyword detection, Whisper transcription, and TTS response. Use when setting up, starting, or troubleshooting the voice assistant.
---

# Hey Clever -- Always-On Voice Assistant

Listens for a keyword ("Clever"), records the spoken command, transcribes with Whisper, sends to the OpenClaw gateway, and plays back the TTS response.

## Architecture

```
Phase 1 (always running): Silero VAD -> buffer -> Whisper tiny -> keyword check
Phase 2 (on activation): Beep -> record until silence -> Whisper small -> gateway -> TTS -> play
```

## Scripts

### `hey-clever.py`
Main voice assistant loop. Requires a Python venv with dependencies.

```bash
python3 scripts/hey-clever.py --debug          # Run with debug logging
python3 scripts/hey-clever.py --list-devices   # List audio devices
python3 scripts/hey-clever.py --device 3       # Use specific input device
```

### `hey-clever-setup.sh`
One-time setup: creates venv, installs dependencies, installs systemd service.

```bash
bash scripts/hey-clever-setup.sh
```

### `faster-whisper.sh`
Standalone Whisper transcription wrapper for media files.

```bash
scripts/faster-whisper.sh input.wav --model small --output_dir /tmp/whisper-out
```

## Systemd Service

```bash
systemctl --user start hey-clever
systemctl --user stop hey-clever
systemctl --user enable hey-clever
journalctl --user -u hey-clever -f
```
