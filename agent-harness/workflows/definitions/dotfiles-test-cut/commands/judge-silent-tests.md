### Judgment

Decide which unit tests leave the suite. Each candidate failed for no mutant of the sources it sits beside, so the
measurement found nothing it discriminates. The checkout root is the path serialized on the next line. Read only; change
no file.
$INPUTS.root

Read the section on what earns a test in `repository/verification/TESTING.md` under that root once, then read the
candidates file serialized on the next line once with a single command. It holds each candidate's identifier and source.
$INPUTS.candidates_path

### Verdicts

Cut a candidate only when it fails one of the seven conditions, and name that condition by its number. Keep a candidate
whose behavior the mutants could not reach: text or format output, a subprocess or file effect, an error message, or a
branch in code that is not Python. A kept candidate needs no entry.

Return one entry for each test to cut, with the identifier copied exactly from the file, the condition number and one
sentence of reason that names the behavior the test fails to guard.
