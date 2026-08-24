<when_to_use>
Use this when the user wants an existing instruction file made better rather than checked: core rules, a SKILL.md and
its chapters, CLAUDE.md at any depth, or an agent definition. Auditing a change against the authoring standards belongs
to the `review` skill's instruction-authoring chapter instead. This chapter owns the sentence-level breakdown and the
refinement pass the user drives from it.
</when_to_use>

<break_it_down_before_proposing_anything>
Read the whole file and never work from a summary of it. Split it by its own structural tags, split each section into
sentences, and index those sentences continuously across the entire file. Never restart the numbering inside a section:
the user answers by row number, and a repeated number makes every instruction they give ambiguous. Present one table per
section with four columns, being the continuous index, the sentence, its category, and the act it names or the lesson it
carries when it names none. Quote each sentence verbatim, or its leading clause when the row would otherwise be
unreadable, so the user can find it in the file without searching.
</break_it_down_before_proposing_anything>

<the_categories_and_why_forcing_them_is_the_point>
Sort every sentence into exactly one of five. An action names something an agent can be seen doing or failing to do.
Wisdom changes how something is weighed and needs another rule before it becomes observable. A mixed sentence teaches in
one clause and acts in another. An exception lifts or narrows a rule above it. Scope names the trigger that arms a
section. The sorting is the diagnostic and the label is only its record, so a sentence that resists every category is
almost always doing two jobs and should be split rather than answered with a sixth category. Judge by whether an act
follows, not by whether the wording sounds imperative: "treat this as evidence, not proof" is phrased as an order and
still names nothing to do.
</the_categories_and_why_forcing_them_is_the_point>

<report_the_shape_not_a_verdict>
Give the count per category and say where the wisdom clusters, then stop. Wisdom is not a defect. Some judgment cannot
be made mechanical, and a file carrying none of it has usually pushed that judgment somewhere less visible rather than
removed it. Make the shape legible enough for the user to decide, and leave the deciding to them.
</report_the_shape_not_a_verdict>

<let_the_user_drive_by_index>
Hand the tables over and take instructions by row number: drop, rewrite, move to another surface, or justify. Read "give
me a reason to keep this" as an invitation to argue the strongest case you have, not as a decision already taken. Put
the consequential calls to the user before applying any of them, one question per open fork, each carrying your
recommendation. The forks worth asking about are the ones invisible from the table: a drop whose behavior has no other
home, a rewrite that changes what a downstream file points at, and an addition whose placement is arguable.
</let_the_user_drive_by_index>

<ground_every_decision_before_you_apply_it>
No drop, rewrite or move is free. Before editing, search for whatever asserts, references or duplicates each sentence:
a test matching its wording, a size or required-section guard, another instruction file naming it as the owner, and any
evaluation whose prompt depends on it. Report what you found beside the decision, because an edit that breaks a guard or
orphans a pointer is a different decision than the user believed they were making. Repair the orphaned pointer inside
the same change instead of leaving a file that claims an owner no longer stating the rule.
</ground_every_decision_before_you_apply_it>

<renumber_and_recount_after_editing>
Rewrites move the index. One sentence split into three shifts every row after it, and a cross-reference written into a
row is wrong the moment that happens. Recount the sentences from the edited file rather than deriving a total from the
drop list, and repeat the per-section counts so the user sees what the file became instead of what it was meant to
become.
</renumber_and_recount_after_editing>
