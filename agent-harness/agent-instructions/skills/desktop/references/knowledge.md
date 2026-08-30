<macos_window_queries_lie>
Three system APIs report window and application state that is confidently wrong, and each has cost a wrong diagnosis.
The window list returns, for nearly every regular application, one borderless layer-zero window per Space at the screen
origin, full width and exactly as tall as the menu bar, with an empty name, so a window count says "has windows" for an
application that has none; filter on that geometry. The running-applications list is maintained from run-loop
notifications rather than queried live, so a daemon that polls with a bare sleep and never spins a run loop keeps
returning processes that already exited and misses ones that appeared; spin the run loop and confirm liveness directly.
Reading the screen size through Finder's desktop bounds is unusable here, because it needs an automation grant the
caller does not hold under launchd and silently takes the fallback, while over SSH it does not fail at all but hangs
forever; query the hardware profile instead.
</macos_window_queries_lie>

<the_accessibility_layer_under_reports_at_cold_start>
The window filter is asynchronous and under-reports right after every config reload while it warms its cache, and the
all-windows query comes back empty during a Space transition. Any logic that reads those results and then deletes or
rewrites persisted state will collapse every window onto one workspace. Never delete an assignment or gate one on the
result of an accessibility query; make assignments write-only and let a missing window simply not be moved.
</the_accessibility_layer_under_reports_at_cold_start>

<hammerspoon_probe_traps>
Timers returned by the scheduling calls are garbage collected unless retained in a global, so a probe assigned to a
local silently never fires. Finding a window by title returns no value rather than nil on this setup, so stringifying
the result raises. Polling all windows at high frequency starves Hammerspoon itself. And the default window animation
duration applies to programmatic frame changes, so parking a window far off-screen interpolates the whole distance with
easing and leaves it visible for most of the animation; use a zero duration for parking.
</hammerspoon_probe_traps>

<applications_that_rewrite_their_own_settings>
A browser that rewrites its accelerator table at every launch restores the default binding of any command whose default
was removed and drops user additions it does not accept, so a keybinding override there silently reverts. Remap at the
keystroke layer instead. Autoupdate is the same shape: the managed-preference policy that disables it is inert on a Mac
without device management and fails silently, so the browser updates anyway; removing the updater and blocking its
install roots is what actually holds. A terminal emulator resolves and pins its config path at startup, and since a
rebuild swaps the symlink to a brand-new store path the running process watches a file that will never change, so
config edits do not apply until it restarts.
</applications_that_rewrite_their_own_settings>

<locale_dependent_window_titles>
A window title's profile separator is locale-dependent, rendering as a dash in one locale and a colon in another, so
any automation that identifies a window by parsing its title breaks on a machine with a different language. Match on
the profile name alone rather than on the separator, or query the application directly.
</locale_dependent_window_titles>

<a_bouncing_dock_icon_is_usually_an_updater>
A tool's icon bouncing in the Dock is typically its bundled updater raising an update-available nag, not the tool
restarting. Diagnose from evidence rather than from the most interesting hypothesis: check the suspected daemon's own
log for actual activity in the window before blaming it. When a package manager owns the cask, the self-check is
redundant and can be turned off at the source.
</a_bouncing_dock_icon_is_usually_an_updater>

<no_screen_capture_over_ssh_on_a_headless_mac>
On a Mac driven only over SSH there is no working path to a screenshot of rendered window content: the capture tool
exits with an image-creation failure because the SSH process sits outside the GUI audit session, running it as the
console user through launchd fails on the missing privacy grant, and the automation framework cannot obtain one either.
Verify rendered output from the artifacts the renderer already writes rather than by capturing the screen.
</no_screen_capture_over_ssh_on_a_headless_mac>
