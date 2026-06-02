# Background Bash — anti-patterns

A Bash command launched with `run_in_background: true` reports completion
via a single task-notification with an exit code, then the LLM reads
the output file.

The validator rejects two distinct failure modes:

1. **silent-fake-success** — the command exits 0 with empty/wrong output,
   so the notification looks identical to genuine success and the LLM has
   no in-band signal that something went wrong. Usually a filter that
   matched nothing because of a typo, a fabricated literal, or an unset
   variable.
2. **hang-forever** — the command blocks on a controlling terminal that a
   background task does not have (interactive editor, full-screen TUI, or
   a git subcommand that opens an editor). It never exits, so the
   completion notification never arrives and the task is stuck. These
   shapes were confirmed empirically: launched under `setsid` with stdin
   at EOF (the background harness environment), they never terminate.

   Note: servers, `tail -f`, `journalctl -f`, `watch`, and long `sleep`s
   also never terminate, but those are *legitimate* background uses (the
   intended replacement for the Monitor tool), so they are NOT rejected.
   Pagers (`less`, `more`, `man`) are NOT rejected either — they detect
   non-TTY stdout and behave like `cat`, exiting immediately.

If the PreToolUse validator rejected your background bash invocation,
find the named rule below and rewrite the command before retrying.

---

## until-loop-terminating-on-empty-count

```
until [ "$(... | jq 'length')" = "0" ]; do sleep N; done
```

The loop terminates when the inner command produces "0" items. If the
inner filter has a typo, mismatched literal, or unset variable, the
count is 0 from the very first iteration. The loop never enters, the
final report runs against the same broken filter, and the command exits
0 with empty output.

- Wrong:
  ```
  until [ "$(gh run list --json status,headSha --jq '[.[] | select(.headSha == "abc...") | select(.status != "completed")] | length')" = "0" ]; do sleep 15; done
  ```
- Right (terminate on *affirmative* signal, with a max-attempts bound):
  ```
  for i in $(seq 1 60); do
    matched=$(gh run list --json status,headSha --jq "[.[] | select(.headSha == \"$SHA\")] | length")
    [ "$matched" -gt 0 ] || { echo "no runs match SHA $SHA"; exit 1; }
    pending=$(gh run list --json status,headSha --jq "[.[] | select(.headSha == \"$SHA\") | select(.status != \"completed\")] | length")
    [ "$pending" = "0" ] && break
    sleep 15
  done
  ```

The fix: verify the filter matches something on iteration 0 (`matched > 0`),
and bound the loop so a stuck condition is reported instead of silently
draining wall time.

---

## jq-select-filter-with-hardcoded-literal-in-flow-control

```
jq '[.[] | select(.field == "long-literal")] | length' ...
```

A hardcoded long literal (SHA, run ID, branch name, PR number, anything
8+ chars and typo-prone) used as the filter pivot is fragile because any
typo silently produces an empty result. When that result feeds control
flow — a count test, a loop termination, a "did we find it" decision —
the typo becomes silent fake-success.

- Wrong: `jq 'select(.headSha == "1e42771447c81fb6a96b2d3eef3e16df9f8517b3")'`
- Right: `jq --arg sha "$(git rev-parse HEAD)" 'select(.headSha == $sha)'`

The fix: never hardcode the literal. Derive it at runtime via
`$(git rev-parse ...)`, `${VARIABLE}`, or `--arg`/`--argjson` for jq.
This way a wrong value fails loudly (variable empty, command errors)
instead of silently filtering to nothing.

---

## count-piped-into-test-against-zero

```
[ "$(... | length)" = "0" ]
[ "$(... | wc -l)" = "0" ]
```

Same shape as the `until` loop above but as a standalone test. The
0-equals-0 vacuous match makes "I confirmed there are no matches"
indistinguishable from "I asked the wrong question".

- Wrong: `[ "$(gh pr list --search "head:$BRANCH" --json number --jq length)" = "0" ] && echo "no PR open"`
- Right:
  ```
  pr_list_json=$(gh pr list --search "head:$BRANCH" --json number)
  [ "$pr_list_json" = "[]" ] && echo "no PR open"
  ```

Or assert the upstream query produced expected shape before testing:

  ```
  gh pr list ... > prs.json
  jq -e 'type == "array"' prs.json >/dev/null || { echo "query failed"; exit 1; }
  [ "$(jq length prs.json)" = "0" ] && echo "no PR open"
  ```

---

## interactive-editor-or-full-screen-tui

```
vim                      nano        top
nvim file.txt            emacs       htop
```

An interactive editor, pager-that-pages, or full-screen TUI opens
`/dev/tty` and blocks for keyboard input. A background task has no
controlling terminal, so the read never returns — the command hangs
forever and the completion notification never fires.

Flagged programs: `vim`, `vi`, `nvim`, `nano`, `pico`, `micro`, `joe`,
`emacs`, `emacsclient`, `vimdiff`, `top`, `htop`, `btop`.

- Wrong: `vim notes.txt` (in background)
- Wrong: `top`
- Right (non-interactive edit): `sed -i 's/old/new/' notes.txt`
- Right (one-shot process sample): `top -l 1` (macOS) / `top -b -n1` (Linux)
- Right (scripted vim): `vim -es -c '...' -c 'wq' file` or `nvim --headless ...`
- Right (emacs script): `emacs --batch -l script.el`

The escape flags above (`-l`/`-b` for top, `-es`/`-Es`/`--headless` for
vim/nvim, `--batch` for emacs, `--eval`/`-e` for emacsclient) make the
program non-interactive, so they are NOT rejected.

`less`, `more`, `man` are deliberately absent — they detect non-TTY
stdout and stream like `cat`, so they do not hang.

---

## git-subcommand-that-opens-an-editor

```
git commit                 # no -m → opens $EDITOR → hangs
git commit --amend         # no -m / no --no-edit → opens $EDITOR
git rebase -i HEAD~3       # opens the todo-list editor
git tag -a v1.0            # annotated tag, no -m → opens $EDITOR
```

When git needs a message and none is supplied on the command line, it
launches `$EDITOR`/`$GIT_EDITOR` (default `vi`). In the background that
editor opens `/dev/tty` and blocks forever. Confirmed: `git commit` with
`EDITOR` set to vim, nano, or unset all hang; `git commit -m ...` and
`EDITOR=cat git commit` terminate.

- Wrong: `git commit`
- Wrong: `git commit --amend`
- Right: `git commit -m "feat: message"`
- Right: `git commit --amend --no-edit`
- Right: `git commit -F message.txt`
- Right (interactive rebase becomes non-interactive): set
  `GIT_SEQUENCE_EDITOR=true` / `GIT_EDITOR=true`, or avoid rebasing in the
  background entirely.

`git add -p` is NOT flagged — with stdin at EOF it reads no hunks and
aborts cleanly instead of hanging.

---

## lingering-daemon-or-service (advisory, not a hard deny)

```
rebuild                    systemctl start foo
darwin-rebuild switch      launchctl bootstrap ...
home-manager switch        brew services start foo
```

This one is an **advisory** (the hook emits a `systemMessage` and still
allows the command), because starting a service is sometimes intended.

The background-bash harness marks a task complete only when the command's
**entire process group/session exits** — not when the foreground command
exits, and not when its stdout pipe reaches EOF (confirmed empirically:
redirecting a child's fds away from the pipe does not change the wait;
moving the child into a new session does). So a command that finishes its
own work but leaves a child alive in the same session — a restarted
service, a build daemon, an activation step — makes the task hang even
though the command succeeded. `rebuild` is the canonical case: the script
prints `rebuild complete` and exits, but a restarted launchd/systemd
service keeps the group alive.

Two fixes, use either or both:

1. **Detach into a new session and poll a log marker** (most robust):
   ```
   launch-command-detached-into-new-session /tmp/rebuild.log rebuild
   # then poll /tmp/rebuild.log for the success/failure marker:
   #   grep -q "rebuild complete" /tmp/rebuild.log
   ```
   The wrapper runs the command via setsid, redirects output to the log,
   and returns immediately, so the harness never waits on the command or
   its daemons. You decide completion from the log marker, not the task
   notification.

2. **Key off the log marker instead of the completion notification.**
   Even without the wrapper, treat a known success line in the output file
   (`rebuild complete`, a server's "listening on", etc.) as the real
   completion signal. The task-completion notification is unreliable for
   anything that spawns a lingering child.

---

## General mitigations

When `run_in_background: true`, design the command so that:

1. **The first iteration of any polling loop verifies the filter matches something.**
   If you're waiting for state X to clear, first confirm state X exists.
2. **Terminate on an affirmative signal, not on an empty set.**
   "I saw all N completed" is more robust than "I saw 0 pending".
3. **Bound polling loops with a max-attempts counter.**
   Silent infinite polls and silent vacuous exits look the same from outside.
4. **Don't hardcode multi-character identifiers (SHAs, IDs, branch names).**
   Derive them at runtime so a wrong value fails loudly.
5. **At the end, print a terminal positive signal** ("completed: <summary>").
   Empty output should always be suspicious.
