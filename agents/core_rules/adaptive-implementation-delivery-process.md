<adaptive-implementation-delivery-process>
Pick the lightest tier that safely satisfies the task and declare it before spawning any agent or opening a multi-file
change. "use AIDP patch" or "use the lightest safe AIDP mode" from the user overrides your pick.
direct: answer only, no files, no agents.
patch: 1-2 files, 0 agents, under 10 minutes.
guided: 2-5 files, max 2 agents, 10-25 minutes.
orchestrated: 5+ files, or any auth, data or public-interface change at any file count.
Risk outranks the counts: a two-file auth change is orchestrated.
</adaptive-implementation-delivery-process>

<escalation>
Default zero subagents, ceiling two until orchestrated. Escalate only on more than two modules, requirements you cannot
restate, data or security impact, or a new public interface. Never escalate because a task sounds important.
De-escalate out loud when the reason stops holding.
</escalation>

<delegated-work>
Every delegated task carries goal, allowed files, out of scope, acceptance criteria, validation method and stop
conditions. A subagent that hits a stop condition reports and stops instead of improvising something adjacent.
</delegated-work>

<acceptance>
Gate in order: scope, design, test, review. Accept only on passing criteria with evidence, no unscoped file touched and
residual risk named. Compiling is not evidence.
</acceptance>

<mid-task-asks>
Classify before acting. refine: do it. separate: its own task after this one. expand: finish the agreed scope, then
name it. conflict: stop and ask.
</mid-task-asks>

<model-tier>
The interactive lead stays Opus; tier the volume around it.
haiku: mechanical high-volume work, searches, sweeps, collecting output.
sonnet: implementation and tests where the design is already settled.
opus: design, subtle debugging, adversarial verification, final review.
Escalate a rung only after the cheap tier failed review twice or the work turned out to need judgment. Lower effort
before lowering the model.
</model-tier>
