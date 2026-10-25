### Scoped native consent

Use `connect --prepare` to identify the current managed Chrome process and window without requesting debugging access.
Obtain explicit approval for that specific connection, then consume its token through `connect`; the command's help owns
syntax. Tokens expire after one minute and are consumed before native interaction. Never cache approval, regenerate a
token as permission for another connection, or invoke the helper under unattended standing authorization.

The helper supports the exact English Chrome warning on one visible, non-fullscreen Chrome Global window under Hyprland
at display scale one. It verifies the browser executable, profile, process lifetime, geometry, complete warning and
button labels before one click. A pre-existing dialog, changed layout, competing operation, or user focus/cursor
movement fails closed. It uses a temporary input daemon with existing uinput permission; do not add permissions or
enable a daemon when preparation fails. Other platforms and ambiguous layouts require manual confirmation for the same
scoped grant.

### Connection execution

Start the bounded helper before the DevTools request; the managed `connect` operation enforces that order. Run it
through an execution tool with a short initial yield so other tools remain available. Observe the same process until
completion; never launch another attached connection while it is pending. It restores focus and cursor when they remain
under its control, stops its temporary input daemon, and exits. The granted worker remains task-owned until normal
cleanup.

Prefer a successful warm connection without native approval. A worker restart, dropped transport, or task change may
require fresh approval; this workflow does not grant persistent access. If the helper fails, inspect the reported target
and cleanup state before obtaining approval for another attempt. Do not blindly click fixed screenshot coordinates.

### Failed attempts and manual consent

A cold `connect` without a scoped approval option fails before requesting access. For an explicitly approved manual
connection, use `--manual-once` and handle the same bounded grant yourself. Never use that option as standing permission.
The native helper dismisses its fresh pending dialog on failure only while target, focus, and cursor remain under its
control; user movement aborts dismissal. If cleanup reports a pending dialog, cancel it manually before another attempt.
