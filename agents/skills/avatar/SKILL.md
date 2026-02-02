---
name: avatar
description: Control the VTuber avatar system — speak through it with lip sync, change expressions, manage the avatar renderer and control server. Use when interacting with the avatar, making it speak, changing expressions, or troubleshooting avatar connection issues.
---

# Avatar Skill

Control the VTuber avatar system — a ChatVRM fork that provides a 3D anime avatar with lip sync, expressions, and WebSocket control.

## Quick Start

### Check if Avatar is Running

```bash
# Check control server
curl -s http://localhost:8766/status || echo "Control server not running"

# Check renderer
curl -s http://localhost:3000 > /dev/null && echo "Renderer running" || echo "Renderer not running"
```

### Start the System

```bash
# Project directory
cd ~/openclaw/projects/night-shift-2026-02-02/

# Terminal 1: Start control server
cd avatar-control-server && node server.js

# Terminal 2: Start renderer
cd avatar-renderer && npx next dev

# Terminal 3: Open browser
xdg-open http://localhost:3000
```

Wait for the green "Control Server Connected" badge in the browser UI.

### Speak Through Avatar (Quick Method)

```bash
~/.dotfiles/agents/skills/avatar/scripts/avatar-speak.sh "Hello, I'm Clever!" neutral
```

## WebSocket Commands

Connect to `ws://localhost:8765` and send JSON messages.

### 1. Identify (Required First)

```json
{
  "type": "identify",
  "role": "agent",
  "name": "clever"
}
```

**Response:** `{ "type": "identifyAck", "role": "agent", "name": "clever" }`

### 2. Speak

```json
{
  "type": "speak",
  "text": "Your message here",
  "emotion": "neutral"
}
```

**Response:** `{ "type": "speakAck", "duration": 5.2 }`

**Emotions:**
- `neutral` — **DEFAULT** — eyes open, natural expression
- `happy` — anime smile (eyes closed) — use sparingly
- `sad` — sad expression
- `angry` — angry expression
- `relaxed` — calm, relaxed
- `surprised` — surprised look

**Important:** Use `neutral` by default. `happy` closes the eyes, which looks unnatural for normal conversation.

### 3. Set Expression

```json
{
  "type": "setExpression",
  "name": "happy",
  "intensity": 1
}
```

Changes facial expression without speaking. Use same emotion names as above.

### 4. Set Idle Mode

```json
{
  "type": "setIdle",
  "mode": "breathing"
}
```

Sets the avatar to idle breathing animation.

### 5. Get Status

```json
{
  "type": "getStatus"
}
```

Returns current system state.

## Speaking Pattern (From Agent Code)

```bash
cd ~/openclaw/projects/night-shift-2026-02-02/avatar-control-server && node -e "
const WebSocket = require('ws');
const ws = new WebSocket('ws://localhost:8765');

ws.on('open', () => {
  // 1. Identify first
  ws.send(JSON.stringify({ 
    type: 'identify', 
    role: 'agent', 
    name: 'clever' 
  }));
  
  // 2. Wait a bit, then speak
  setTimeout(() => {
    ws.send(JSON.stringify({ 
      type: 'speak', 
      text: 'Your message here', 
      emotion: 'neutral' 
    }));
    
    // 3. Wait for TTS + playback to complete (~15s)
    setTimeout(() => { 
      ws.close(); 
      process.exit(0); 
    }, 15000);
  }, 1000);
});

ws.on('message', (d) => console.log('Rx:', d.toString()));
"
```

**Timing:**
- Wait 1s after identify before speaking
- Wait ~15s after speak command before closing (allows TTS generation + audio playback)

## Audio System

### TTS Engine
- **Engine:** edge-tts
- **Voice:** en-GB-RyanNeural (British male)
- **Output:** `/tmp/clever-avatar-tts/{id}/voice.mp3`

### Audio Flow
1. Agent sends `speak` command to control server (port 8765)
2. Control server runs edge-tts → generates MP3
3. Control server sends `startSpeaking` message to renderer with:
   - `audioUrl: "http://localhost:8766/audio/{id}/voice.mp3"`
   - `screenplay` (lip sync timing data)
4. Renderer fetches audio via HTTP (port 8766)
5. Renderer plays audio + lip sync in browser

**Critical:** Do NOT play audio via mpv or system audio. The browser handles playback. Playing it twice causes echo/duplication.

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Agent (Clever)                                 │
│  - Sends WebSocket commands                     │
│  - ws://localhost:8765                          │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  Control Server (avatar-control-server)         │
│  - WebSocket: port 8765                         │
│  - HTTP API: port 8766                          │
│  - Runs edge-tts for speech synthesis           │
│  - Serves audio files                           │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  Avatar Renderer (avatar-renderer)              │
│  - Next.js app: port 3000                       │
│  - ChatVRM fork (3D VRM model)                  │
│  - Renders avatar, plays audio, lip sync        │
└─────────────────────────────────────────────────┘
```

## Common Use Cases

### Make Avatar Speak

```bash
# Using the convenience script
~/.dotfiles/agents/skills/avatar/scripts/avatar-speak.sh "Hello world" neutral

# Or with a different emotion
~/.dotfiles/agents/skills/avatar/scripts/avatar-speak.sh "I'm so happy!" happy
```

### Change Expression Without Speaking

```bash
cd ~/openclaw/projects/night-shift-2026-02-02/avatar-control-server && node -e "
const WebSocket = require('ws');
const ws = new WebSocket('ws://localhost:8765');
ws.on('open', () => {
  ws.send(JSON.stringify({ type: 'identify', role: 'agent', name: 'clever' }));
  setTimeout(() => {
    ws.send(JSON.stringify({ type: 'setExpression', name: 'surprised', intensity: 1 }));
    setTimeout(() => { ws.close(); process.exit(0); }, 1000);
  }, 500);
});
"
```

### Check System Status

```bash
# Control server health
curl http://localhost:8766/status

# Renderer health
curl -I http://localhost:3000
```

## Troubleshooting

### Avatar Not Connecting

**Symptom:** Browser shows "Control Server Disconnected" (red badge)

**Check:**
1. Is control server running? `curl http://localhost:8766/status`
2. Is WebSocket port open? `ss -tlnp | grep 8765`
3. Check server logs in the terminal where `node server.js` is running

**Fix:** Restart control server:
```bash
cd ~/openclaw/projects/night-shift-2026-02-02/avatar-control-server
node server.js
```

### No Audio Playback

**Symptom:** Avatar lip syncs but no sound

**Check:**
1. Browser audio not muted
2. System audio not muted: `wpctl get-volume @DEFAULT_AUDIO_SINK@`
3. Audio file exists: `ls /tmp/clever-avatar-tts/`
4. Control server HTTP endpoint working: `curl http://localhost:8766/status`

**Fix:** The browser handles audio. Don't try to play via mpv.

### Avatar Lips Not Moving

**Symptom:** Audio plays but avatar doesn't lip sync

**Check:** Control server logs for TTS generation errors

**Common cause:** edge-tts failed to generate screenplay data

### Speak Command Hangs

**Symptom:** `speakAck` never received

**Check:**
1. Did you send `identify` first?
2. Is edge-tts installed? `which edge-tts`
3. Check control server logs for errors

**Fix:** Always send `identify` before any other command.

### Double Audio / Echo

**Symptom:** Hear the same audio twice

**Cause:** Playing audio via both browser AND system audio player (mpv)

**Fix:** Let the browser handle audio exclusively. Don't call mpv.

## Key Gotchas

### ⚠️ Emotion Defaults
- **Use `neutral` by default**, not `happy`
- `happy` closes eyes (anime smile) — looks weird for normal conversation
- Only use `happy` for emphasis or actual excitement

### ⚠️ Command Naming
- Server command is `setExpression`, not `updateExpression` or `expression`
- The renderer handles both server-side names (`startSpeaking`, `updateExpression`) AND client-side names (`speak`, `setExpression`)

### ⚠️ Timing
- Wait ~1s after `identify` before sending commands
- Wait ~15s after `speak` before closing WebSocket
  - Edge-TTS generation: ~2-5s
  - Audio playback: varies by text length
  - Buffer: 2-3s

### ⚠️ Connection Lifecycle
- Each WebSocket session must start with `identify`
- Close connection cleanly after task completes
- React strict mode causes double-mount — control server handles this with `destroyed` flag

### ⚠️ Audio Handling
- **Never play avatar audio via mpv** — causes duplication
- Browser plays audio automatically via `http://localhost:8766/audio/{id}/voice.mp3`
- The `viewer.model.speak()` method handles lip sync timing

## Virtual Camera (Not Yet Working)

**Status:** Configured but requires system reboot

### Configuration
- Module: v4l2loopback
- Device: `/dev/video10`
- Label: "Avatar Cam"

### Planned Pipeline
1. Browser canvas (avatar rendering)
2. Canvas stream → ffmpeg
3. ffmpeg → v4l2loopback device
4. v4l2loopback → Google Meet / OBS / etc.

### Current Block
- Kernel module not loaded (needs reboot)
- Check after reboot: `ls -l /dev/video10`

### Future Usage
Once enabled, the avatar will be available as a virtual webcam in Google Meet and other video conferencing tools.

## File Locations

```
~/openclaw/projects/night-shift-2026-02-02/
├── avatar-control-server/
│   ├── server.js              # WebSocket + HTTP server
│   └── package.json
├── avatar-renderer/
│   ├── src/
│   │   └── lib/avatarClient.ts  # WebSocket client
│   ├── public/
│   │   └── AvatarSample_B.vrm   # 3D model
│   └── package.json
└── README.md

/tmp/clever-avatar-tts/        # TTS output directory
└── {id}/
    └── voice.mp3              # Generated audio files

~/.dotfiles/agents/skills/avatar/
├── SKILL.md                   # This file
├── scripts/
│   └── avatar-speak.sh        # Convenience script
└── references/
    └── architecture.md        # Detailed architecture docs
```

## Integration with Clever Agent

### When to Use Avatar

**Good for:**
- Presentations or demos
- Storytelling (more engaging than text)
- Video calls (when virtual camera is enabled)
- "Storytime" moments
- Showing personality through expressions

**Not needed for:**
- Quick responses in chat
- Routine heartbeats
- File operations
- Background tasks

### From Agent Code

```javascript
// Quick helper function to speak through avatar
async function avatarSpeak(text, emotion = 'neutral') {
  const { exec } = require('child_process');
  const script = '~/.dotfiles/agents/skills/avatar/scripts/avatar-speak.sh';
  
  return new Promise((resolve, reject) => {
    exec(`${script} "${text}" ${emotion}`, (error, stdout, stderr) => {
      if (error) reject(error);
      else resolve(stdout);
    });
  });
}

// Usage
await avatarSpeak("Hello, I'm Clever!", "neutral");
```

### Decision Tree

```
Need to communicate with Lucas?
├─ Is avatar system running?
│  ├─ Yes: Consider using avatar for:
│  │  ├─ Long explanations (> 2 paragraphs)
│  │  ├─ Stories or narratives
│  │  ├─ Demonstrations
│  │  └─ Emotional moments (with appropriate expression)
│  └─ No: Use text chat (Telegram, etc.)
└─ Avatar not needed? Use text
```

## References

For detailed architecture, message flow diagrams, and deep troubleshooting:
→ See `references/architecture.md`
