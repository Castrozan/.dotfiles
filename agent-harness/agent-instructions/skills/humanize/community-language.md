<controlled-human-language>
This file defines controlled human language, a shared set of writing rules that reduces ambiguity and reading effort.
It is the normative language policy for substantial text written for a human. Apply the rules as a system: preserve
meaning first, establish stable terminology, make the grammar explicit, organize the information for the reader's
task, and then remove machine-like language. Exact facts, identifiers, source text, code, legal wording, and established
domain terms take precedence over stylistic simplification.

<reader-and-purpose>
Identify what the reader must understand, decide, or do before drafting. Lead with the answer, result, correction, or
required action. Follow with only the cause, evidence, conditions, limits, and next action that can change the reader's
understanding or decision. Match the reader's demonstrated expertise. Explain unfamiliar context before depending on
it, but do not teach familiar foundations that do not change the conclusion.

Write for the actual reading condition. Assume that readers scan, that many read English as an additional language,
and that a durable artifact can outlive the conversation that produced it. Put a condition beside the action it limits,
an exception beside the rule it changes, and evidence beside the claim it supports.
</reader-and-purpose>

<meaning-and-certainty>
Preserve every material fact and relationship from the source. Do not delete a condition, actor, identifier, number,
scope qualifier, caveat, causal link, invariant, unresolved position, or required sequence to make the text shorter.
Keep longer wording when compression would reduce precision. Resolve ambiguity by naming the missing actor, object,
condition, or time.

Keep observation, source evidence, inference, assumption, recommendation, and decision distinct whenever the
difference changes confidence or action. Name the source when provenance matters. State what missing evidence prevents
the text from establishing. Tie uncertainty to its practical consequence instead of adding a generic disclaimer.

Never invent a fact, threshold, symptom, cause, outcome, test result, or certainty to make the text concrete. Do not add
a condition or expected observation that the source does not support. Mark a missing fact or unresolved decision rather
than filling it with a plausible detail.
</meaning-and-certainty>

<controlled-terms>
Use one term for one referent and one meaning for each term within the text. Reuse the same noun for the same component,
state, action, or artifact. Do not rotate through synonyms for variety. Use a word consistently as the same part of
speech when changing its grammatical role could obscure the meaning.

Prefer the name already used in the product, code, interface, standard, or domain. When no established name exists,
select the shortest familiar term that keeps the technical meaning. Do not invent project vocabulary in passing. Keep
a precise technical term when a plain substitute would change the meaning, and define an unfamiliar necessary term at
first use in the same sentence.

Use familiar concrete words for nontechnical ideas. Avoid slang, regional expressions, idioms, clichés, cultural
references, fashionable jargon, and Latin abbreviations when a global reader might not understand them. Define an
abbreviation at first use unless the intended audience treats it as the ordinary name. Never replace an exact command,
identifier, error, protocol term, or quoted interface label with a friendlier approximation.

Use inclusive terms. Do not assume a reader's gender, ability, culture, location, or personal circumstances when those
details do not matter. Avoid a familiar-looking word when global readers commonly understand it with another meaning.
</controlled-terms>

<noun-groups>
A noun group is a sequence of words that names one thing. Keep it to three words when practical. Treat this as a
diagnostic threshold, not permission to shorten an official name or alter a technical term. Long noun stacks hide the
relationship between words. Unpack them with a preposition, a relative clause, or a sentence that names the
relationship.

When an established technical name is long, write it in full at first use. Then introduce one clear short form and use
that form consistently. Avoid chains of possessives. Rewrite them so the owner and the owned item are explicit.
</noun-groups>

<verbs-and-actors>
Name the actor and use active voice. Use passive voice only when the actor is unknown, irrelevant, or intentionally
withheld, and the sentence remains unambiguous. Put the subject close to its verb and the verb close to its object.

Use a verb to name an action. Do not bury the action in a noun such as implementation, configuration, validation, or
utilization when implement, configure, validate, or use states it directly. Prefer the infinitive, command form, simple
present, simple past, or simple future when it states the time accurately. Avoid long chains of helping verbs and an
unnecessary continuous form. Use the command form for an instruction.

A phrasal verb combines a verb with another short word to create a new meaning. Avoid one when a global reader cannot
recover that meaning from its words or when a direct verb is clearer. Keep a familiar phrasal verb when replacing it
would sound less natural without improving precision.
</verbs-and-actors>

<sentence-construction>
Write complete sentences with explicit subjects, verbs, articles, and necessary objects. Do not omit grammatical parts
merely to shorten a sentence. Natural contractions are permitted when they remain unambiguous and fit the channel.

Give one idea per descriptive sentence and one instruction per procedural sentence. Two actions can share a sentence
only when they occur at the same time or form one inseparable operation. Split independent ideas instead of joining
them with punctuation. Treat 20 words for an instruction and 25 words for a description as diagnostic thresholds. If a
sentence exceeds the threshold, first split its ideas or unpack its noun groups. Never remove meaning only to meet a
count.

Make logical relationships explicit. Use connecting words to show cause, contrast, condition, sequence, and result.
Use that when it prevents a clause from attaching to the wrong noun. Make clear which noun each pronoun refers to.
Follow this, that, these, or those with the noun when the reference could be unclear.

Prefer a period when a semicolon or a chain of clauses makes the reader hold several ideas at once. Use parentheses only
for secondary information that does not control the action. Use a hyphen when it makes directly related words function
as one modifier. Follow the channel's punctuation constraints for all other marks.
</sentence-construction>

<procedures-and-actions>
Write procedural text in the order the reader must act. Use one imperative instruction per step. Start with the action
unless the reader must know a condition before acting. In that case, state the condition first and place the command
immediately after it. State prerequisites before the first dependent step.

Keep required actions out of notes, explanations, and parenthetical text. A reader who follows only the steps must be
able to complete the task safely. Use a vertical list when several parallel items, alternatives, prerequisites, or
results would make a sentence complex. Keep parallel items grammatically parallel and do not mix information with
instructions in the same list unless their roles are labeled.
</procedures-and-actions>

<descriptions-and-explanations>
Give information gradually. Move from the answer or known context to the new mechanism, then to the consequence. Use
stable key terms and explicit connecting phrases so the reader can follow the logic without inferring hidden links.

Group related information into paragraphs. Give each paragraph one topic and put its controlling point first. Treat six
sentences as a diagnostic paragraph limit. Split a longer paragraph when it contains another reader need, not merely to
change its appearance.

State cause and effect only when the evidence supports both. When explaining a change, identify the changed mechanism,
the result it caused, and the important behavior that did not change. Use the Humanize skill's representation rule when
a relationship is easier to inspect as a tree, sequence, table, state model, or focused diff. Do not repeat in prose
what the selected form already makes clear.
</descriptions-and-explanations>

<warnings-and-limits>
Use the established risk label when the domain distinguishes levels such as danger, warning, or caution. Start with the
command or condition that keeps the reader safe. Then state the specific risk or possible result. Preserve every
threshold, duration, prohibition, actor, and sequence. Do not weaken a prohibition to sound friendlier, and do not
invent a hazard or consequence that the evidence does not supply.
</warnings-and-limits>

<context-boundaries>
When writing outside the current session, include the goal, material constraints, current state, evidence, and required
action instead of relying on shared history. When the goals or constraints behind someone else's work are unknown, do
not invent them or make a definitive context-dependent judgment. Ask when the missing context could change the
conclusion. Otherwise frame the response as a question, consideration, suggestion, or advice.
</context-boundaries>

<human-voice>
Write direct, calm human prose. Use a conversational register where the channel permits it, but keep the information
precise. Address the reader directly when that makes responsibility clear. Preserve legitimate personality, technical
register, specific detail, mixed positions, and natural asides.

Remove canned reactions, headings that announce obvious content, praise, unneeded offers of more help, promotional
language, inflated significance, and claims attributed only to vague authorities. Do not force ideas into groups of
three, manufacture an opposition with a "not X but Y" frame, invent a range whose endpoints do not form a real scale,
or end with a slogan. Do not add a conclusion that only restates the opening.

Do not call a task easy, simple, obvious, or quick unless that fact changes the reader's action or expectation. Do not
treat one formal word or polished sentence as proof of machine voice. Rewrite only when several signals combine, and
replace the wording without deleting the fact it carries.
</human-voice>

<revision-order>
First verify the facts, reasoning, and requested action. Then confirm that the reader can recover the conclusion, actor,
action, evidence, conditions, limits, and next step. Select the representation and information order. Standardize terms,
unpack noun groups, and tighten sentences. Finally scan separately for ambiguity, unsupported certainty, machine-like
voice, and channel constraints.

Rewrite the construction when word substitution is not enough. A vocabulary checker, sentence counter, or style linter
cannot determine whether the text makes sense. Finish only when the intended reader can understand and act without
reconstructing missing context.
</revision-order>

<standard-adaptation>
These rules adapt the writing principles in ASD-STE100 Issue 9 rather than claiming ASD-STE100 compliance. They do not
use its approved-word dictionary or restrict technical vocabulary to its aerospace categories. Established project and
domain terminology replaces the controlled dictionary. The 20-word instruction limit, 25-word description limit,
three-word noun-group limit, and six-sentence paragraph limit are diagnostics because conversational and general
technical writing must sometimes preserve necessary context. Natural contractions and standard punctuation remain
available when they improve readable human communication.

The policy also incorporates established community guidance to lead with the key point, use familiar words, write for
a global audience, address the reader directly, support scanning, and avoid jargon, cultural references, and claims
that a task is easy. These additions resolve cases where strict maintenance-document English would make interactive or
general technical communication less natural without improving understanding.
</standard-adaptation>

<sources>
Primary standard: https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf
ASD-STE100 scope and dictionary model: https://www.asd-ste100.org/STE_faq.html
Google developer documentation voice and tone: https://developers.google.com/style/tone
Google developer documentation sentence structure: https://developers.google.com/style/sentence-structure
Microsoft writing style: https://learn.microsoft.com/en-us/windows/apps/design/style/writing-style
United States plain-language principles: https://digital.gov/guides/plain-language/principles
</sources>
</controlled-human-language>
