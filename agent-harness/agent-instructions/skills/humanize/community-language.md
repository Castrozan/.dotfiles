<community-language-calibration>
Use these examples as evidence for readable choices, not as templates to copy. Select the nearest reader task only after
the facts, audience, and required action are known. Preserve project vocabulary and the reader's demonstrated register.
Keep a precise technical term when plain wording would change its meaning, and define it at first use when the reader
may not know it. If an example conflicts with the Humanize policy or the source facts, the policy and facts win.

<example-selection>
Use explain when the reader needs a mechanism; diagnose when evidence must be separated from a cause; decide when
trade-offs select an option; warn when a condition changes safe action; report when measured state or change matters;
summarize when the reader needs one conclusion or action. Use only the example family that matches the task. Do not make
every reply sound casual, copy an example's cadence, or add a visual when prose already carries the relationship.
</example-selection>

<explain-by-contrast>
Show the same system before and after when the changed mechanism is the point. Put each number beside the step that
produced it, label the artifact handed across the boundary, and let the prose interpret the contrast without repeating
the figure.

<explain-example-one>
The whole trick: the review used to rediscover its own diff one file per round trip, and the `maxTurns: 8` that looked
like a ceiling was never a real option, so nothing stopped it. Now the first pass writes the entire patch in one command
and hands the second pass that file path, so both passes read the same bytes instead of deriving them again. Model and
effort are pinned on each call because those are the controls the runner actually honours.

```
BEFORE (738 s, hit the 600 s ceiling)      AFTER (~405 s, completes)

Review  haiku, maxTurns:8 = ignored        Review  haiku, effort low
  git diff -- fileA   -+                     Bash x1  whole patch -> /tmp/...XXXXXXXX
  git diff -- fileB    |  39 per-file        Read x1  27 KB patch in context
  ... x39              |  diffs                   |
  194 turns / 95 calls -+                         | returns
                                                  |  { repoRoot, changedFiles, patchPath }
Verify  sonnet                                    v
  rediscovers the same diff                Verify  sonnet, effort medium
  81 turns / 53 calls                        Read x1  the SAME patchPath
                                             22 turns / 11 calls

275 turns . 148 tool calls                 37 turns . 17 tool calls
97 % of it waiting on round trips          round trips collapsed to 2
```

Two passes and two model calls, unchanged: the second still refutes the first independently, it just no longer pays to
find the diff twice.
</explain-example-one>

<explain-example-two>
Input: explain eventual consistency when a successful write reaches replicas within two seconds. Output: "After the API
accepts a write, a read from another replica can return the previous value for up to two seconds. Retry the read when
the caller needs the new value immediately." This keeps the technical term available but explains the observed behavior,
time limit, and caller action instead of substituting an abstract definition.
</explain-example-two>
</explain-by-contrast>

<diagnose-from-evidence>
State what was observed before naming a possible cause. Say what evidence cannot establish, then name the cheapest probe
or reversible response that changes the decision.

<diagnose-example-one>
Input: latency rose after a cache deploy, key churn is suspected, and no key-cardinality metric exists. Output: "Latency
rose after the cache deploy. The timing makes that deploy a candidate cause, but the logs do not show key churn. Capture
key cardinality before treating churn as the diagnosis. Roll back now only if the current latency costs more than that
measurement window." The output separates evidence, hypothesis, missing evidence, and decision.
</diagnose-example-one>

<diagnose-example-two>
Input: a backup failed with permission denied, but the record does not identify whether the scheduler or uploader writes
the archive. Output: "The archive write was denied. The record does not identify the writer, so it cannot tell us which
permission is wrong. Trace the process that opens the archive, then inspect that process's effective identity." The
output exposes the unresolved actor instead of inventing one.
</diagnose-example-two>
</diagnose-from-evidence>

<decide-by-tradeoff>
Compare only criteria that can change the choice. Give the recommendation after the comparison and tie it to the stated
constraint, not to a generic ranking.

<decide-example-one>
Input: choose SQLite or PostgreSQL for one local writer today with concurrent writers expected next quarter. Output:
"Choose PostgreSQL because concurrent writes are already a dated requirement. SQLite has the smaller local setup, but a
later database migration would cost more than configuring PostgreSQL now." The recommendation names the deciding
constraint and keeps the losing option's real advantage.
</decide-example-one>

<decide-example-two>
Input: choose a rolling restart or full restart when five nodes serve traffic and the schema remains compatible. Output:
"Use a rolling restart. The compatible schema lets old and new nodes overlap, so capacity stays available during the
change. Use a full restart only if runtime evidence shows mixed versions cannot interoperate." The exception is attached
to the condition that would reverse the choice.
</decide-example-two>
</decide-by-tradeoff>

<warn-with-condition>
Put the hazard before the action when it changes what the reader may safely do. Name the actor, threshold, wait, or
sequence explicitly. Never weaken a prohibition to make the sentence friendlier.

<warn-example-one>
Input: a cabinet retains 48 volts for five minutes after disconnection. Output: "Disconnect external power before you
remove the cover. The cabinet can retain 48 volts for five minutes. Wait until the indicator turns off, then verify zero
volts before you touch a terminal." The output preserves the voltage, duration, actor, and required sequence.
</warn-example-one>

<warn-example-two>
Input: retry SQLSTATE 40001 at most twice, never retry permission errors, and the second retry can increase lock
contention. Output: "Retry only SQLSTATE 40001, at most twice. Never retry a permission error. Before the second retry,
check whether higher lock contention is acceptable." The shorter wording retains every operational limit.
</warn-example-two>
</warn-with-condition>

<report-measured-change>
Lead with the measured result and its scope. Remove claims of importance that the evidence does not establish. Mark a
missing fact instead of inventing a number to make the report sound concrete.

<report-example-one>
Input: a migration reduced median build time from 11 minutes to 7 minutes in measured CI jobs. Output: "The migration
reduced median build time from 11 minutes to 7 minutes in the measured CI jobs." No milestone, transformation, or team
praise improves the result; the measurement and scope carry the report.
</report-example-one>

<report-example-two>
Input: churn rose for a second quarter, the percentage is absent, and pricing plus onboarding are candidate causes.
Output: "Churn rose for a second quarter [add the measured change]. The March pricing change and onboarding drop-off are
candidate causes, not confirmed causes. Test those first." The placeholder exposes missing evidence without fabricating
precision.
</report-example-two>
</report-measured-change>

<summarize-for-action>
State the answer or action first. Keep only the cause, condition, or limit needed to use it correctly. A summary may be
short, but it cannot discard the fact that would make the action unsafe or wrong.

<summarize-example-one>
Input: each review pass searched for the same diff, and the fix writes it once for both passes without changing review
logic. Output: "TL;DR: each review pass searched for the same diff again. The workflow now writes it once and gives both
passes the same file. The two independent reviews did not change." The summary carries mechanism and invariant in plain
language.
</summarize-example-one>

<summarize-example-two>
Input: two of ten canaries fail health checks, the remaining eight are healthy, and rollout must wait for diagnosis.
Output: "Pause the rollout. Two of ten canaries fail health checks; the other eight are healthy. Diagnose those two
before deploying another batch." The action, evidence, scope, and next step remain recoverable.
</summarize-example-two>
</summarize-for-action>

<meaning-recovery-check>
Before delivery, verify that the reader can recover the conclusion, actor, action, conditions, evidence, limits, and
next step that matter for this task. Revise an ambiguity that changes action. If the reader can already recover those
parts, do not add background, synonyms, a visual, or another example merely to make the answer look complete.
</meaning-recovery-check>

<community-provenance>
The patterns are synthesized from MIT-licensed sources pinned at
`humanlayer/skills@3c2629142c5d437428269b1b722b08c0b87f574d`,
`forjd/better-writing@4023076319e5a7838dd7587ebf3d5e3588f9544f`,
`phb123/ste@9ddbe815e1ffe0d994d3dff6e4060df52e26dab3`, and
`blader/humanizer@523374dee72d67c7b2b5f858ea0094ffda49c3ac`. The first explaining example is repository evidence from
`6e909243`, selected by the owner after using it in an interactive session. Upstream changes never update this corpus
automatically. Promote a new pattern only after human review and a transfer evaluation outside its source example.
</community-provenance>
</community-language-calibration>
