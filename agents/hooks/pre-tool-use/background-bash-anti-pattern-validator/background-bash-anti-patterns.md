# Background Bash — denied shapes

Every rule here is a hard deny on `run_in_background: true`. The denial names
the rule; find it below, take the right-hand shape, retry. Nothing here is
advice you may weigh.

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

## Still allowed

Servers, `tail -f`, `journalctl -f`, `watch`, long `sleep`s: legitimate
background work, and the intended replacement for the Monitor tool. Pagers
(`less`, `more`, `man`) and `git add -p` detect the non-TTY and exit on their
own.
