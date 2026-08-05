<usage>
Run `scripts/keyboard.sh` type "text" or `scripts/keyboard.sh` key "combo". Combos use + separator: ctrl+s, alt+F4,
ctrl+shift+t.
</usage>

<pitfalls>
Types into whatever window is currently focused: always screenshot first to verify target. Never type secrets into
unverified windows. Key names are XKB keysyms: the script normalizes common aliases (ctrl→Control_L, alt→Alt_L,
super→Super_L, enter→Return, esc→Escape, backspace→BackSpace) but uncommon keys need exact XKB names. Wayland-only via
wtype: will not work in X11 or headless environments. For browser typing, use the browser skill instead (more reliable,
targets specific elements).
</pitfalls>
