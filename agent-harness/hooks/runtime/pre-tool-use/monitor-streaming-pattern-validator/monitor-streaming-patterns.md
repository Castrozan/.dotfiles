# Monitor tool — streaming patterns

The Monitor tool delivers each stdout line as a separate `<event>` notification ONLY if the line reaches Monitor's stdout pipe immediately. The patterns below cause Monitor to batch all output into a single end-of-stream notification, defeating the point of using Monitor over `Bash run_in_background`.

If the PreToolUse validator rejected your Monitor invocation, find the named rule below and rewrite the command before retrying.

---

## python-without-u

Python block-buffers stdout when stdout is not a TTY. With multi-second gaps between prints, lines only arrive when the internal buffer fills (4-8 KB) or the process exits.

- Wrong: `python3 worker.py`
- Wrong: `python3 -c "import time; print('hi'); time.sleep(60)"`
- Right: `python3 -u worker.py`
- Right: `PYTHONUNBUFFERED=1 python3 worker.py`

The `-u` flag also covers nested Python subprocesses if they inherit the env, but `PYTHONUNBUFFERED=1` is the safer environment-level fix when wrapping commands like `make`, `pytest`, etc.

---

## grep-without-line-buffered

GNU grep buffers stdout block-wise when its stdout is a pipe (which Monitor's capture always is). The input is read line-by-line, but writes are deferred until the buffer fills.

- Wrong: `tail -f /var/log/app.log | grep ERROR`
- Right: `tail -f /var/log/app.log | grep --line-buffered ERROR`

Applies to all grep variants (`grep`, `egrep`, `fgrep`, `rg --line-buffered` is the ripgrep equivalent).

---

## sed-without-u

GNU sed buffers stdout when output is a pipe. Same root cause as grep.

- Wrong: `journalctl -f | sed 's/foo/bar/'`
- Right: `journalctl -f | sed -u 's/foo/bar/'` (or `--unbuffered`)

BSD sed (macOS default) uses `-l` instead of `-u`. On NixOS/Linux you'll have GNU sed.

---

## awk-needs-fflush

awk buffers stdout when piped. There is no global flag for GNU awk — you must either call `fflush()` after each `print`, or use `mawk` with `-W interactive`.

- Wrong: `tail -f /var/log/app.log | awk '/ERROR/ {print}'`
- Right: `tail -f /var/log/app.log | awk '/ERROR/ {print; fflush()}'`
- Right: `tail -f /var/log/app.log | mawk -W interactive '/ERROR/ {print}'`

---

## stderr-only-without-redirect

Monitor only watches stdout. Bytes written to stderr land in the output file but do NOT trigger `<event>` notifications. Many CLI tools (`git fetch`, `git push`, `curl -v`, `npm install --verbose`, `cargo build`, `kubectl apply --debug`) write progress and important status to stderr.

- Wrong: `git fetch --verbose origin main`
- Right: `git fetch --verbose origin main 2>&1`

If you want to suppress stderr entirely instead, use `2>/dev/null` — but only if you genuinely don't need it.

---

## rapid-bursts

Lines arriving within 200ms of each other coalesce into a single event by design (documented). Test outputs from a tight loop like `for i in {1..100}; do echo $i; done` will collapse to one event. This is not a bug you can hook around; either space the output with `sleep`, or accept the batching for that command.

---

## What Monitor actually streams reliably

After applying the rules above, these shapes stream per-line as expected:

- `tail -f /path/to/log` (kernel-level line buffering)
- `journalctl -f` (line-buffered native output)
- `python3 -u script.py`
- `pipeline | grep --line-buffered PATTERN`
- `pipeline | sed -u 'EXPR'`
- Native shell builtin output (`bash`/`zsh` `echo`, `printf` with `\n`)
- `cat` and `tr` in a pipe (pass-through, don't add buffering)

## What Monitor cannot do

- React to lines without trailing newlines (`printf "PROGRESS"` with no `\n` never fires)
- React to stderr (always redirect with `2>&1` if you need it)
- React to per-line output from binaries that buffer based on `isatty()` and have no flag to disable (some Go and Rust CLIs) — wrap them with `stdbuf -oL` at the call site if it works, or accept batched output
