# Background Bash — silent fake-success patterns

A Bash command launched with `run_in_background: true` reports completion
via a single task-notification with an exit code, then the LLM reads
the output file. If the command exits 0 with empty/wrong output, the
notification looks identical to genuine success and the LLM has no
in-band signal that something went wrong.

The patterns below produce exactly that shape: exit 0, empty output,
notification fires, but the command never actually did its job because a
filter matched nothing — often due to a typo, a fabricated literal, or
an unset variable.

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
