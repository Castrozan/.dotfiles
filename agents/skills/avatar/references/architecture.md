# Avatar System Architecture

Detailed technical documentation for the VTuber avatar system.

## System Overview

The avatar system consists of three layers:

```
┌────────────────────────────────────────────────────────────┐
│  Layer 1: Agent (Clever)                                   │
│  - Runs in OpenClaw environment                            │
│  - Sends WebSocket commands to control server              │
│  - Does NOT handle audio playback                          │
└─────────────────────────┬──────────────────────────────────┘
                          │ WebSocket (ws://localhost:8765)
                          │ JSON messages
                          ▼
┌────────────────────────────────────────────────────────────┐
│  Layer 2: Control Server (avatar-control-server)           │
│  - Node.js server with WebSocket (port 8765)               │
│  - HTTP API (port 8766) for audio serving                  │
│  - TTS generation via edge-tts                             │
│  - Message routing and state management                    │
└─────────────────────────┬──────────────────────────────────┘
                          │ WebSocket (outbound)
                          │ HTTP (audio files)
                          ▼
┌────────────────────────────────────────────────────────────┐
│  Layer 3: Avatar Renderer (avatar-renderer)                │
│  - Next.js application (port 3000)                         │
│  - ChatVRM fork (3D VRM model rendering)                   │
│  - Audio playback + lip sync                               │
│  - Facial expression control                               │
└────────────────────────────────────────────────────────────┘
```

## Component Details

### Layer 1: Agent (Clever)

**Purpose:** High-level interface for avatar control

**Responsibilities:**
- Construct and send WebSocket commands
- Manage conversation flow
- Decide when to use avatar vs. text chat

**Does NOT:**
- Handle audio playback (that's browser's job)
- Directly control TTS
- Manage avatar state

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8765');
```

**Lifecycle:**
1. Open WebSocket connection
2. Send `identify` message
3. Wait for `identifyAck`
4. Send command(s)
5. Wait for response(s)
6. Close connection cleanly

### Layer 2: Control Server

**Location:** `~/openclaw/projects/night-shift-2026-02-02/avatar-control-server/`

**Ports:**
- WebSocket: 8765 (command channel)
- HTTP: 8766 (audio file serving + status endpoint)

**Key File:** `server.js`

**Responsibilities:**
1. **WebSocket Server** (port 8765)
   - Accept connections from agents and renderers
   - Route messages between connected clients
   - Handle identification and session management

2. **HTTP Server** (port 8766)
   - Serve generated audio files: `/audio/{id}/voice.mp3`
   - Health check endpoint: `/status`
   - CORS enabled for browser access

3. **TTS Generation**
   - Run `edge-tts` CLI for speech synthesis
   - Voice: `en-GB-RyanNeural`
   - Generate screenplay (lip sync timing data)
   - Save to `/tmp/clever-avatar-tts/{id}/voice.mp3`

4. **Message Processing**
   - Validate incoming messages
   - Transform agent commands → renderer commands
   - Example: `speak` → generate TTS → `startSpeaking` with audioUrl

**Message Flow Example (Speak Command):**
```
Agent → Server: { type: 'speak', text: '...', emotion: 'neutral' }
                      ↓
                [Run edge-tts]
                      ↓
        [Generate audio + screenplay]
                      ↓
Server → Renderer: { type: 'startSpeaking', 
                     audioUrl: 'http://localhost:8766/audio/xyz/voice.mp3',
                     screenplay: [...] }
                      ↓
Server → Agent: { type: 'speakAck', duration: 5.2 }
```

**State Management:**
- Tracks connected agents and renderers
- Maintains session IDs
- Handles disconnections gracefully

### Layer 3: Avatar Renderer

**Location:** `~/openclaw/projects/night-shift-2026-02-02/avatar-renderer/`

**Port:** 3000 (Next.js dev server)

**Technology:**
- Next.js (React framework)
- Three.js (3D rendering)
- ChatVRM (VRM model library, forked)
- Web Audio API (audio playback)

**Key Files:**
- `src/lib/avatarClient.ts` - WebSocket client for control server
- `src/components/viewer.tsx` - Main 3D viewer component
- `public/AvatarSample_B.vrm` - 3D VRM model file

**Responsibilities:**
1. **WebSocket Client**
   - Connect to control server (ws://localhost:8765)
   - Identify as `role: 'renderer'`
   - Listen for commands: `startSpeaking`, `updateExpression`, `setIdle`

2. **3D Rendering**
   - Load and display VRM model
   - Render to canvas at 60fps
   - Camera positioning and lighting

3. **Audio Playback**
   - Fetch audio file from `http://localhost:8766/audio/{id}/voice.mp3`
   - Decode audio via Web Audio API
   - Play audio through browser (NOT system audio)

4. **Lip Sync**
   - Parse screenplay data (phoneme timing)
   - Animate mouth shapes (VRM morph targets)
   - Sync with audio playback frame-by-frame

5. **Facial Expressions**
   - Map emotion names to VRM expression presets
   - Blend between expressions smoothly
   - Idle animations (breathing, blinking)

**Connection Handling:**

The renderer has a critical issue with React strict mode causing double-mounting. This is handled with a `destroyed` flag:

```typescript
// avatarClient.ts pattern
let destroyed = false;

function connectAvatarWS() {
  if (destroyed) return null;
  
  const ws = new WebSocket('ws://localhost:8765');
  
  // ... setup handlers ...
  
  return ws;
}

// Cleanup on unmount
useEffect(() => {
  return () => {
    destroyed = true;
    ws?.close();
  };
}, []);
```

This prevents zombie connections when React strict mode mounts components twice.

## Message Protocol

### Agent → Control Server

#### 1. Identify (Required First)

```json
{
  "type": "identify",
  "role": "agent",
  "name": "clever"
}
```

**Response:**
```json
{
  "type": "identifyAck",
  "role": "agent",
  "name": "clever"
}
```

#### 2. Speak

```json
{
  "type": "speak",
  "text": "Hello, I'm Clever!",
  "emotion": "neutral"
}
```

**Server Processing:**
1. Validates message
2. Generates unique ID
3. Runs edge-tts:
   ```bash
   edge-tts --voice en-GB-RyanNeural \
            --text "Hello, I'm Clever!" \
            --write-media /tmp/clever-avatar-tts/{id}/voice.mp3 \
            --write-subtitles /tmp/clever-avatar-tts/{id}/screenplay.json
   ```
4. Parses screenplay for lip sync timing
5. Sends to renderer (see next section)

**Response to Agent:**
```json
{
  "type": "speakAck",
  "duration": 5.2,
  "audioId": "xyz123"
}
```

The `duration` field is critical — agent should wait `(duration * 1000) + 2000` milliseconds before closing connection to allow full playback.

#### 3. Set Expression

```json
{
  "type": "setExpression",
  "name": "happy",
  "intensity": 1
}
```

Changes expression without speaking. Forwarded directly to renderer.

#### 4. Set Idle

```json
{
  "type": "setIdle",
  "mode": "breathing"
}
```

Returns avatar to idle state with breathing animation.

#### 5. Get Status

```json
{
  "type": "getStatus"
}
```

**Response:**
```json
{
  "type": "statusResponse",
  "agents": 1,
  "renderers": 1,
  "speaking": false
}
```

### Control Server → Renderer

#### 1. Identify

Renderer sends on connection:
```json
{
  "type": "identify",
  "role": "renderer"
}
```

**Response:**
```json
{
  "type": "identifyAck",
  "role": "renderer"
}
```

Plus an `initialState` message with current system state.

#### 2. Start Speaking

```json
{
  "type": "startSpeaking",
  "audioUrl": "http://localhost:8766/audio/xyz123/voice.mp3",
  "emotion": "neutral",
  "screenplay": [
    { "time": 0, "phoneme": "sil" },
    { "time": 0.1, "phoneme": "h" },
    { "time": 0.2, "phoneme": "e" },
    ...
  ]
}
```

**Renderer Processing:**
1. Fetch audio file via HTTP
2. Decode audio via Web Audio API
3. Play audio through browser
4. Animate mouth shapes based on `screenplay` timing
5. Apply `emotion` as facial expression

**CRITICAL:** Renderer plays audio. Agent/server should NOT play audio via mpv or any system player. That causes duplication/echo.

#### 3. Update Expression

```json
{
  "type": "updateExpression",
  "name": "surprised",
  "intensity": 1
}
```

Same as `setExpression` from agent perspective, but server uses `updateExpression` when forwarding to renderer.

#### 4. Set Idle

```json
{
  "type": "setIdle",
  "mode": "breathing"
}
```

Return to idle breathing animation.

## Audio Pipeline

### TTS Generation (Control Server)

**Tool:** edge-tts (Microsoft Edge TTS)

**Voice:** `en-GB-RyanNeural`
- British English accent
- Male voice
- Clear pronunciation
- Good for technical content

**Process:**
```bash
# Create output directory
mkdir -p /tmp/clever-avatar-tts/{id}/

# Generate audio + screenplay
edge-tts \
  --voice en-GB-RyanNeural \
  --text "Your text here" \
  --write-media /tmp/clever-avatar-tts/{id}/voice.mp3 \
  --write-subtitles /tmp/clever-avatar-tts/{id}/screenplay.json

# Output files:
# - voice.mp3: Audio file
# - screenplay.json: Phoneme timing for lip sync
```

**Screenplay Format:**
```json
[
  { "time": 0, "phoneme": "sil" },      // silence
  { "time": 0.1, "phoneme": "h" },      // H sound
  { "time": 0.2, "phoneme": "e" },      // E sound
  { "time": 0.3, "phoneme": "l" },      // L sound
  ...
]
```

### Audio Serving (Control Server)

**Endpoint:** `http://localhost:8766/audio/{id}/voice.mp3`

**CORS Enabled:** Yes (required for browser fetch)

**File Location:** `/tmp/clever-avatar-tts/{id}/voice.mp3`

### Audio Playback (Renderer)

**Technology:** Web Audio API

**Flow:**
1. Receive `startSpeaking` message with `audioUrl`
2. Fetch audio file:
   ```javascript
   const response = await fetch(audioUrl);
   const arrayBuffer = await response.arrayBuffer();
   ```
3. Decode audio:
   ```javascript
   const audioContext = new AudioContext();
   const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
   ```
4. Play audio + lip sync:
   ```javascript
   viewer.model.speak(audioBuffer, screenplay);
   ```

The `viewer.model.speak()` method handles:
- Audio playback via Web Audio API
- Lip sync animation based on screenplay
- Mouth shape morphing (VRM blend shapes)
- Frame-by-frame synchronization

**Audio Output:** Browser's default audio output (same as watching a YouTube video)

### Why Browser Plays Audio (Not Agent/Server)

**Rationale:**
1. **Synchronization:** Audio and lip sync must be perfectly aligned
2. **Latency:** Minimized when playback happens in same process as rendering
3. **Simplicity:** No IPC or file coordination needed
4. **Web Audio API:** Provides precise timing and control

**Common Mistake:** Playing audio via `mpv` or `paplay` while browser also plays it → echo/duplication.

## Expression System

### Available Expressions

| Name | VRM Blend Shapes | Notes |
|------|------------------|-------|
| `neutral` | Resets all | Default, eyes open |
| `happy` | Smile + Eyes closed | Anime-style smile, use sparingly |
| `sad` | Frown + Brow down | |
| `angry` | Frown + Brow furrowed | |
| `relaxed` | Slight smile | Calm, content |
| `surprised` | Eyes wide + Mouth open | |

### Expression Mapping (Renderer)

```typescript
const expressionPresets = {
  neutral: { happy: 0, angry: 0, sad: 0, relaxed: 0, surprised: 0 },
  happy: { happy: 1, angry: 0, sad: 0, relaxed: 0, surprised: 0 },
  sad: { happy: 0, angry: 0, sad: 1, relaxed: 0, surprised: 0 },
  angry: { happy: 0, angry: 1, sad: 0, relaxed: 0, surprised: 0 },
  relaxed: { happy: 0, angry: 0, sad: 0, relaxed: 1, surprised: 0 },
  surprised: { happy: 0, angry: 0, sad: 0, relaxed: 0, surprised: 1 }
};
```

### Why `neutral` is Default (Not `happy`)

**Problem with `happy`:**
- Closes eyes (anime smile squint)
- Looks unnatural for normal conversation
- Gives impression of not paying attention

**Best Practice:**
- Use `neutral` for 90% of speech
- Use `happy` only for actual excitement or joy
- Reserve expressions for moments that genuinely call for them

### Blending and Intensity

Expressions can be blended with intensity values (0-1):

```json
{
  "type": "setExpression",
  "name": "happy",
  "intensity": 0.5
}
```

This creates a subtle half-smile instead of full anime grin.

## Connection Lifecycle

### Normal Flow

```
1. WebSocket Open
   Agent → Server: connect ws://localhost:8765

2. Identification
   Agent → Server: { type: 'identify', role: 'agent', name: 'clever' }
   Server → Agent: { type: 'identifyAck', ... }

3. Command(s)
   Agent → Server: { type: 'speak', text: '...', emotion: 'neutral' }
   Server → Renderer: { type: 'startSpeaking', audioUrl: '...', screenplay: [...] }
   Server → Agent: { type: 'speakAck', duration: 5.2 }

4. Wait for Completion
   [Agent waits ~15s for TTS generation + audio playback]

5. Close Connection
   Agent → Server: ws.close()
```

### Timing Considerations

**After `identify`:** Wait 500-1000ms before sending commands
- Allows server to fully process identification
- Prevents race conditions

**After `speak`:** Wait `(duration * 1000) + 2000` ms before closing
- `duration` from `speakAck` (TTS audio length in seconds)
- +2000ms buffer for HTTP fetch and initial playback
- Total usually ~15s for typical sentence

**Between commands:** No wait needed if commands are independent

### Error Handling

**Connection Failed:**
```javascript
ws.on('error', (err) => {
  console.error('WebSocket error:', err.message);
  // Check if control server is running
  // curl http://localhost:8766/status
});
```

**Timeout:**
```javascript
const timeout = setTimeout(() => {
  console.error('Timeout waiting for response');
  ws.close();
}, 30000); // 30s timeout

ws.on('message', (data) => {
  clearTimeout(timeout);
  // ... process message
});
```

## React Strict Mode Issue

### Problem

React 18 strict mode (development) mounts components twice:
```
Mount → Unmount → Mount
```

This causes:
1. First WebSocket connection created
2. First connection "destroyed" (but still alive)
3. Second WebSocket connection created
4. Both connections send messages → duplication

### Solution: Destroyed Flag Pattern

```typescript
// avatarClient.ts
let destroyed = false;

export function connectAvatarWS() {
  if (destroyed) {
    console.log('Already destroyed, skipping connection');
    return null;
  }
  
  const ws = new WebSocket('ws://localhost:8765');
  
  ws.addEventListener('open', () => {
    if (destroyed) {
      ws.close();
      return;
    }
    // ... normal open handler
  });
  
  ws.addEventListener('message', (event) => {
    if (destroyed) return;
    // ... normal message handler
  });
  
  return ws;
}

// In component:
useEffect(() => {
  const ws = connectAvatarWS();
  
  return () => {
    destroyed = true;
    ws?.close();
  };
}, []);
```

This ensures:
- First mount's connection is marked `destroyed` on unmount
- Second mount creates clean connection
- No zombie connections sending duplicate messages

### Production Behavior

In production build (`npm run build && npm start`), React does NOT double-mount. This issue only affects development.

## Troubleshooting Deep Dive

### Control Server Won't Start

**Error:** `EADDRINUSE: address already in use`

**Diagnosis:**
```bash
# Check what's using ports
ss -tlnp | grep 8765
ss -tlnp | grep 8766

# Kill existing process
kill $(lsof -t -i:8765)
```

**Fix:** Kill existing server, restart.

---

**Error:** `edge-tts: command not found`

**Diagnosis:**
```bash
which edge-tts
```

**Fix:** Install edge-tts:
```bash
pip install edge-tts
# or
nix-env -iA nixpkgs.edge-tts  # if on NixOS
```

### Renderer Won't Connect

**Symptom:** Red "Control Server Disconnected" badge in UI

**Diagnosis:**
```bash
# 1. Is control server running?
curl http://localhost:8766/status

# 2. Can renderer reach it?
curl -v ws://localhost:8765  # (will fail, but shows if port is open)

# 3. Check browser console
# Open DevTools → Console → look for WebSocket errors
```

**Common Causes:**
1. Control server not started: Start with `node server.js`
2. Wrong port: Check renderer's WebSocket URL (should be `ws://localhost:8765`)
3. Firewall blocking: Unlikely on localhost, but check `iptables`

**Fix:** Ensure control server is running, refresh browser page.

### Audio Plays Twice (Echo)

**Symptom:** Hear same audio twice with slight delay

**Cause:** Both browser AND system audio player (mpv) playing audio

**Diagnosis:**
```bash
# Check for mpv processes
ps aux | grep mpv

# Check audio sinks
wpctl status
```

**Fix:**
1. Don't call mpv for avatar audio
2. Let browser handle playback exclusively
3. Kill any stray mpv processes: `killall mpv`

### Lip Sync Broken (Mouth Not Moving)

**Symptom:** Audio plays but avatar's mouth doesn't move

**Diagnosis:**
1. Check browser console for errors
2. Check control server logs for TTS generation
3. Verify screenplay file exists: `cat /tmp/clever-avatar-tts/{id}/screenplay.json`

**Common Causes:**
1. edge-tts failed to generate screenplay
2. Screenplay data malformed or empty
3. Renderer not receiving `screenplay` field in `startSpeaking` message

**Fix:**
- Test edge-tts manually:
  ```bash
  edge-tts --voice en-GB-RyanNeural \
           --text "Test" \
           --write-media /tmp/test.mp3 \
           --write-subtitles /tmp/test.json
  cat /tmp/test.json  # Should have phoneme data
  ```
- Check server code sends `screenplay` in `startSpeaking` message
- Restart control server

### Expression Doesn't Change

**Symptom:** `setExpression` sent but avatar keeps same face

**Diagnosis:**
1. Check if correct command name used (`setExpression`, not `updateExpression` or `expression`)
2. Check browser console for message receipt
3. Verify expression name is valid

**Valid Expression Names:**
- neutral
- happy
- sad
- angry
- relaxed
- surprised

**Case sensitive:** Use lowercase

**Fix:**
- Use correct command: `{ type: 'setExpression', name: 'happy', intensity: 1 }`
- Check spelling of emotion name
- Restart renderer if stuck in expression

### Agent Can't Send Commands

**Symptom:** Connection succeeds but commands ignored

**Diagnosis:**
1. Did you send `identify` first?
2. Check control server logs for validation errors
3. Verify JSON format

**Fix:**
- Always send `identify` before any other command
- Check JSON syntax (trailing commas, quotes, etc.)
- Example:
  ```javascript
  ws.on('open', () => {
    // REQUIRED FIRST:
    ws.send(JSON.stringify({ type: 'identify', role: 'agent', name: 'clever' }));
    
    // THEN commands:
    setTimeout(() => {
      ws.send(JSON.stringify({ type: 'speak', text: 'Test', emotion: 'neutral' }));
    }, 1000);
  });
  ```

### TTS Generation Slow

**Symptom:** Long delay before audio plays

**Typical Times:**
- Short sentence (5-10 words): 2-3s
- Medium (20-30 words): 3-5s  - Long (50+ words): 5-8s

**Diagnosis:**
```bash
# Time a manual TTS generation
time edge-tts --voice en-GB-RyanNeural \
              --text "This is a test sentence" \
              --write-media /tmp/test.mp3
```

**If Slow (>10s for short text):**
1. Network issue (edge-tts uses Microsoft cloud service)
2. CPU constrained (check with `htop`)
3. Disk I/O slow (check `/tmp` mount)

**Fix:**
- Check internet connection
- Consider using local TTS engine (Piper, Coqui TTS) for offline use
- Use shorter text chunks

### "speakAck" Never Received

**Symptom:** Agent waits indefinitely after sending `speak`

**Diagnosis:**
1. Check control server logs for errors
2. Verify TTS generation succeeded
3. Check `/tmp/clever-avatar-tts/` for audio files

**Common Causes:**
1. edge-tts failed (network, invalid text, etc.)
2. Server crashed during processing
3. WebSocket disconnected mid-processing

**Fix:**
- Check server logs: `journalctl -u avatar-control-server -f` (if running as service)
- Or check terminal where `node server.js` is running
- Verify edge-tts works manually (see above)
- Add timeout in agent code:
  ```javascript
  const timeout = setTimeout(() => {
    console.error('Timeout waiting for speakAck');
    ws.close();
  }, 30000);
  
  ws.on('message', (data) => {
    const msg = JSON.parse(data);
    if (msg.type === 'speakAck') {
      clearTimeout(timeout);
      // ... proceed
    }
  });
  ```

## Virtual Camera Setup

**Status:** Configured in NixOS but kernel module not loaded (requires reboot)

### NixOS Configuration

```nix
# ~/.dotfiles/hosts/zanoni/configuration.nix
boot.extraModulePackages = [ config.boot.kernelPackages.v4l2loopback ];
boot.kernelModules = [ "v4l2loopback" ];
boot.extraModprobeConfig = ''
  options v4l2loopback devices=1 video_nr=10 card_label="Avatar Cam" exclusive_caps=1
'';
```

### After Reboot

```bash
# Verify module loaded
lsmod | grep v4l2loopback

# Check device exists
ls -l /dev/video10

# Should show:
# crw-rw----+ 1 root video 81, 10 Feb 2 14:30 /dev/video10
```

### ffmpeg Pipeline (Future)

```bash
# Capture browser canvas and stream to v4l2loopback
ffmpeg -f x11grab -video_size 1920x1080 -framerate 30 \
       -i :0.0+0,0 \  # Adjust to browser window position
       -vf "format=yuv420p" \
       -f v4l2 /dev/video10
```

**Note:** This will require scripting to:
1. Get browser window position/size
2. Start ffmpeg in background
3. Keep streaming while avatar is active
4. Stop cleanly when done

### Using in Google Meet

Once virtual camera is working:

1. Join Google Meet
2. Click settings (three dots) → Settings → Video
3. Select "Avatar Cam" from camera dropdown
4. Your avatar will appear as your video feed

**Limitations:**
- No bidirectional lip sync (avatar won't react to your voice)
- Currently requires manual ffmpeg invocation
- Future: Automated start/stop with avatar system

## Performance Considerations

### CPU Usage

**Control Server:** ~5-10% CPU (mostly idle, spikes during TTS)

**Renderer:** ~30-60% CPU for 3D rendering at 60fps

**TTS Generation:** ~20-30% CPU burst during edge-tts run

### Memory Usage

**Control Server:** ~50-100 MB

**Renderer (Browser):** ~500-800 MB (typical for 3D web app)

**Disk Space:** `/tmp/clever-avatar-tts/` accumulates audio files
- ~50-200 KB per audio file
- Clean up old files periodically:
  ```bash
  find /tmp/clever-avatar-tts -type f -mtime +1 -delete
  ```

### Network

**edge-tts:** Requires internet connection (Microsoft cloud service)

**Local Traffic:** WebSocket (8765) + HTTP (8766) both localhost only

**Bandwidth:** Minimal (~100 KB/minute for WebSocket messages + audio files)

## Security Notes

### Ports

**8765 (WebSocket)** - Should NOT be exposed to internet
- No authentication currently
- Anyone with access can control avatar

**8766 (HTTP)** - Should NOT be exposed to internet
- Serves audio files without auth
- CORS enabled (required for browser, but means any origin can fetch)

**3000 (Next.js)** - Local development only
- In production, would be behind nginx or similar

### Recommended Firewall

```bash
# Only allow localhost
iptables -A INPUT -p tcp --dport 8765 -s 127.0.0.1 -j ACCEPT
iptables -A INPUT -p tcp --dport 8765 -j DROP

iptables -A INPUT -p tcp --dport 8766 -s 127.0.0.1 -j ACCEPT
iptables -A INPUT -p tcp --dport 8766 -j DROP
```

### Future: Authentication

For production/multi-user:
- Add API keys or JWT tokens
- Validate `identify` messages against user database
- Rate limiting on speak commands (prevent TTS spam)

## Future Enhancements

### Planned
- [x] Basic lip sync with edge-tts
- [x] Expression control
- [ ] Virtual camera (blocked on reboot)
- [ ] Automated ffmpeg streaming
- [ ] systemd service files
- [ ] Browser extension for easier control

### Ideas
- **Voice cloning:** Use Coqui TTS or Piper for custom voice
- **Motion capture:** Webcam → face tracking → avatar expressions
- **Bidirectional:** Avatar reacts to microphone input (lip sync + expressions)
- **Scene control:** Change background, lighting, camera angles
- **Outfit system:** Load different VRM models or costumes
- **Animation presets:** Wave, nod, shrug, etc.
- **Multiplayer:** Multiple avatars in one scene

## Development Workflow

### Making Changes

**Control Server:**
1. Edit `server.js`
2. Restart: `Ctrl+C` then `node server.js`
3. Test with curl or WebSocket client

**Renderer:**
1. Edit files in `src/`
2. Next.js auto-reloads (watch terminal)
3. Refresh browser if needed
4. Check browser console for errors

### Testing Commands

```bash
# Test identify
wscat -c ws://localhost:8765
> {"type":"identify","role":"agent","name":"test"}

# Test speak (after identify)
> {"type":"speak","text":"Hello world","emotion":"neutral"}

# Test expression
> {"type":"setExpression","name":"happy","intensity":1}
```

**wscat installation:**
```bash
npm install -g wscat
# or
nix-shell -p nodePackages.wscat
```

### Debugging Tips

**Enable verbose logging in server:**
```javascript
// server.js
const DEBUG = true;

if (DEBUG) console.log('Message:', JSON.stringify(msg, null, 2));
```

**Browser DevTools:**
- Console: See WebSocket messages and errors
- Network: Check audio file loading (should be 200 OK)
- Sources: Set breakpoints in avatarClient.ts
- Performance: Monitor rendering FPS

**Server logs:**
```bash
# If running as systemd service
journalctl -u avatar-control-server -f

# Or just watch the terminal where node server.js runs
```

## File Reference

### Control Server Files

```
avatar-control-server/
├── server.js              # Main server file
├── package.json           # Dependencies: ws (WebSocket)
├── node_modules/          # Installed packages
└── /tmp/clever-avatar-tts/  # TTS output (outside project)
    └── {id}/
        ├── voice.mp3
        └── screenplay.json
```

### Renderer Files

```
avatar-renderer/
├── src/
│   ├── app/
│   │   └── page.tsx       # Main page component
│   ├── components/
│   │   ├── viewer.tsx     # 3D viewer (VRM rendering)
│   │   └── ...
│   └── lib/
│       └── avatarClient.ts  # WebSocket client
├── public/
│   └── AvatarSample_B.vrm  # 3D model
├── package.json
└── next.config.js
```

### Skill Files

```
~/.dotfiles/agents/skills/avatar/
├── SKILL.md                     # Main skill documentation
├── scripts/
│   └── avatar-speak.sh          # Convenience script
└── references/
    └── architecture.md          # This file
```

## Related Documentation

- **ChatVRM:** https://github.com/pixiv/ChatVRM (upstream project)
- **VRM Specification:** https://vrm.dev/en/
- **edge-tts:** https://github.com/rany2/edge-tts
- **WebSocket API:** https://developer.mozilla.org/en-US/docs/Web/API/WebSocket
- **Web Audio API:** https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API

## Changelog

- **2026-02-02:** Initial documentation created
  - 3-layer architecture defined
  - All message types documented
  - Troubleshooting section added
  - Virtual camera setup documented (pending reboot)
  - React strict mode issue documented with solution
