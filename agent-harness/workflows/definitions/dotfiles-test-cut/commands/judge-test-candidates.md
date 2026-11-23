### Judgment

Decide which measured unit tests leave the suite. Read only; change no file. The checkout root is the path serialized
on the next line.
$INPUTS.root

Read the section on what earns a test in `repository/verification/TESTING.md` under that root once. Then read the
candidates file serialized on the next line once with a single command.
$INPUTS.candidates_path

Each candidate carries its identifier, its source and the evidence a mutation run found against it. Either it failed
for no mutant of the code it runs, or one stronger test in the same file, whose source is included, caught every mutant
it caught.

### Verdicts

The evidence is necessary and never sufficient: mutants are small edits, so they cannot show what a test guards against
a rewrite. Cut a candidate only when reading it confirms the evidence. A silent candidate leaves when its assertions
could not fail for any change of behavior. A dominated candidate leaves when it charges the same behavior as its
stronger test with another example of the same kind.

Keep a candidate that states a property or invariant, a boundary, an error path, or an effect on a file, a process or
printed output that its stronger test never asserts. When unsure, keep it. A kept candidate needs no entry.

Return one entry for each test to cut: the identifier copied exactly, the number of the condition it fails, and one
sentence naming the behavior that stays guarded without it.
