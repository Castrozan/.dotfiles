# Background Bash — denied shapes

Every rule here is a hard deny. Most deny a shape on `run_in_background: true`;
`sleep-paced-loop` and `fixed-delay` deny waiting by sleeping in every context
and harness, and `foreground-wait-on-ci` and `foreground-event-wait` deny a
wait that must not run in the foreground. The denial names the rule; find it
below, take the right-hand shape, retry. Nothing here is advice you may weigh.

No wait is polled. Every wait blocks on an event, runs backgrounded or under
Monitor, and the agent keeps working until the harness notifies it.

Two failure modes justify the wall. A shape that **exits 0 with empty output**
is indistinguishable from success, so a typo'd filter reads as a clean result.
A shape that **never exits** never fires the completion notification, so the
task is stuck: the harness waits on the whole process group, not on the
command, and neither closing the stdout pipe nor reparenting the child ends
that wait (both confirmed empirically).

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
  `launch-command-detached-into-new-session <log> <command>` and block
  on `wait-for-event process <printed pid>`, then read the log.

Starting the service is fine. Asking a background task to wait on one is not:
the restarted daemon keeps the group alive past the command's own success.

## sleep-paced-loop and fixed-delay

Applies to foreground Bash, backgrounded Bash and Monitor on every harness. A
delay is an executed `sleep N` or `gsleep N`, a `python -c` program that only
sleeps, `watch`, a `read -t N` whose input is discarded (`_` or `</dev/null`),
and `timeout N` around a command that never ends on its own (`sleep infinity`,
`tail -f /dev/null`), including inside `bash -c` and behind `timeout`, `nohup`
or `env`. A delay inside a `while`/`until` loop, a counter loop, or a loop with
`break` is `sleep-paced-loop`; any other delay of a second or more is
`fixed-delay`. Both guess when the change lands and stall past it. A cap on the
loop does not make it an event. The denial names what the command read and the
event that ends the same wait:

| Waited on | Wait on this instead |
| --- | --- |
| background task output file | the harness's completion notification |
| CI run | `ci-watcher <run-id>`, backgrounded |
| peer agent | `herdr agent wait`, `orchestrator watch` under Monitor, `a2a ask`; one `orchestrator status` read when due |
| pane output | `herdr pane wait-output <pane> --match <text>` |
| process exit | background the command, or `wait-for-event process <pid>` |
| service | `systemctl start` (notify units), `wait-for-event process <MainPID>`, `docker wait` |
| desktop window | `hypruse wait_for window_open --match <title>` |
| browser page | `navigate_page` already waits for load; `evaluate_script` a MutationObserver promise |
| local endpoint | `wait-for-event file <log> --match <ready line>`, or `curl --retry-connrefused` |
| file content | `wait-for-event file <path> --match <regex>` |
| merge request | backgrounded `ci-watcher <pipeline-id>`, then one read; auto-merge when waiting to merge |
| remote API | one read when due, or one backgrounded `curl --retry N --retry-all-errors` |

Named exceptions, the only delays allowed:

- `sub-second-input-pacing`: delays under one second outside any polling loop,
  such as gaps between synthetic key or pointer events.
- Not delays at all: `timeout N <cmd>`, a tool's own interval or retry flag
  (`gh run watch --interval`, `curl --retry-delay`, `nvidia-smi --loop`),
  `sleep infinity`, and sleep text the shell never runs (quoted arguments,
  heredoc bodies written to files, a program's own logic in a script file).

## peer-event-stream-outside-monitor

- Wrong: `orchestrator watch --workspace <id>` with `run_in_background: true`
- Right: the same command under the Monitor tool.

Backgrounded Bash notifies once, when the command exits, and this stream never
exits. Monitor delivers each line as an event.

## Allowed background waits

A backgrounded command that waits is allowed only in one of these shapes:

- A native blocking wait: `herdr agent wait <pane> --until done --timeout <ms>`,
  `ci-watcher`, `wait-for-event`, `wait <pid>`.
- `peer-event-stream-under-monitor`: `orchestrator watch` under Monitor.

One-shot jobs that do not loop (a build, a test run, a server) are not waits
and stay allowed.

## foreground-wait-on-ci

- Wrong: `gh run watch <id>`, `gh pr checks <n> --watch`
- Right: background `ci-watcher <run-id>` and let the harness report its exit,
  or read `gh run list --commit <sha> --json name,conclusion` once when a
  verdict is actually due.

The wait is minutes long, and every progress redraw it prints lands in the
context. Backgrounded it costs nothing; in the foreground it buys dead time
with tokens. Reading about a run stays allowed: `gh run list`, `gh run view`,
`gh run watch --help`, and grepping for the string all pass.

## foreground-event-wait

Claude Code only, where Bash can run in the background.

- Wrong: `herdr agent wait <pane> --until done`, `herdr pane wait-output <pane>
  --match X --timeout 600000`, `wait-for-event process <pid>`, `docker wait
  <name>`, `hypruse wait_for ... --timeout 60`, `ci-watcher <run>` in the
  foreground
- Right: the same command with `run_in_background: true`; keep working and act
  on the completion notification.

A blocking wait is the right primitive and the wrong place: in the foreground
it parks the session for the whole wait. Only a wait bounded to 30 seconds or
less, by a `timeout` wrapper or the tool's own timeout flag, stays in the
foreground, as a short synchronization such as waiting for a window before a
screenshot. A CI wait never qualifies.

## Still allowed

Servers, `tail -f` and `journalctl -f` are legitimate background work and the
intended input for the Monitor tool. Pagers (`less`, `more`, `man`) and
`git add -p` detect the non-TTY and exit on their own.
