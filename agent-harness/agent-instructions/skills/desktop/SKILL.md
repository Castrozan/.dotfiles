---
name: desktop
description: Automate desktop input, screenshots, clipboard, and media controls across Linux/Wayland and macOS. Use for non-browser GUI interaction or local media; keyboard and mouse are Linux/Wayland-only.
---

<cross_platform_capability_routing>
For full, region, or active-window screenshots, read `references/screenshot.md`. For clipboard read, write, or watch,
read `references/clipboard.md`; watch is Linux-only. For playback and volume through MPRIS on Linux or system audio
and Music.app on macOS, read `references/media-control.md`.
</cross_platform_capability_routing>

<linux_wayland_capability_routing>
For keyboard input through wtype, read `references/keyboard.md`. For mouse clicks, movement, scrolling, or dragging
through ydotool, read `references/mouse.md`.
</linux_wayland_capability_routing>

<macos_debugging_routing>
For macOS desktop traps that cost real debugging: window and application queries that report confidently wrong state,
accessibility under-reporting, Hammerspoon probe pitfalls, applications that rewrite their own settings, and the absence
of screen capture over SSH; read `references/knowledge.md`.
</macos_debugging_routing>
