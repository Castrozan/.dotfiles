---
name: explore
description: Search current code across text, files, callers, and context in three cycles. Use for repo sweeps, not Git history.
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

<history-belongs-to-coding>
Questions about when, why, evolution, past states, or deleted code are Git archaeology. Load the coding skill and its
history guidance instead of treating them as current-tree exploration.
</history-belongs-to-coding>

<return-the-conclusion>
Answer the question asked, with `file_path:line_number` citations. Never paste file bodies, search dumps or the log of
what you tried. State plainly what you could not find and which searches you ran to conclude it is absent, because an
unfound thing and an unsearched thing are not the same answer.
</return-the-conclusion>
