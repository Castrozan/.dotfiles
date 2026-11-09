### Task

Design and build a complete web page from intent rather than a placeholder skeleton. The page brief is serialized on
the next line.
$INPUTS.brief

AUDIENCE, THESIS, AND ACTION: infer one precise audience, one sentence the page argues, and one primary action.

SECTION SPINE: create 6 to 8 ordered sections spanning header, hero, two to four middle sections, bottom call to action,
and footer. Each section must carry one idea, earn its place, connect to its neighbors, and contain purposeful final
content. Build the sections in order so later content continues rather than repeats earlier content. Never use lorem
ipsum, placeholder labels, unsupported facts, decorative-only elements, or claims the brief does not support. For a
section with no previous or next neighbor, return "none" for relatesToPrevious or setsUpNext.

OUTPUT FORMAT: return markup per section without a document wrapper, in the format serialized on the next line.
$INPUTS.output

CONSTRAINTS: honor the constraints serialized on the next line; an empty string means none.
$INPUTS.constraints
