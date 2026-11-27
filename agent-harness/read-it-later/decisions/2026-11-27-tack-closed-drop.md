# tack: Nix pinning video, closed without filing

**Bundle goal:** Close out one tweet about vimjoyer's tack video after the earlier file proposal was closed; nothing in Lucas's setup changes.

| # | Capture | TL;DR | Action | Why | Already covered | Second Brain direction | Systems | Local | Lucas's note |
|---|---|---|---|---|---|---|---|---|---|
| 1 | [Tweet from Yurii Melnychenko (2026-11-27 10-52-07)](https://x.com/vimjoyer/status/2126093782647210405) | vimjoyer's video 'I Replaced Nix Flake Inputs With This' on tack (manic-systems/tack), a TOML pin file plus lock that Nix reads without flakes. | drop | Lucas closed the earlier file proposal in pull request 314 without a comment, the origin is unchanged since, and swapping flake inputs for tack would rework the dependencies sub-flake for no current problem. Answer 'file' if closing it meant only that the reference was not wanted as a pull request. | pull request 314 proposed filing this capture as a Developer Tooling reference and was closed unmerged with no comment; the dotfiles pin everything through flake inputs: repository/flake-assembly/dependencies/flake.nix owns every input and flake.lock holds the locks, and no file mentions tack, npins or niv | - | dotfiles | yes | - |

Answer on the pull request in plain language: approve the table as it stands, change any card ("drop 3", "session for 2 on kira"), or ask. Captures added after your approval need a new one.

<details><summary>Card data</summary>

<!-- ril-cards -->
```json
{
  "topic_slug": "tack-closed-drop",
  "title": "tack: Nix pinning video, closed without filing",
  "bundle_goal": "Close out one tweet about vimjoyer's tack video after the earlier file proposal was closed; nothing in Lucas's setup changes.",
  "session": null,
  "cards": [
    {
      "linked_urls": [
        "https://www.youtube.com/watch?v=MS_iZlr-XKI",
        "https://github.com/manic-systems/tack"
      ],
      "covered_evidence": [
        "pull request 314 proposed filing this capture as a Developer Tooling reference and was closed unmerged with no comment",
        "the dotfiles pin everything through flake inputs: repository/flake-assembly/dependencies/flake.nix owns every input and flake.lock holds the locks, and no file mentions tack, npins or niv"
      ],
      "second_brain_direction": [],
      "systems": [
        "dotfiles"
      ],
      "runs_locally_on_chise": true,
      "capture": "Tweet from Yurii Melnychenko (2026-11-27 10-52-07).md",
      "tldr": "vimjoyer's video 'I Replaced Nix Flake Inputs With This' on tack (manic-systems/tack), a TOML pin file plus lock that Nix reads without flakes.",
      "origin_url": "https://x.com/vimjoyer/status/2126093782647210405",
      "lucas_note": "",
      "action": "drop",
      "reason": "Lucas closed the earlier file proposal in pull request 314 without a comment, the origin is unchanged since, and swapping flake inputs for tack would rework the dependencies sub-flake for no current problem. Answer 'file' if closing it meant only that the reference was not wanted as a pull request.",
      "added_at": "2026-11-27T22:38:56+00:00"
    }
  ]
}
```

</details>
