Original prompt: i would like to configure one skill to help agents use my pc on the best of them hability. Like using all the features tha a headed pc disposes. Like typing, screenshots, clicking, gestures, output audio, mic, output video, camera input... We already have some instructions scattered on the skills like browser usage, avatar has some mic and camera capabilities, we have some transcriptions capabilities with audio pipeline and other tools. Create for me a todo list of all the habilities ia agents should have and which skills provide them. We also need to think how to enable them, like a skill called desktop? sepparate skills for better discovery? How can we think about this?

# PC Habilities — AI Agent Desktop Capabilities

## Current Capability Map

| Capability | Status | Provider Skill(s) | Notes |
|---|---|---|---|
| **Audio Output (Speakers)** | DONE | talk-to-user, avatar, notify, hey-clever | edge-tts + mpv, wpctl volume control |
| **Audio Input (Microphone)** | DONE | hey-clever | whisp-away recording + whisper-cpp transcription |
| **Virtual Microphone** | DONE | avatar | PulseAudio AvatarMic sink, bridges to Discord/Meet |
| **Virtual Camera** | DONE | avatar | v4l2loopback, browser captures avatar window |
| **Browser Automation** | DONE | browser | Pinchtab (Chrome CDP), click/type/scroll/screenshot/JS eval |
| **Browser Screenshots** | DONE | browser | Via Pinchtab screenshot command |
| **Desktop Notifications** | DONE | notify | notify-send (D-Bus) + ntfy.sh mobile push |
| **Clipboard Read** | PARTIAL | hey-clever | wl-paste used but not as a general capability |
| **Window Management** | PARTIAL | hyprland-debug, quickshell | Read-only diagnostics, no active window manipulation |
| **System Monitoring** | DONE | system-health | CPU/memory/disk/temps/services/gateway |
| **Process Control** | DONE | tmux | Start/stop/restart processes in tmux panes |
| **Service Control** | PARTIAL | hyprland-debug, quickshell | systemctl for specific services only |
| **Desktop Screenshots** | MISSING | — | No grim/slurp Wayland screenshot skill |
| **Global Keyboard Input** | MISSING | — | No wtype/ydotool for typing outside browser |
| **Global Mouse Control** | MISSING | — | No ydotool for clicks/moves outside browser |
| **Clipboard Write** | MISSING | — | No wl-copy general capability |
| **Screen Recording** | MISSING | — | No wf-recorder or similar |
| **Webcam Capture** | MISSING | — | Can output virtual camera but can't read real webcam |
| **File Manager** | MISSING | — | No GUI file interaction |
| **Gestures/Touch** | MISSING | — | No gesture simulation |
| **OCR / Screen Reading** | MISSING | — | No screenshot → text pipeline for desktop |
| **Display/Monitor Control** | PARTIAL | hyprland-debug | hyprctl exists but not exposed as a capability |
| **Music/Media Control** | MISSING | — | No playerctl / MPRIS integration |

## Industry Context

Anthropic and OpenAI both use a single "computer" tool with sub-actions (screenshot, click, type, scroll, drag, key). The model does a screenshot→action loop. Microsoft builds agent connectors at the OS level (MCP servers for file explorer, settings, etc.). The consensus: pixel-based GUI automation is a fallback — use structured APIs/CLIs when available.

Key insight: None of the major providers handle audio I/O, camera, or notifications through their computer-use tools. These are handled through separate APIs entirely. Our skill system already covers these better than any commercial offering.

## Architecture Decision: Organization

**Separate skills** (recommended over a single "desktop" skill):

1. **Better discovery** — each skill description is injected into every session. A skill named "screenshot" with a clear description triggers when an agent needs to capture the screen. A monolithic "desktop" skill would either have a vague description or a massive one.

2. **Token efficiency** — agents only load the full body of skills they invoke. Separate small skills = smaller context per invocation. A mega-skill loads everything every time.

3. **Composability** — agents combine skills naturally. "Take a screenshot, OCR it, read the text aloud" chains screenshot → ocr → talk-to-user. Each step is independently useful.

4. **Matches our pattern** — browser, avatar, talk-to-user, hey-clever are already separate. Extending with more focused skills is consistent.

**What we do NOT need**: A meta-skill that indexes all capabilities. The skill description list already serves as the discovery mechanism. Each skill's description must clearly state what PC capability it provides.

## TODO: Missing Skills to Implement

### Priority 1 — High Impact, Low Effort (tools already on system)

- [ ] **screenshot** — Capture desktop/region/window screenshots using grim + slurp (Wayland). Return image path. Essential for the screenshot→action loop that all computer-use agents rely on. Could also integrate OCR (tesseract) for a screenshot→text pipeline.

- [ ] **clipboard** — Read and write system clipboard via wl-copy/wl-paste. Agents frequently need to transfer data between contexts. Currently scattered across hey-clever with no general-purpose access.

- [ ] **keyboard** — Global keyboard input via wtype (Wayland) or ydotool. Type text, send key combos (Ctrl+S, Alt+Tab), hold modifiers. Enables interaction with any focused application, not just browser.

- [ ] **mouse** — Global mouse control via ydotool. Click, move, scroll, drag at screen coordinates. Combined with screenshot skill, enables the screenshot→click loop for any desktop application.

- [ ] **media-control** — Play/pause/next/previous via playerctl (MPRIS D-Bus). Volume control via wpctl. Query now-playing metadata. Currently talk-to-user does volume ducking but no general media control.

### Priority 2 — Medium Impact, Medium Effort

- [ ] **screen-record** — Record screen/region/window using wf-recorder. Output to file. Useful for demos, bug reports, documenting workflows.

- [ ] **window** — Active window management via hyprctl dispatch. Move, resize, focus, fullscreen, workspace switching. Currently hyprland-debug reads state but doesn't manipulate windows as a capability.

- [ ] **webcam** — Capture frames from real webcam via ffmpeg/v4l2. Currently avatar outputs to virtual camera but agents can't see through the real camera.

- [ ] **ocr** — Screenshot → text via tesseract or similar. Could be part of screenshot skill or standalone. Enables agents to read desktop application content without accessibility APIs.

### Priority 3 — Nice to Have

- [ ] **display** — Monitor management: resolution, arrangement, brightness, night mode via hyprctl/wlr-randr/ddcutil.

- [ ] **bluetooth** — Device scanning, pairing, connecting via bluetoothctl.

- [ ] **wifi** — Network scanning, connecting via nmcli/iwctl.

## Existing Skills — Enhancement TODOs

- [ ] **browser** — Already comprehensive. Consider adding: PDF viewing, download management, multi-tab orchestration.

- [ ] **talk-to-user** — Already handles TTS well. Consider adding: stream audio files (music, podcasts), audio from URL.

- [ ] **avatar** — Already handles virtual cam + mic. Consider adding: emotion detection from webcam (requires webcam skill first), gesture-driven expressions.

- [ ] **hey-clever** — Already handles push-to-talk. Consider adding: continuous listening mode (voice-activated, not just push-to-talk), wake word customization.

## Implementation Notes

Each new skill follows the existing pattern:
- `agents/skills/{name}/SKILL.md` with YAML frontmatter (name, description ≤30 words)
- `agents/skills/{name}/scripts/` for shell/JS implementations
- Scripts follow canonical pattern: `set -Eeuo pipefail`, readonly constants, `main()` at bottom
- Deployed via `skills.nix` in home-manager modules
- Tools available on NixOS: grim, slurp, wtype, ydotool, wf-recorder, playerctl, wl-clipboard, tesseract, ffmpeg

Priority 1 skills (screenshot, clipboard, keyboard, mouse, media-control) give agents 80% of the missing desktop capabilities with minimal implementation effort since all underlying tools are standard Wayland/Linux utilities.
