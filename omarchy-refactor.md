 Ready to code?

 Here is Claude's plan:
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
 Refactor: Remove Omarchy Branding from Hyprland Config

 Summary

 Remove all "omarchy" naming, merge the two-layer config (omarchy defaults + user overrides) into a single
 flat structure, and rename scripts from omarchy-* to hypr-*.

 Directory Structure Changes

 Hyprland config: merge two layers into conf.d/

 Before:
 .config/hypr/
 ├── hyprland.conf           (sources omarchy/* then user/*)
 ├── omarchy/                (base defaults - DELETE)
 │   ├── envs.conf
 │   ├── looknfeel.conf
 │   ├── input.conf
 │   ├── windows.conf
 │   ├── autostart.conf
 │   ├── bindings/{tiling,media,clipboard,utilities}.conf
 │   └── workspaces.conf
 └── user/                   (overrides - DELETE)
     ├── monitors.conf
     ├── input.conf
     ├── looknfeel.conf
     ├── autostart.conf
     ├── bindings.conf
     ├── workspaces.conf
     └── windows.conf

 After:
 .config/hypr/
 ├── hyprland.conf           (sources conf.d/*)
 ├── conf.d/
 │   ├── env.conf            ← from omarchy/envs.conf (no user override)
 │   ├── appearance.conf     ← MERGED omarchy/looknfeel.conf + user/looknfeel.conf
 │   ├── input.conf          ← MERGED omarchy/input.conf + user/input.conf
 │   ├── windows.conf        ← MERGED omarchy/windows.conf + user/windows.conf
 │   ├── autostart.conf      ← MERGED omarchy/autostart.conf + user/autostart.conf
 │   ├── monitors.conf       ← from user/monitors.conf
 │   ├── bindings.conf       ← MERGED all omarchy/bindings/* + user/bindings.conf
 │   └── workspaces.conf     ← from user/workspaces.conf (user's is the final state)
 ├── themes/                 ← moved from .config/omarchy/themes/
 │   ├── catppuccin/
 │   ├── tokyo-night/
 │   └── ... (14 themes)
 └── templates/              ← moved from .config/omarchy/themed/
     ├── mako.conf.tpl
     ├── waybar.css.tpl
     └── ... (16 templates)

 Theme runtime state: ~/.config/hypr-theme/

 Writable directory for runtime-generated theme files (can't be inside Nix-managed .config/hypr/).

 ~/.config/hypr-theme/       (created by activation hook)
 ├── current/
 │   ├── theme/              (generated theme files: mako.conf, waybar.css, etc.)
 │   ├── theme.name          (current theme name)
 │   ├── next-theme/         (temp during theme switch)
 │   ├── old-theme/          (temp during switch)
 │   └── background          (symlink to current bg)
 ├── user-themes/
 └── backgrounds/

 Scripts: bin/omarchy/ → bin/hypr/

 Rename directory and all 22 scripts from omarchy-* to hypr-*:
 ┌───────────────────────────────┬────────────────────────────┐
 │           Old name            │          New name          │
 ├───────────────────────────────┼────────────────────────────┤
 │ omarchy-theme-set             │ hypr-theme-set             │
 ├───────────────────────────────┼────────────────────────────┤
 │ omarchy-theme-set-templates   │ hypr-theme-set-templates   │
 ├───────────────────────────────┼────────────────────────────┤
 │ omarchy-theme-bg-next         │ hypr-theme-bg-next         │
 ├───────────────────────────────┼────────────────────────────┤
 │ omarchy-theme-list            │ hypr-theme-list            │
 ├───────────────────────────────┼────────────────────────────┤
 │ omarchy-theme-current         │ hypr-theme-current         │
 ├───────────────────────────────┼────────────────────────────┤
 │ omarchy-theme-set-gnome       │ hypr-theme-set-gnome       │
 ├───────────────────────────────┼────────────────────────────┤
 │ omarchy-restart-waybar        │ hypr-restart-waybar        │
 ├───────────────────────────────┼────────────────────────────┤
 │ omarchy-restart-swayosd       │ hypr-restart-swayosd       │
 ├───────────────────────────────┼────────────────────────────┤
 │ omarchy-restart-hyprctl       │ hypr-restart-hyprctl       │
 ├───────────────────────────────┼────────────────────────────┤
 │ omarchy-restart-swaync        │ hypr-restart-swaync        │
 ├───────────────────────────────┼────────────────────────────┤
 │ omarchy-restart-mako          │ hypr-restart-mako          │
 ├───────────────────────────────┼────────────────────────────┤
 │ omarchy-menu                  │ hypr-menu                  │
 ├───────────────────────────────┼────────────────────────────┤
 │ omarchy-fuzzel                │ hypr-fuzzel                │
 ├───────────────────────────────┼────────────────────────────┤
 │ omarchy-super-launcher        │ hypr-super-launcher        │
 ├───────────────────────────────┼────────────────────────────┤
 │ omarchy-bluetooth             │ hypr-bluetooth             │
 ├───────────────────────────────┼────────────────────────────┤
 │ omarchy-close-window-cycle    │ hypr-close-window-cycle    │
 ├───────────────────────────────┼────────────────────────────┤
 │ omarchy-show-desktop          │ hypr-show-desktop          │
 ├───────────────────────────────┼────────────────────────────┤
 │ omarchy-maximize-focus-daemon │ hypr-maximize-focus-daemon │
 ├───────────────────────────────┼────────────────────────────┤
 │ omarchy-monitor-switch        │ hypr-monitor-switch        │
 ├───────────────────────────────┼────────────────────────────┤
 │ omarchy-summon-brave          │ hypr-summon-brave          │
 ├───────────────────────────────┼────────────────────────────┤
 │ omarchy-screenshot            │ hypr-screenshot            │
 ├───────────────────────────────┼────────────────────────────┤
 │ omarchy-network               │ hypr-network               │
 └───────────────────────────────┴────────────────────────────┘
 ---
 Implementation Steps

 Step 1: Create merged conf.d/ files

 Create each file by merging omarchy base + user overrides into final values:

 - conf.d/env.conf — Copy omarchy/envs.conf as-is
 - conf.d/appearance.conf — Take omarchy/looknfeel.conf as base, apply user overrides (border colors,
 rounding=12, blur size=10/passes=3, dim_inactive, groupbar disabled, user's animations)
 - conf.d/input.conf — Merge: kb_layout=br, follow_mouse=2, sensitivity=-0.9 (user), keep
 kb_options=compose:caps, touchpad, DPMS (omarchy)
 - conf.d/windows.conf — Combine all window rules from both files
 - conf.d/autostart.conf — Combine both, rename omarchy-* commands to hypr-*
 - conf.d/monitors.conf — Copy user/monitors.conf as-is
 - conf.d/bindings.conf — Merge all binding files. Remove bindings the user unbound, apply user replacements.
 No unbind commands needed in merged config.
 - conf.d/workspaces.conf — Use user's workspace rules only (omarchy workspace grid bindings go into
 bindings.conf)

 Step 2: Update hyprland.conf

 Replace all source = ~/.config/hypr/omarchy/... and source = ~/.config/hypr/user/... with source =
 ~/.config/hypr/conf.d/... entries.

 Update theme import path: ~/.config/omarchy/current/theme/hyprland.conf →
 ~/.config/hypr-theme/current/theme/hyprland.conf

 Step 3: Move theme assets into .config/hypr/

 - Move .config/omarchy/themes/ → .config/hypr/themes/
 - Move .config/omarchy/themed/ → .config/hypr/templates/
 - Delete .config/omarchy/ directory

 Step 4: Rename scripts

 - Move bin/omarchy/ → bin/hypr/
 - Update all internal references in scripts:
   - ~/.config/omarchy/ → ~/.config/hypr-theme/ (runtime) or ~/.config/hypr/themes/ (definitions) or
 ~/.config/hypr/templates/ (templates)
   - omarchy-* command calls → hypr-*
   - Update usage/help text

 Step 5: Update Nix modules

 - Rename omarchy.nix → themes.nix
 - Rename omarchy-scripts.nix → scripts.nix
 - Update themes.nix:
   - Import ./scripts.nix
   - Change home.file paths to .config/hypr/themes and .config/hypr/templates
       - Wait: themes/ and templates/ are now INSIDE the .config/hypr source tree, so they get deployed
 automatically via the whole-directory symlink in packages.nix. Remove the separate home.file entries.
   - Update activation hook: initOmarchyTheme → initHyprTheme, paths → ~/.config/hypr-theme/
 - Update scripts.nix:
   - All mkScript names: omarchy-* → hypr-*
   - All source paths: ../../../bin/omarchy/ → ../../../bin/hypr/
 - Update default.nix: import ./themes.nix instead of ./omarchy.nix
 - Update mako-service.nix: ~/.config/omarchy/current/theme/mako.conf →
 ~/.config/hypr-theme/current/theme/mako.conf
 - Update swaync-service.nix: ~/.config/omarchy/current/theme/swaync.css →
 ~/.config/hypr-theme/current/theme/swaync.css
 - Update hyprshell.nix: CSS import path + comments
 - Update packages.nix: remove omarchy comment

 Step 6: Update other references

 - bin/rebuild (line 208-209): omarchy-restart-hyprctl → hypr-restart-hyprctl
 - .config/waybar/config: omarchy-super-launcher → hypr-super-launcher, omarchy-network → hypr-network
 - .config/waybar/style.css.in: ~/.config/omarchy/current/theme/waybar.css →
 ~/.config/hypr-theme/current/theme/waybar.css
 - .config/waybar/calendar-popup.py: ~/.config/omarchy/current/theme/colors.toml →
 ~/.config/hypr-theme/current/theme/colors.toml
 - Template files (.config/hypr/templates/*.tpl): update any omarchy references in template comments
 - Theme files (.config/hypr/themes/*/vscode.json): hackerman and ethereal reference "omarchy" in extension
 names — update or leave (these are external extension IDs)

 Step 7: Delete old files

 - Remove .config/hypr/omarchy/ directory (10 files)
 - Remove .config/hypr/user/ directory (7 files)
 - Remove .config/omarchy/ directory
 - Remove home/modules/hyprland/omarchy.nix
 - Remove home/modules/hyprland/omarchy-scripts.nix
 - Remove bin/omarchy/ directory

 ---
 Config Merge Details: bindings.conf

 The merged bindings.conf combines 4 omarchy binding files + user overrides into one file. Key decisions:

 From tiling.conf — KEEP all except:
 - SUPER, W → replace with hypr-close-window-cycle
 - SUPER SHIFT, F → replace with fullscreen, 0
 - SUPER, TAB / SUPER SHIFT, TAB → REMOVE (hyprshell handles Super+Tab)
 - SUPER CTRL, LEFT/RIGHT/UP/DOWN swap bindings → REMOVE (conflicted with workspace grid, user doesn't use)

 From utilities.conf — KEEP all except:
 - SUPER, B → replace with hypr-summon-brave
 - , PRINT → replace with hypr-screenshot annotate
 - Rename all omarchy-* commands to hypr-*

 From clipboard.conf — KEEP all except:
 - SUPER, V → replace with wezterm clipse

 From media.conf — KEEP as-is

 Add user custom bindings:
 - SUPER Q → hypr-super-launcher
 - Calendar, bluetooth TUI, whisper, tmux, daily note, voxtype, read-it-later, notifications, audio mixer

 Workspace navigation:
 - Use CTRL ALT arrows (user's preference, not omarchy SUPER CTRL)
 - Use CTRL ALT SHIFT for move-to-workspace

 ---
 Verification

 1. Rebuild: Run rebuild script after changes
 2. Check theme switching: hypr-theme-set catppuccin should work
 3. Check keybindings: Test SUPER+Q (launcher), SUPER+W (close), CTRL+ALT arrows (workspace nav)
 4. Check services: waybar, mako, swaync, hyprshell should start and load theme correctly
 5. Grep verification: grep -r "omarchy" .config/ home/ bin/ should return no results (except maybe
 vscode.json extension IDs which are external)
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌

 Claude has written up a plan and is ready to execute. Would you like to proceed?

 ❯ 1. Yes, clear context and bypass permissions
   2. Yes, and bypass permissions
   3. Yes, manually approve edits
   4. Type here to tell Claude what to change

 ctrl-g to edit in Cursor · ~/.claude/plans/scalable-questing-eclipse.md
