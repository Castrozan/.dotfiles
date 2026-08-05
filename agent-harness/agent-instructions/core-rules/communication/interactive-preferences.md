<interactive-session>
These rules apply only while the user is actively driving the session at the keyboard, never to background agents,
clawde, headless runs, or subagents. Universal agent behavior lives in core.md and still applies here on top of these
rules. These preferences exist because the user is multitasking across several live sessions and rebuilds context from
each reply, so the reply template holds on every turn and never lapses as the conversation grows long.
</interactive-session>

<wording_judgment>
For the wording judgment no checker can make, load the humanize skill.
</wording_judgment>

<artifact_links>
Anything the user validates elsewhere, an MR, PR, ticket, issue, deploy, or published page, belongs on the Done line so
they click straight through instead of hunting for it. A local commit they read by its sha needs only the sha.
</artifact_links>

<exhaust-before-returning>
Returning to the user costs them a context switch, so earn it. Before handing control back, exhaust every available
capability: investigate with the tools, make reasonable decisions on judgment calls, and complete the whole task end to
end. Do not bounce back with questions that investigation or a sensible default can resolve, and do not stop at the
first checkpoint. Return only when the task is genuinely done, or when blocked by a true ambiguity that would send the
work in the wrong direction, or before an irreversible action that needs sign-off. This is the interactive escalation
bar for core's `<questions>` ladder: a human is present to ask, but interrupting is expensive, so only a rung-4 fork
(irreversible-or-owner-only and blocking all remaining work) justifies a stop, and you deliver everything already done
alongside the question.
</exhaust-before-returning>
