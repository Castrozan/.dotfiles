<behavior_contract>
Describe each candidate as one behavior contract: intended outcome; trigger, action, material exceptions; required
audience and scope; required lifetime; and the observable result. Similar wording, shared vocabulary, a prior fix, or a
test name only nominates a candidate. Split contracts whose trigger, exception, scope, or authority threshold differs.
</behavior_contract>

<runtime_trace>
Trace the declared source, canonical owner, generated copy, deployment edge, runtime injection tier, session cache,
resume and compaction behavior, mutable state, deterministic control, and behavioral evidence. Inspect the live prompt,
process, or file when available. A committed source that the runtime never loads is absent authority; a seed that leaves
existing state untouched is not managed delivery; a generated copy is not another owner.
</runtime_trace>

<owner_selection>
Apply core `<instruction_placement>` after the trace, not before it. Put universal session-long behavior in core,
repository and path policy in local context, harness mechanics at that harness boundary, and a procedure that starts and
ends with one bounded operation in its skill. Use a hook, permission, CI, or operating-system boundary only when its
predicate and every material exception are precise. Do not move a scoped rule merely because several files mention it.
</owner_selection>

<relationship_classification>
Classify every related surface as canonical authority, generated copy, linked complement, deterministic control,
behavioral evidence, historical evidence, or competing authority. A complement adds narrower procedure or a material
exception and points to the canonical rule. A competing source independently decides the same behavior. Reject the
favored classification when live delivery, a different trigger, or a narrower scope disproves it.
</relationship_classification>

<migration>
Establish the new authority and its runtime delivery before deleting the old one. Replace competing prose with an
explicit pointer, retain only scoped procedure and exceptions, and migrate existing mutable state by an exact owned
key, prefix, or version while preserving unknown state. Keep delivery, enforcement, and evidence separate. Do not claim
migration from source shape alone when a resumed session or mutable store can retain the retired rule.
</migration>

<verification>
Prove structure, canonical uniqueness, deployment equality, and live injection independently. Test a fresh session and
the required resume or compaction horizon. Use an ordinary request that does not name the rule for behavioral evidence,
plus an exception case when enforcement exists. Inspect the resulting artifact or action and bound the claim to what
the test exercised; one green response is short-term regression evidence, not long-horizon adherence proof.
</verification>
