---
name: quickshell
description: Implement, debug, and test Quickshell bar/OSD/switcher. Use when modifying QML files, debugging shape paths or rendering, testing IPC calls, or verifying visual changes after edits. Also use when adding new bar modules, popouts, dashboard tabs, or launcher features.
---

<announcement>
"I'm using the quickshell skill to work with the Quickshell bar."
</announcement>

<non_obvious_constraints>
Everything lives in one PanelWindow per screen — bar, popouts, dashboard, launcher are siblings, not separate windows. Region masking in Drawers.qml controls what's clickable vs click-through. Forgetting to add a new drawer to the mask region list makes it invisible to input.

Two shape files must always produce identical geometry: one fills the background, the other strokes the border. Change one, change both. The model can read them to understand the property interface — the trap is forgetting to update both.

Two separate color systems coexist. Bar-level code uses ThemeColors. Dashboard-level code uses Colours (Caelestia Material 3 palette). Mixing them compiles fine but produces wrong colors at runtime with no error.

Each subdirectory needs a qmldir registering its types. Missing qmldir entries produce "module not installed" errors that look like missing dependencies but are just registration.
</non_obvious_constraints>

<shape_traps>
Junction arcs INTO a drawer: PathArc.Clockwise. Corner arcs OF a drawer: PathArc.Counterclockwise. Wrong direction compiles and renders — but the arc takes the long way around, producing visual artifacts. This is the most common shape bug and the hardest to diagnose from screenshots alone.

When a popout overlaps a bar corner, merge logic activates automatically. Read the merged/effective properties in the shape files before assuming you need to handle overlap manually.

Trace the path mentally before coding. It's a continuous pen: PathLine moves, PathArc curves. Think start position, travel direction, inward vs outward relative to filled area.
</shape_traps>

<service_lifecycle>
Restart via systemctl only — never manually kill or start. QML changes need only a service restart (config is symlinked). Nix module changes need rebuild first, then restart.

Discover IPC targets dynamically with `qs ipc -c bar show`. Call with `qs ipc -c bar call TARGET FUNCTION [ARGS]`. Use IPC to trigger UI states for testing — more reliable than mouse simulation.
</service_lifecycle>

<visual_verification>
After visual changes: restart, wait 2 seconds, trigger UI state via IPC if needed, screenshot with the screenshot script in bin/hypr/, read the file to inspect. Prefer IPC show commands over hover simulation for popouts.
</visual_verification>

<debugging>
Journal logs first — a QML syntax error in any imported file prevents the entire shell from loading. Invisible components: check z-order, dimensions, and the Region mask list in Drawers.qml. Stale code after restart: verify nix symlinks still point to current dotfiles, not a cached store path.
</debugging>

<development_workflow>
Read existing code. Make changes. Commit. Restart service. Trigger UI via IPC. Screenshot and verify. Check logs. If broken: logs, fix, commit, restart, repeat.
</development_workflow>
