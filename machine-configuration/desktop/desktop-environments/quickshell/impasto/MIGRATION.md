### Previous bar to Impasto: where every feature went

Impasto paths are relative to `home/.config/quickshell/` in the fork `Castrozan/impasto`. Current bar paths are relative to `machine-configuration/desktop/desktop-environments/quickshell/bar/program-configuration/` in the dotfiles. Every Impasto equivalent below was found by reading the source.

Status values: `migrated` (native in Impasto as configured), `migrated differently` (another surface covers it), `needs work` (a fork or dotfiles change is still required), `dropped` (with the reason).

### Shape, hiding, monitors

| # | Current feature | Impasto equivalent | Status | Reason / how to reach it |
|---|---|---|---|---|
| 1 | Vertical bar on the left edge, 48 px (`drawers/ScreenDrawers.qml`) | Horizontal bar on the top edge with the island in the middle (`bar/Bar.qml`) | migrated differently | Impasto has no vertical bar; its four styles are all top-edge (`barStyle` in `services/SettingsService.qml`). |
| 2 | Bar hidden by default, shown on hover of a 2 px left edge strip | `barAutohide` plus the top-edge strip (`bar/Bar.qml:260-340`) | migrated | Seeded `barAutohide: true`; the pointer at the top edge brings the bar down. |
| 3 | Top edge hover opens the dashboard | Hovering a bar module opens its glance in the island (`bar/widgets/DynamicIsland.qml`) | migrated differently | No whole-dashboard hover; SUPER+A opens the control centre. |
| 4 | Bottom edge hover opens the launcher | Dock on the bottom edge with a launcher button (`dock/Dock.qml`, `dockLauncher`) | migrated differently | Dock is auto-hidden (`dockAutohide`); launcher by SUPER+Q or the dock button. |
| 5 | Right edge thirds: notifications, OSD, session menu on hover | Control centre notifications card, island OSD, session panel (`bar/island/ControlsPanel.qml`, `OsdLayer.qml`, `SessionPanel.qml`) | migrated differently | No right-edge hover zones; reached by SUPER+A, automatic OSD, and the session door in the control centre or launcher `>` list. |
| 6 | Hover timing 200 ms show, 450 ms hide | Impasto's own autohide timings (`bar/Bar.qml:297`, `Theme.durationFast`) | migrated differently | Timings are Impasto's and are not exposed as settings. |
| 7 | Workspace change shows the bar for 6 s | None found | dropped | No peek-on-workspace-change in `bar/Bar.qml`; the island still shows events while hidden. |
| 8 | One bar, panels and state per screen | Bar and dock on every screen, island live on the focused one (`shell.qml:86-120`, `barEverywhere`, `dockEverywhere`) | migrated | Default settings. |
| 9 | Bar drops under a fullscreen window | `covered` puts bar and dock in zen under a fullscreen window (`bar/Bar.qml:255-257`, `services/DockService.qml:289-295`) | migrated | Volume and brightness readouts still rise over the fullscreen window (`bar/Bar.qml:53-57`). |
| 10 | Click outside or Esc closes panels; open panel takes keyboard focus | Island panels hold the keyboard and close on Esc or outside click (`bar/Bar.qml:368`, `desktop/Desktop.qml:93` focus grab) | migrated | Native. |
| 11 | Desktop border frame on an empty workspace | Optional rounded screen corners (`ScreenCorners.qml`, `screenCorners`), deck or spectrum on empty workspace (`deckOnEmpty`, `spectrumOnEmpty`) | dropped | The continuous-frame border is the old shell's signature and has no Impasto counterpart; the listed options are different decorations, all off by default. |

### Bar modules

| # | Current feature | Impasto equivalent | Status | Reason / how to reach it |
|---|---|---|---|---|
| 12 | Launcher button, left click launcher, right click terminal | Dock launcher button (`dock/Dock.qml`, `dockLauncher`); launcher shortcut | migrated differently | No right-click terminal; SUPER+RETURN stays the terminal key. |
| 13 | Window-switcher button (writes the switcher socket) | None | dropped | Lucas's own switcher service stays on SUPER+TAB and ALT+TAB; only the bar button goes. The launcher also has a `windows` mode (`services/LauncherService.qml:39`). |
| 14 | Workspaces: 7 slots per page, paged around the focused one, highest at top, click to switch | Workspace strip, 5 slots growing to 10, dots, bars, rings or numbers (`bar/widgets/WorkspacesWidget.qml`, `workspaceCount`, `workspaceMax`, `workspaceStyle`) | migrated differently | Horizontal, capped at `workspaceMax` 10 by default, so the screensaver workspace 11 needs `workspaceMax` raised to show. Click uses the hyprlang dispatch added in the fork (`services/CompositorDispatch.qml`). |
| 15 | Slot index 3 drawn in the warning colour | None | dropped | Bespoke marker with no counterpart. |
| 16 | Scroll over workspaces switches workspace | None found in `bar/widgets/WorkspacesWidget.qml` | dropped | No wheel handler on the strip. |
| 17 | Special workspaces not shown in the bar | A capsule for the special workspace open over the screen (`bar/widgets/WorkspacesWidget.qml:340-394`); scratchpads in the overview (`bar/island/OverviewPanel.qml:751-806`) | migrated | Gain: `special:avatar` and others show while open. |
| 18 | CPU, RAM, GPU percentages every 3 s | `stats` module with CPU, memory and graphics, 3 s poll (`bar/modules/StatsModule.qml`, `services/StatsService.qml`, `scripts/stats.py`) | migrated | GPU usage and temperature were added in the fork as one more series; the chip is on the bar by the first-run settings. |
| 19 | Running apps: icon per window class, focused marker, click focuses, +N overflow | Dock with pinned and running apps on every screen (`dock/Dock.qml`, `dock/DockItem.qml`, `services/DockService.qml`, `dockRunning`); optional app icons on the workspace strip (`workspaceApps`) | migrated differently | Lives in the bottom dock, not the bar. Focus uses the fork's hyprlang dispatch. |
| 20 | Tray: recoloured icons, left click activates, menu in a popout | Tray on the bar, left activates, right opens the menu in the island, middle is the second action (`bar/widgets/TrayWidget.qml:19,104-112`, `bar/island/TrayMenuPanel.qml`) | migrated | Icons come from Papirus panel icons where named (`components/TrayIcon.qml`), patched to the Nix store path in the fork package. |
| 21 | Clock: HH, MM, day, month stacked | Island rest shows the time; `clock` module and `clockShowsDate`, `clockShowsSeconds`, `clockFormat` (`bar/island/IslandRest.qml`, `bar/modules/ClockModule.qml`) | migrated | Horizontal; set `clockShowsDate` to keep the date visible. |
| 22 | Status icon: VPN (polls `openvpn-proton-paraguay.service`, click runs `vpn-py`/`vpn-off`) | `vpn` module and control centre tile (fork: `services/VpnService.qml`, `bar/modules/VpnModule.qml`) | migrated | The unit and both commands are Impasto settings (`vpnUnit`, `vpnConnectCommand`, `vpnDisconnectCommand`), seeded for chise. |
| 23 | Status icon: notification sound toggle (`hypr-notification-sound-toggle`) | Focus (do not disturb) toggle only (`services/ControlsService.qml:269-271`); per-app `notificationRules` | dropped | The helper toggled mako's sound; mako is off while Impasto is active and Impasto has no sound-only toggle. |
| 24 | Status icon: output device glyph, click toggles mute | `volume` module with detail, device list and mute (`bar/modules/VolumeModule.qml`, `bar/island/SoundDetail.qml`) | migrated | Native through Quickshell's Pipewire service. |
| 25 | Status icon: microphone, click runs `hypr-microphone-toggle` | Microphone tile and detail (`services/ControlsService.qml:275-279`, `bar/island/MicrophoneDetail.qml`); privacy indicator on the island | migrated | Mute through Pipewire; the old helper is no longer called by the shell. |
| 26 | Status icon: network, hover popout, click runs `hypr-network` | `network` module and Wi-Fi detail with connect, disconnect, password entry, scan (`bar/modules/NetworkModule.qml`, `bar/island/NetworkDetail.qml`) | migrated | Richer than the old read-only list. |
| 27 | Status icon: bluetooth, hover popout, click opens `bluetui` | `bluetooth` module and detail with pair, connect, disconnect (`bar/modules/BluetoothModule.qml`, `bar/island/BluetoothDetail.qml`) | migrated | `bluetui` stays available from the terminal. |
| 28 | Status icon: keyboard backlight cycle (chise only) | `keyboardlight` module and control centre tile (fork: `services/KeyboardBacklightService.qml`, `bar/modules/KeyboardBacklightModule.qml`) | migrated | Drives a sysfs keyboard led, or the command in `keyboardBacklightCommand`, which chise sets to `set-keyboard-backlight-brightness`. The tile cycles 0/5/25/50/100. |
| 29 | Status icon: battery with popout (percent, status, watts) | `battery` module and `BatteryWidget`, power detail with profile picker (`bar/modules/BatteryModule.qml`, `bar/widgets/BatteryWidget.qml`, `bar/island/PowerDetail.qml`) | migrated | Uses UPower, so not tied to `BAT0`. Power profiles need power-profiles-daemon, which the trial log showed absent, so that tile reads "Unknown". |
| 30 | Status icons collapse into a "⋯" popout when the bar is short | Tray fold (`bar/widgets/TrayWidget.qml:148`) and chip settings (`chipFigure`, `chipHover`) | migrated differently | Modules are chosen and arranged in Settings; there is no automatic overflow popout for modules. |
| 31 | Power button runs `wlogout` | Session panel: lock, suspend, log out, restart, shut down (`services/SessionService.qml:24-28`, `bar/island/SessionPanel.qml`) | migrated differently | `wlogout` keeps its own keybinds; the session panel opens from the control centre, the launcher `>` list or `panel open session`. |

### Popouts

| # | Current feature | Impasto equivalent | Status | Reason / how to reach it |
|---|---|---|---|---|
| 32 | Network popout: connection, IP, list of networks | `bar/island/NetworkDetail.qml`; address also in `bar/island/StatsPanel.qml` | migrated | Opens in the island from the module or the Wi-Fi tile. |
| 33 | Bluetooth popout: adapter state, connected devices | `bar/island/BluetoothDetail.qml` | migrated | Same. |
| 34 | Battery popout: percent, status, watts | `bar/island/PowerDetail.qml`, battery glance | migrated | Watts not verified in the detail; percent and state are shown. |
| 35 | Status-icons popout: 7 rows repeating icon actions | Toggles block in the control centre (`bar/island/controls/TogglesBlock.qml`) | migrated differently | Covers Wi-Fi, Bluetooth, power, focus, microphone, airplane, keep awake, night light. |
| 36 | Tray menu popout with submenus | `bar/island/TrayMenuPanel.qml` | migrated | Right click on a tray icon. |

### Dashboard

| # | Current feature | Impasto equivalent | Status | Reason / how to reach it |
|---|---|---|---|---|
| 37 | Dashboard panel with Tab and Shift+Tab between five tabs | Control centre, a grid of blocks (`bar/island/ControlsPanel.qml`, default layout at `services/ControlsService.qml:522-529`) plus one island panel per topic | migrated differently | SUPER+A for the control centre; SUPER+M for media. |
| 38 | Dashboard tab: user card (OS, WM, uptime) | `impasto` block (`bar/island/controls/ImpastoBlock.qml`, data from `scripts/machine.py`) | needs work | The block exists but is not in the default layout, and `machine.py` counts packages from `/var/lib/pacman/local`, which is absent on NixOS. Add the block in Settings; package count stays empty unless patched. |
| 39 | Dashboard tab: weather summary | `bar/island/controls/WeatherCard.qml` | migrated | In the default control centre. |
| 40 | Dashboard tab: date and time, calendar | `bar/island/controls/CalendarCard.qml`, `ClockBlock.qml`, `calendar` module | migrated | Calendar card is in the default layout; it also takes calendar links and task dots. |
| 41 | Dashboard tab: CPU, memory, storage bars | `bar/island/StatsPanel.qml` (processor, memory, temperature, network, storage) | migrated | `panel open stats` or the stats door. |
| 42 | Dashboard tab: media card with cover, title, transport, player badge | `bar/island/controls/MediaCard.qml`, `bar/island/MediaPanel.qml` | migrated | Player switcher appears when more than one player exists (`MediaPanel.qml:210-214`). |
| 43 | Media tab: cava visualiser | Spectrum from cava on the media chip and the island (`services/CavaService.qml`, `bar/modules/MediaModule.qml`, `bar/island/IslandRest.qml:272`, `islandSpectrum`); desktop spectrum (`desktop/SpectrumBars.qml`, `desktop/EdgeSpectrum.qml`) | migrated | Uses the shell's own `scripts/cava.conf`; the old pulse-monitor helper script is not used. |
| 44 | Media tab: bongo cat GIF | Pet on the bar and in a panel (`services/PetService.qml`, `bar/modules/PetModule.qml`, `bar/island/PetPanel.qml`) | dropped | No bongo cat asset; the pet is a different feature that fills the same playful slot. |
| 45 | Media tab: seek slider and keyboard seek | `bar/island/MediaPanel.qml:42-43,110-135` | migrated | Left and Right seek 5 s, Space plays or pauses. |
| 46 | Media tab: raise player and quit player buttons | Not found in `bar/island/MediaPanel.qml` | dropped | No raise or quit action in the panel. |
| 47 | Performance tab: CPU card with temperature | `bar/island/StatsPanel.qml:48,155`, hwmon read in `scripts/stats.py:152` | migrated | One temperature series from hwmon. |
| 48 | Performance tab: GPU card with usage and temperature | Graphics card in `bar/island/StatsPanel.qml` (fork) | migrated | Reads `nvidia-smi`, else `gpu_busy_percent`; absent on a machine with neither. |
| 49 | Performance tab: memory and storage gauges | `bar/island/StatsPanel.qml:96,211` | migrated | Native. |
| 50 | Performance tab: network sparkline | `bar/island/StatsPanel.qml:171`, `netspeed` module (`bar/modules/NetSpeedModule.qml`) | migrated | Native. |
| 51 | Performance tab: battery tank | Battery module and widget (row 29) | migrated differently | Shown as a ring or figure, not a tank. |
| 52 | Weather tab: Open-Meteo 7-day forecast, sunrise, humidity, feels-like, wind | wttr.in reading with forecast (`scripts/weather.py:29`, `services/WeatherService.qml`, `bar/island/controls/WeatherCard.qml`) | migrated differently | Different source; card shows current, feels-like, high and low and a forecast row. Humidity and wind detail not verified. |
| 53 | Weather location from IP via ipinfo.io | wttr.in geolocates the request when `weatherPlace` is empty (`services/WeatherService.qml:18-19,63`) | migrated | Trial showed "Criciuma, Brazil". Set `weatherPlace` to pin it. |
| 54 | Celsius and 24-hour clock | `weatherUnits: "m"`, `clockFormat: "HH:mm"` defaults | migrated | Defaults already match. |
| 55 | Audio tab: output and input devices, default, volume, mute | `bar/island/SoundDetail.qml`, `bar/island/MicrophoneDetail.qml` | migrated | Through Pipewire instead of pactl. |
| 56 | Audio tab: Bluetooth devices connect and disconnect | `bar/island/BluetoothDetail.qml` | migrated | Native. |
| 57 | Audio tab: Bluetooth audio profile picker (`pactl set-card-profile`) | Profile rows per connected Bluetooth card in `bar/island/SoundDetail.qml` (fork, data in `services/AudioService.qml`) | migrated | Lists the available profiles as pactl names them, with the active one marked. |

### Launcher and wallpaper

| # | Current feature | Impasto equivalent | Status | Reason / how to reach it |
|---|---|---|---|---|
| 58 | Launcher apps mode: desktop entries, prefix first, most recent first | Apps mode with history (`services/LauncherService.qml:53`, `launcherOrder: "recent"`, `scripts/applications.py`) | migrated | Opened by SUPER+Q. Apps start through `gtk-launch`; terminal apps follow the desktop entry, so wezterm handling should be checked live. |
| 59 | Launcher `:` actions: Wallpaper, Next Wallpaper, Lock, Reboot, Shutdown | `>` desk list of control centre doors and modes (`services/LauncherService.qml:366-403`); session panel | migrated differently | Session actions through the session door; wallpaper through the appearance door. No "next wallpaper" entry; `wallpaper random` exists as IPC (`Commands.qml:515`). |
| 60 | Launcher `:wallpaper` mode over `~/.config/hypr-theme/wallpapers`, applying through `hypr-theme-generate-and-apply` | hypr-theme stays the picker; `theme_bg_apply.py` hands each applied wallpaper to Impasto (`wallpaper set`) | migrated differently | Pick wallpapers through hypr-theme as before; Impasto takes its palette from the wallpaper it is handed. Picking in Impasto's own appearance panel changes only Impasto and the wallpaper, not the hypr-theme programs. |
| 61 | 3 s shrinking-circle wallpaper transition overlay | `awww` transitions chosen by `wallpaperTransition` (`services/WallpaperService.qml:254-271`) | migrated differently | Transition is drawn by `awww`, not by a shell overlay. `theme_bg_apply.py` currently passes `--transition-type none` because the old overlay animated it. |
| 62 | Launcher size 520 px, 7 rows | `launcherResults: 9`, `launcherFits` | migrated differently | Sized by Impasto settings. |

### OSD, session, notifications, utilities

| # | Current feature | Impasto equivalent | Status | Reason / how to reach it |
|---|---|---|---|---|
| 63 | OSD fed by JSON on `quickshell-osd.sock` from `volume` and `brightness` scripts | Island OSD driven by the services themselves (`services/OsdService.qml`, `bar/island/OsdLayer.qml`) | migrated | Volume and mute come from Pipewire change signals, brightness from a watch on the backlight file (`services/BrightnessService.qml:136-141`), so the scripts keep working and the socket message is no longer needed. `quickshell-osd-send` finds no socket while Impasto is active; confirm it fails quietly. |
| 64 | OSD for microphone mute | `services/OsdService.qml:148-158` | migrated | Announces "Microphone muted" or "Microphone live". |
| 65 | OSD slider is interactive (drag, scroll) | Volume and brightness sliders in the control centre and module details (`bar/island/controls/TogglesBlock.qml`, `bar/island/LevelRow.qml`) | migrated differently | The OSD readout itself is not a control. |
| 66 | OSD volume tinted when no music plays | None | dropped | Bespoke cue. |
| 67 | OSD on every screen | OSD on the island of the live screen; brightness names the screen that changed (`services/OsdService.qml:92-104`) | migrated differently | One island is live at a time. |
| 68 | Session menu: fullscreen toggle, lock, exit, suspend, reboot, poweroff | `services/SessionService.qml:24-28,111-131` | migrated differently | No fullscreen toggle (SUPER+F stays in Hyprland). Lock runs hyprlock through `IMPASTO_LOCK_COMMAND` (fork, `services/LockService.qml`). Log out uses the fork's hyprlang `exit`. |
| 69 | Notification sidebar backed by mako (list, history, dismiss one, dismiss all) | Notification server in the shell with history (`services/NotificationService.qml:43`, `bar/island/controls/NotificationList.qml`, `bar/island/NotificationLayer.qml`, `bar/modules/NotificationsModule.qml`) | migrated | Impasto owns `org.freedesktop.Notifications`; mako is off while Impasto is active. Arrivals show on the island with their buttons. |
| 70 | Sidebar keyboard: j/k, Enter, d, Esc | Not verified in `NotificationList.qml` | needs work | Check live; if absent, a small fork change adds the keys. |
| 71 | Utilities: Wi-Fi toggle | `services/ControlsService.qml:245` | migrated | Toggles block. |
| 72 | Utilities: Bluetooth power | `services/ControlsService.qml:252` | migrated | Toggles block. |
| 73 | Utilities: microphone mute | `services/ControlsService.qml:275` | migrated | Toggles block. |
| 74 | Utilities: do not disturb (`makoctl mode`) | Focus tile, `doNotDisturb` (`services/ControlsService.qml:269-271`) | migrated | Held in Impasto settings. |
| 75 | Utilities: keep awake (`systemd-inhibit`) | Keep-awake tile, `IdleService.keepAwake` (`services/ControlsService.qml:283-286`, `services/IdleService.qml`) | migrated differently | It holds Impasto's own idle monitors off, and those are all 0 (never) by default; it is not a systemd idle inhibitor, so it does not stop other idle handlers. |
| 76 | Utilities: night light (`hyprsunset -t 3500`) | Night-light tile and detail (`services/SunsetService.qml`, `bar/island/NightLightDetail.qml`, `nightTemperature: 4000`) | migrated | Uses `hyprsunset`; the autostart `hyprsunset` line should be checked against it. |

### Theming, IPC, keybinds

| # | Current feature | Impasto equivalent | Status | Reason / how to reach it |
|---|---|---|---|---|
| 77 | Colours from `quickshell-bar-colors.json`, rendered by the hypr-theme pipeline | Adaptive palette sampled from the wallpaper, or one of nine fixed palettes (`services/ThemeService.qml`, `scripts/theme_manager.py`) | migrated differently | Impasto colours itself from the wallpaper it set; `themeTargets: []` stops it writing other programs. The template stays because the overview reads it. |
| 78 | Font hardcoded to JetBrainsMono Nerd Font | `fontFamily` Inter, `fontMono` JetBrainsMono Nerd Font Mono (`services/SettingsService.qml`) | migrated differently | Configurable; set `fontFamily` to keep the old face. |
| 79 | `bar toggle` on SUPER+J | `bar pin` (fork, `Commands.qml`), `bar toggle` (zen) | migrated | SUPER+J pins or unpins the bar. |
| 80 | `dashboard toggle` on SUPER+M | Global shortcut `quickshell:media` (`shell.qml`, `services/ShortcutService.qml:39-79`) | migrated differently | Opens the media panel rather than a tabbed dashboard. |
| 81 | `launcher toggle` on SUPER+Q | Global shortcut `quickshell:launcher` | migrated | Same key. |
| 82 | `sidebar toggle` on SUPER+A | Global shortcut `quickshell:controls` | migrated | Control centre with the notifications card. |
| 83 | `session toggle` (no caller) | `panel open session`, global `quickshell:session` | migrated | Unbound by default in Lucas's config, as before. |
| 84 | `utilities toggle` (no caller) | Control centre | migrated differently | Part of the SUPER+A surface. |
| 85 | `osd show/hide` (no caller) | `osd say <text> <icon>` (`Commands.qml:543`) | migrated differently | Shows a message; levels come from the services. |
| 86 | `popout toggle/show/hide` (no caller) | `panel open <name>` with wifi, bluetooth, sound, microphone, brightness, nightlight, power (`Commands.qml:252`) | migrated | Same idea, named panels. |
| 87 | SUPER+O overview and SUPER+TAB switcher services | Unchanged; Impasto's own overview panel (`bar/island/OverviewPanel.qml`) stays unbound | migrated | Lucas's services keep running beside Impasto. |
| 88 | SUPER+SPACE fuzzel | Unchanged | migrated | Not part of the shell. |
| 89 | Tests and probes that name `quickshell-bar` (`runtime.bats`, `perf-runtime.bats`, desktop benchmarks, bar QML tests) | `runtime.bats` reads the active shell's units from `~/.config/hypr-shell/autostart.conf` | migrated differently | The bar's perf tests skip while the bar is not the active shell; its QML tests stay while the previous bar is kept. No perf tests cover Impasto yet. |

### Gaps that remain

- User card (row 38): the package count reads pacman, so it stays empty on NixOS.
- Notification list keyboard keys (row 70): not checked live.
- Notification sound toggle (row 23): `hypr-notification-sound-toggle` and `makoctl` do nothing while mako is off;
  Focus is the single switch.
- Impasto's Settings pages for keys, compositor look and monitor arrangement do nothing on a hyprlang config; the
  dotfiles own those.

### New things Impasto adds

- A dock with pinned and running applications, auto-hidden, on every screen.
- Desktop widgets on the wallpaper in three themes, arranged by right click.
- Notes, a task board and timers, each with IPC (`note`, `task`, `timer` in `Commands.qml`) and launcher modes.
- Launcher modes for calculation, open windows, clipboard history, emoji and timers.
- Capture surface: region, window and screen shots, annotation with satty, text recognition, recording.
- Its own lock screen, idle monitors and polkit agent, available but not relied on in the decided design.
- Claude Code and Codex usage modules, GitHub wall, markets, screen time, local servers, virtual machines.
- Material choices per layer (classic, glass, liquid), four bar styles and a settings window for all of it.
