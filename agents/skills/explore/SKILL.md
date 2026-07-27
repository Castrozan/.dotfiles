---
name: explore
description: Search a codebase in three widening-then-narrowing cycles, using text, file, history and context search, and return the conclusion rather than the files.
---

<three-cycles>
Cycle one casts wide and reads nothing: fire several independently worded searches at once and collect paths only.
Cycle two reads the survivors and follows their edges: imports, callers, and the names those files reveal. Cycle three
closes the gaps: search for what the first two implied but never confirmed, the caller nobody found, the test that
should exist, the config that wires it. Stop early when a cycle surfaces nothing new, and never run a fourth.
</three-cycles>

<word-the-query-several-ways>
One phrasing finds one thing. In cycle one, search the identifier, the human synonym, the error or log string it would
emit, the config key that would enable it, and the path shape it would live under. A concept absent under every one of
those is genuinely absent; absent under one is just badly named.
</word-the-query-several-ways>

<text-search>
Grep is ripgrep. Use `output_mode: files_with_matches` in cycle one so breadth costs almost nothing, then switch to
`content` with `-C` once the candidate set is small. Cut noise with `type` before `glob`, and `glob` before manual
filtering. Use `multiline: true` for anything spanning lines, such as a function signature and its body or a config
block. Case-insensitive first, exact once you know the casing.
</text-search>

<file-and-structure-search>
Glob finds by path shape when you know the naming convention but not the location. `tree` on a directory beats a dozen
Globs when you are learning an unfamiliar layout, and `fd` is there for name searches with type or extension filters
that Glob cannot express.
</file-and-structure-search>

<history-search-finds-what-text-search-cannot>
No file-content search answers "when did this appear" or "what used to be here". `git log -S<string>` finds the commits
that changed how many times a string occurs, which is how you locate a deletion. `git log -G<regex>` matches the diff
text itself. `git log --oneline -- <path>` gives a file's history, and `git grep <pattern> <revision>` searches a past
state without checking it out. Reach for these whenever the thing you want is missing from the working tree.
</history-search-finds-what-text-search-cannot>

<return-the-conclusion>
Answer the question asked, with `file_path:line_number` citations. Never paste file bodies, search dumps or the log of
what you tried. State plainly what you could not find and which searches you ran to conclude it is absent, because an
unfound thing and an unsearched thing are not the same answer.
</return-the-conclusion>
