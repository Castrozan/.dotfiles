---
name: keyboard
description: Type text or send key combinations to the focused desktop window. Use when interacting with non-browser applications, filling native UI fields, or triggering OS keyboard shortcuts.
---

<execution>
Run: scripts/keyboard.sh type "text to type"
Run: scripts/keyboard.sh key "combo"

scripts/keyboard.sh type "Hello, world!"       # type text into focused window
scripts/keyboard.sh key "ctrl+s"               # send key combo (save)
scripts/keyboard.sh key "super"                # single key press
scripts/keyboard.sh key "alt+F4"               # close window
scripts/keyboard.sh key "ctrl+shift+t"         # reopen tab
</execution>

<key_names>
Modifiers: ctrl, alt, shift, super (logo key). Keys: a-z, 0-9, F1-F12, Return, Escape, Tab, BackSpace, Delete, space, Up, Down, Left, Right, Home, End, Page_Up, Page_Down, Insert, Print. Use wtype key names (XKB keysym names).
</key_names>

<caution>
Types into whatever window is currently focused. Verify the correct window has focus before typing sensitive content. Use screenshot skill to confirm visual state before keyboard actions. Never type passwords or secrets into unverified windows.
</caution>

<environment>
Wayland-only. Uses wtype. The script auto-sets WAYLAND_DISPLAY and XDG_RUNTIME_DIR if missing.
</environment>
