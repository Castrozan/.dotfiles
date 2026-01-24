#!/bin/bash
# Toggle calendar popup - close if open, open if closed
if pkill -f "calendar-popup.py"; then
    exit 0
else
    python3 ~/.config/waybar/calendar-popup.py &
fi
