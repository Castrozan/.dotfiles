<per_client_views_are_a_local_fork>
Upstream fuses server and session so one server holds a single global active-workspace pointer mirrored to every
attached client. The tmux model, where each client moves independently, comes from a local fork pinned by tag. A running
server keeps the binary it launched with across a rebuild, so a fork change goes live only on a full server restart,
which drops every session on it.
</per_client_views_are_a_local_fork>

<never_steer_a_view_from_the_cli>
Per-client view isolation is implemented as a context swap performed only on a full client's own render and input.
Socket API requests bypass it, so a workspace or tab focus call over the CLI moves the foreground human's view rather
than the caller's. A client that needs to move its own view types the prefix chord into its own pty instead. Creation is
already safe, since the create and agent-start verbs all take a no-focus flag.
</never_steer_a_view_from_the_cli>

<shifted_digit_chords_are_destructive>
The workspace-switch binding is the prefix plus a shifted digit, and on a US layout those shifted digits are literally
the close-tab and split-pane characters, with close-tab winning. Closing the only tab of a workspace destroys the
workspace and every agent running in it. Never type a non-digit character blind into a multiplexer whose keymap you do
not own; the unshifted prefix-plus-digit tab switch is the only safe indexed chord, because bare digits carry no other
binding.
</shifted_digit_chords_are_destructive>

<a_lingering_ctrl_turns_a_prefix_chord_into_a_dead_key>
The prefix right-hand side matches on exact modifier equality, with a fallback for a lone shift and none for control,
so a chord typed before the finger leaves control arrives as control plus the letter and matches the plain-letter
binding on nothing. An unmatched right-hand side leaves prefix mode silently and never reaches the pane, so the chord
reads as a dead key rather than a stray character and fails only intermittently. Give such an action both spellings as
an array. Where the control spelling already carries a binding the fast chord fires that other action instead of
nothing, and a letter whose control code owns a key of its own is uncoverable, since the host input parser reads 0x09
as a bare tab.
</a_lingering_ctrl_turns_a_prefix_chord_into_a_dead_key>

<pane_run_wedges_after_a_full_screen_tui>
The pane-run verb delivers its command as a bracketed paste. A shell that just came back from a full-screen TUI killed
without restoring the terminal cannot consume the paste framing: the command lands with a literal paste marker, the
trailing return is swallowed as a newline inside the paste, and the buffer grows into a multi-line input. Drive such a
pane with the agent-send verb plus a separate carriage return instead.
</pane_run_wedges_after_a_full_screen_tui>

<agent_resume_across_reboots_is_native>
Surviving a reboot is a built-in feature: the server persists the working directory and agent session per pane and
replays the harness resume command when it restores, and the option defaults on. The only missing link was that nothing
reported the session id, which a session-start hook now does. No server restart is needed to activate it, since the
running server accepts the report on its existing socket. The limitation is that the replay uses a fixed argument list,
so a pane needing a different launcher still needs the fallback manifest.
</agent_resume_across_reboots_is_native>

<a_claude_pane_reads_idle_until_its_osc_title_arrives>
Claude Code keeps its prompt box rendered while it works, so the `live_prompt_box` rule matches all through a turn and
the pane reports idle. The one rule that outranks it, `osc_title_working`, reads the OSC title region, and Claude Code
writes that title only while `CLAUDE_CODE_DISABLE_TERMINAL_TITLE` is unset: that variable is the whole gate, read once
when the REPL mounts, and it suppresses the working title and the idle title together. herdr records the title
faithfully once one is sent, so an empty title region means the harness wrote nothing rather than a terminal that drops
it. Setting that variable therefore costs every claude pane's `agent_status` on the machine, and every gate built on a
working pane goes with it.
</a_claude_pane_reads_idle_until_its_osc_title_arrives>

<a_reported_state_loses_to_screen_detection>
`pane.report_agent` sets agent and state together on a pane herdr has not detected, and on a pane whose agent carries a
detection manifest it answers ok and changes nothing, whatever source or sequence number it passes. A hook that pushes
turn state can therefore never compensate for a detector that reads the rendering wrong: repair what the manifest
matches, or ship a local manifest override, and read `herdr agent explain` for the winning rule and its per-region
evidence before writing any reporter at all.
</a_reported_state_loses_to_screen_detection>

<panes_inherit_a_display_less_environment>
The server starts from the systemd user manager before the compositor imports the graphical session variables, so its
environment carries no `WAYLAND_DISPLAY`, `DISPLAY` or `XAUTHORITY` and every pane shell inherits that gap, which the
interactive bash rc repairs. In a pane that missed the repair, compositor-dependent work fails as if the tool rejected
its input rather than an environment fault: Claude Code reads a clipboard image by shelling out to `wl-paste` and
`xclip`, so it refuses every pasted image without ever naming the missing display. Do not reach for
`remote_image_paste`, which is hard-gated on the remote-client environment variable and yields no key on a local client,
leaving a `config.toml` binding inert.
</panes_inherit_a_display_less_environment>
