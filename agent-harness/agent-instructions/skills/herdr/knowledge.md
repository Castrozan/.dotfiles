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
