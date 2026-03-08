---
name: mouse
description: Control mouse cursor — click, move, scroll, and drag on the desktop. Use when interacting with non-browser GUI applications, clicking desktop elements, or automating mouse-driven workflows.
---

<usage>
Run scripts/mouse.sh with subcommands: click X Y, move X Y, scroll DIRECTION [AMOUNT], drag X1 Y1 X2 Y2. Click accepts --button left|right|middle and --double.
</usage>

<pitfalls>
Requires ydotool and its daemon ydotoold — script auto-starts the daemon if not running but ydotoold needs uinput access (the user must be in the input group or ydotoold must run as root). Coordinates are absolute pixels from top-left of the virtual display (spans all monitors). Always take a screenshot first to identify target coordinates — never click blindly. Unlike keyboard/clipboard, ydotool works on both Wayland and X11 (it uses kernel uinput, not Wayland protocols). For browser clicks, use the browser skill instead (element-based, not coordinate-based).
</pitfalls>
