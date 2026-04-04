---
name: screenshot
description: Capture screenshots on Wayland. Use when the user asks to take a screenshot, capture the screen, save a window image, or grab a region.
---

<execution>
Run scripts/screenshot.sh from this skill's directory. Prints the saved file path to stdout.
</execution>

<flags>
--full     Full desktop capture (default)
--region   Interactive region selection via slurp
--window   Active window only (reads geometry from hyprctl)
</flags>

<output>
Saves to /tmp/screenshot-{timestamp}.png and prints the path to stdout.
</output>
