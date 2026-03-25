<usage>
Run scripts/screenshot.sh. Flags: --region (interactive slurp select), --active (focused window via hyprctl), --output PATH. Prints absolute path to saved PNG.
</usage>

<pitfalls>
Wayland-only — script auto-sets WAYLAND_DISPLAY=wayland-1 and XDG_RUNTIME_DIR but if running inside a container or remote SSH without Wayland socket access, grim will silently fail. The --region flag requires slurp which is interactive (user must drag-select) — don't use it in unattended automation. The --active flag depends on hyprctl activewindow returning valid geometry — fails if no window is focused (e.g., desktop background selected).
</pitfalls>
