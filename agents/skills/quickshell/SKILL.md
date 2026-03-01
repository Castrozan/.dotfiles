---
name: quickshell
description: Implement, debug, and test Quickshell bar/OSD/switcher. Use when modifying QML files, debugging shape paths or rendering, testing IPC calls, or verifying visual changes after edits. Also use when adding new bar modules, popouts, dashboard tabs, or launcher features.
---

<silent_failure_traps>
Multiple shape files trace the same geometry for different purposes (fill vs stroke). They share the same property interface but are not programmatically linked. Changing one without the other compiles fine, renders with mismatched fill and border.

Multiple color systems coexist across different UI layers. Mixing them compiles fine, produces wrong colors at runtime with no error. Read imports at the top of the file you're editing to know which system that layer uses.

Region masking controls click-through. Adding a new visual element without adding it to the mask list makes it visible but unclickable. Read the mask region list when adding new interactive areas.

PathArc direction (Clockwise vs Counterclockwise) compiles and renders either way — wrong direction takes the long way around, producing visual artifacts. Read existing arcs in the same file to match the convention before adding new ones.

qmldir files register types for cross-directory imports. Missing entries produce "module not installed" errors that look like missing packages but are just registration. Check existing qmldir files in the directory when adding new types.
</silent_failure_traps>

<service_lifecycle>
Config directories are nix-managed symlinks. After changes: use the rebuild skill to regenerate symlinks, then restart the service via systemctl. Never manually kill or start quickshell processes. Editing existing files only needs restart (symlink target is the repo). Adding new files or directories needs rebuild first — the file exists in the repo but quickshell reads from the store path which doesn't include it yet.

Discover IPC targets dynamically with `qs ipc -c bar show`. Call with `qs ipc -c bar call TARGET FUNCTION [ARGS]`. Use IPC to trigger UI states for testing — more reliable than mouse simulation.
</service_lifecycle>

<visual_verification>
After visual changes: restart, wait 2 seconds, trigger UI state via IPC if needed, screenshot with the screenshot script in bin/hypr/, read the file to inspect. Prefer IPC show commands over hover simulation for popouts.
</visual_verification>

<debugging>
Journal logs first — a QML syntax error in any imported file prevents the entire shell from loading. Invisible components: check z-order, dimensions, and the Region mask list. Stale code after restart: verify nix symlinks still point to current dotfiles, not a cached store path.
</debugging>

<development_workflow>
Read existing code. Make changes. Commit. Rebuild (use rebuild skill). Restart service. Trigger UI via IPC. Screenshot and verify. Check logs. If broken: logs, fix, commit, rebuild, restart, repeat.
</development_workflow>
