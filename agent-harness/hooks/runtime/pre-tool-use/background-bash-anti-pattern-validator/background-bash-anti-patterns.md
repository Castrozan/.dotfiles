# Background Bash — denied shapes

Every rule here is a hard deny about where a command runs. All but the last
deny a shape on `run_in_background: true`; the last denies a shape that must
not run in the foreground. The denial names the rule; find it below, take the
right-hand shape, retry. Nothing here is advice you may weigh.

Two failure modes justify the wall. A shape that **exits 0 with empty output**
is indistinguishable from success, so a typo'd filter reads as a clean result.
A shape that **never exits** never fires the completion notification, so the
task is stuck: the harness waits on the whole process group, not on the
command, and neither closing the stdout pipe nor reparenting the child ends
that wait (both confirmed empirically).

## until-loop-terminating-on-empty-count

- Wrong: `until [ "$(... | jq length)" = "0" ]; do sleep N; done`
- Right: bound the loop with `for i in $(seq 1 N)`, assert the filter matched
  something on the first pass, then break on the affirmative signal.

## jq-select-filter-with-hardcoded-literal-in-flow-control

- Wrong: `jq 'select(.headSha == "1e42771447c...")'`
- Right: `jq --arg sha "$(git rev-parse HEAD)" 'select(.headSha == $sha)'`

A typo'd literal filters to nothing silently; a derived one fails loudly.

## count-piped-into-test-against-zero

- Wrong: `[ "$(... | length)" = "0" ]`
- Right: capture the payload first and test its shape (`= "[]"`, or
  `jq -e 'type == "array"'`) before trusting a zero.

## interactive-editor-or-full-screen-tui

- Wrong: `vim file`, `top`
- Right: the program's non-interactive flag (`top -l 1`, `nvim --headless`,
  `emacs --batch`), or a non-interactive tool (`sed -i`).

## git-subcommand-that-opens-an-editor

- Wrong: `git commit`, `git commit --amend`, `git rebase -i`, `git tag -a v1`
- Right: supply the message inline (`-m`, `-F`, `--no-edit`), or set
  `GIT_EDITOR=true` / `GIT_SEQUENCE_EDITOR=true`.

## lingering-daemon-or-service

- Wrong: `rebuild`, `systemctl start foo`, `launchctl bootstrap ...`,
  `home-manager switch`, `brew services start foo`
- Right: run it in the foreground, where the harness waits on the command and
  not on a group its children hold open. If it must be detached, use
  `launch-command-detached-into-new-session <log> <command>` and poll the log
  for the command's own success marker.

Starting the service is fine. Asking a background task to wait on one is not:
the restarted daemon keeps the group alive past the command's own success.

## peer-wait-without-liveness-exit

Applies to backgrounded Bash and to Monitor. A loop that reads a peer agent's
state (`orchestrator report show`, `herdr agent read`, `herdr pane read`,
`a2a status`, `a2a inbox`) must also leave when the peer is gone. A closed pane
freezes everything the loop reads, so the loop sits silent until its cap, or
forever.

- Wrong: `until orchestrator report show <peer> | grep -q done; do sleep 45; done`
- Right: put a liveness probe in the exit condition and say why the loop ended:

```
n=0
until orchestrator report show <peer> | grep -q done \
  || ! herdr pane get <pane> >/dev/null 2>&1 || [ $n -ge 80 ]; do
  sleep 45; n=$((n+1))
done
herdr pane get <pane> >/dev/null 2>&1 || echo "PEER-GONE: pane <pane> closed"
orchestrator report show <peer>
```

Probes that count, inside the loop: `herdr pane get`, `herdr pane list`,
`herdr pane process-info`, `herdr agent get`, `herdr agent list`, `a2a list`,
`kill -0`, `pgrep`, `ps -p`. A probe that runs only after the loop is not an
exit.

## peer-event-stream-outside-monitor

- Wrong: `orchestrator watch --workspace <id>` with `run_in_background: true`
- Right: the same command under the Monitor tool.

Backgrounded Bash notifies once, when the command exits, and this stream never
exits. Monitor delivers each line as an event.

## Allowed background waits

A backgrounded command that waits is allowed only in one of these shapes:

- A native blocking wait: `herdr agent wait <pane> --until done --timeout <ms>`,
  a CI watcher, `wait <pid>`.
- `peer-event-stream-under-monitor`: `orchestrator watch` under Monitor.
- `peer-poll-with-liveness-exit`: the loop above.
- `condition-poll`: a sleep-paced loop over a process, file, CI run or
  endpoint, with no peer read in it.

One-shot jobs that do not loop (a build, a test run, a server) are not waits
and stay allowed.

## foreground-wait-on-ci

- Wrong: `gh run watch <id>`, `gh pr checks <n> --watch`
- Right: background the same command and let the harness report its exit, or
  poll `gh run list --commit <sha> --json name,conclusion` when a verdict is
  actually due.

The wait is minutes long, and every progress redraw it prints lands in the
context. Backgrounded it costs nothing; in the foreground it buys dead time
with tokens. Reading about a run stays allowed: `gh run list`, `gh run view`,
`gh run watch --help`, and grepping for the string all pass.

## foreground-ci-polling-loop

- Wrong: `for i in $(seq 1 25); do gh run list ... ; sleep 40; done`
- Right: background the same loop, or run one `gh run list --commit <sha>` when
  the verdict is due.

Hand-rolling the wait out of a loop, a query and a `sleep` costs exactly what
`gh run watch` costs, so it is denied on the same grounds. A loop that sleeps
and re-queries CI trips this; a single query does not, and neither does the
same loop backgrounded.

## Still allowed

Servers, `tail -f`, `journalctl -f`, `watch`, long `sleep`s: legitimate
background work, and the intended replacement for the Monitor tool. Pagers
(`less`, `more`, `man`) and `git add -p` detect the non-TTY and exit on their
own.
