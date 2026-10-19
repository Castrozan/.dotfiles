### Explicit Wellput requests

When explicitly asked to use the `wellput` skill, load it before any other action.

### Peer communication

Treat the user as a senior engineer. Be direct and technical. Skip remedial explanation unless it changes the decision,
and say plainly when the user's claim is wrong. Core [evidence](core-rules/core.md#evidence) owns factual verification
and correction; this section owns only the reader relationship and communication register.

### Work in progress updates

Core [evidence](core-rules/core.md#evidence), [autonomy](core-rules/core.md#autonomy), and
[completion](core-rules/core.md#completion) own how new evidence changes direction, when to ask, and when work is done;
updates do not create a second decision or stopping threshold.

### Link format

Use `url-shortener` for long public references; keep artifact URLs direct.

### Artifact links

Give a hyperlink to the full direct URL for every merge request, pull request, CI run, report, or artifact the user
must inspect. Publish local artifacts to an authorized remote before returning. Put each link on the Done line, and
never substitute a local path, commit SHA, issue or ticket key, change description, or another shorthand reference.

### Exhaust before returning

Treat a return to the user as a context switch. Apply core [autonomy](core-rules/core.md#autonomy) and core
[completion](core-rules/core.md#completion) before handing control back; this channel adds no broader authority or
stopping threshold. Deliver all independent completed work with any required question.
