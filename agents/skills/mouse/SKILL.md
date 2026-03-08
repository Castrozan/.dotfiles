---
name: mouse
description: Control mouse cursor — click, move, scroll, and drag on the desktop. Use when interacting with non-browser GUI applications, clicking desktop elements, or automating mouse-driven workflows.
---

<execution>
Run: scripts/mouse.sh click X Y [--button left|right|middle] [--double]
Run: scripts/mouse.sh move X Y
Run: scripts/mouse.sh scroll DIRECTION [AMOUNT]
Run: scripts/mouse.sh drag X1 Y1 X2 Y2

scripts/mouse.sh click 500 300                 # left click at (500, 300)
scripts/mouse.sh click 500 300 --button right  # right click
scripts/mouse.sh click 500 300 --double        # double click
scripts/mouse.sh move 100 200                  # move cursor to (100, 200)
scripts/mouse.sh scroll down 5                 # scroll down 5 steps
scripts/mouse.sh scroll up 3                   # scroll up 3 steps
scripts/mouse.sh drag 100 200 400 500          # drag from (100,200) to (400,500)
</execution>

<coordinates>
Pixel coordinates from top-left corner of the screen. Use the screenshot skill first to identify element positions. For multi-monitor setups, coordinates span the full virtual display.
</coordinates>

<caution>
Clicks wherever you point. Always take a screenshot first to confirm what's at the target coordinates. Never click blindly.
</caution>

<environment>
Requires ydotool and ydotoold (the daemon). The script starts ydotoold if not running. Works on both Wayland and X11.
</environment>
