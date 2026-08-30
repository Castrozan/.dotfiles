<adaptive_implementation_delivery_process>
Apply core `<delegation>` to choose the lightest safe execution shape, then map it to these Claude-specific tiers:
direct answers touch no file and spawn no agent; patch changes one or two files alone; guided changes a handful with at
most two agents; orchestrated is five or more files, or any auth, data, or public-interface change at any file count,
and is the only tier that spends a third agent. Risk outranks counts, so a two-file auth change is orchestrated. A user
request for `AIDP patch` or the lightest safe AIDP mode overrides the mapping.
</adaptive_implementation_delivery_process>

<how_the_ceiling_holds>
A PreToolUse guard counts subagent spawns per interactive session and denies the third while the session is still below
orchestrated, so no tier below it costs you a word of ceremony. Unlock the rest of the session by re-attempting that
denied spawn with the `Agent` description starting with `orchestrated:` and the trigger that earned it. The triggers are
more than two modules, requirements you cannot restate, data or security impact, or a new public interface. Never
escalate because a task sounds important, and de-escalate out loud when the reason stops holding. Lower a delegate's
effort before lowering its model.
</how_the_ceiling_holds>

<mid_task_asks>
Classify before acting. refine: do it. separate: its own task after this one. expand: finish the agreed scope, then name
it. conflict: stop and ask.
</mid_task_asks>

<roles>
Core `<delegation>` retains requirements, architecture, judgment, verification, and synthesis with the owning agent. In
this process, review delegated work from names and function shape through module placement and system design, request
changes until it is right, then apply, deploy, merge, and confirm it live. At direct and patch tiers implement and
verify alone, loading `architecture`, `coding`, and `review` to hold the same standard.
</roles>
