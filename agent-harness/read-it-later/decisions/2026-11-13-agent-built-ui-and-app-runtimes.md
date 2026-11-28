# Agent-first UI libraries: Vercel UI SDK and Expo Exact

**Bundle goal:** Keep one tweet pointing at two agent-first frontend projects, vercel-labs/ui and expo/exact, as reference; nothing in Lucas's setup changes.

| # | Capture | TL;DR | Action | Why | Already covered | Second Brain direction | Systems | Local | Lucas's note |
|---|---|---|---|---|---|---|---|---|---|
| 1 | [Tweet from Jon Kuperman (2026-11-13 07-26-45)](https://x.com/jkup/status/2121025116436078633) | Two links with the comment 'This feels like a moment': vercel-labs/ui (UI SDK, a library of UI behaviors written for agents to compose, beta, created 2026-10-26) and expo/exact (write one app, run it natively on web, macOS, iOS and Linux, with an agent driver that builds, runs, sees and tests it, pre-1.0, created 2026-11-02). | file → Jon Kuperman - Agent-first UI SDK and Expo Exact (Developer Tooling MOC) | Both projects are young and pre-stable, and neither matches a system Lucas runs: a search of the dotfiles finds no reference to either, and no Expo or React Native project. They are worth keeping as a pointer for when an agent-built frontend or a cross-platform app comes up. | - | - | - | no | - |

Answer on the pull request in plain language: approve the table as it stands, change any card ("drop 3", "session for 2 on kira"), or ask. Captures added after your approval need a new one.

<details><summary>Card data</summary>

<!-- ril-cards -->
```json
{
  "topic_slug": "agent-built-ui-and-app-runtimes",
  "title": "Agent-first UI libraries: Vercel UI SDK and Expo Exact",
  "bundle_goal": "Keep one tweet pointing at two agent-first frontend projects, vercel-labs/ui and expo/exact, as reference; nothing in Lucas's setup changes.",
  "session": null,
  "cards": [
    {
      "linked_urls": [
        "https://github.com/vercel-labs/ui",
        "https://github.com/expo/exact"
      ],
      "covered_evidence": [],
      "second_brain_direction": [],
      "systems": [],
      "runs_locally_on_chise": false,
      "capture": "Tweet from Jon Kuperman (2026-11-13 07-26-45).md",
      "tldr": "Two links with the comment 'This feels like a moment': vercel-labs/ui (UI SDK, a library of UI behaviors written for agents to compose, beta, created 2026-10-26) and expo/exact (write one app, run it natively on web, macOS, iOS and Linux, with an agent driver that builds, runs, sees and tests it, pre-1.0, created 2026-11-02).",
      "origin_url": "https://x.com/jkup/status/2121025116436078633",
      "lucas_note": "",
      "action": "file",
      "reason": "Both projects are young and pre-stable, and neither matches a system Lucas runs: a search of the dotfiles finds no reference to either, and no Expo or React Native project. They are worth keeping as a pointer for when an agent-built frontend or a cross-platform app comes up.",
      "entry": {
        "title": "Jon Kuperman - Agent-first UI SDK and Expo Exact",
        "theme_moc": "Developer Tooling MOC",
        "tags": [
          "topic/dev-tools",
          "medium/product"
        ],
        "why": "Two projects from the same fortnight that design the frontend for an agent as the main author: UI SDK as composable behaviors with an installable skill, Exact as a runtime whose ten-operation agent driver builds, runs, screenshots and tests the same app on every host.",
        "what_to_steal": [
          "UI SDK ships its own agent skill (npx skills add vercel-labs/ui --skill ui-sdk) so the library teaches the agent how to use it",
          "Exact keeps its agent API to ten operations on purpose and gives the agent control of the clock, so tests are deterministic"
        ],
        "reuse_for": "choosing a frontend stack when an agent will write and test most of the code",
        "creator": "Jon Kuperman (@jkup)",
        "platform": "X"
      },
      "added_at": "2026-11-13T10:41:48+00:00"
    }
  ]
}
```

</details>
