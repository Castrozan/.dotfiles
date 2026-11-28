# Modern Web Guidance agent skill

**Bundle goal:** Keep one tweet about the modern-web-guidance agent skill from vercel-labs/agent-browser as reference for the frontend-design skill; nothing in Lucas's setup changes.

| # | Capture | TL;DR | Action | Why | Already covered | Second Brain direction | Systems | Local | Lucas's note |
|---|---|---|---|---|---|---|---|---|---|
| 1 | [Tweet from Chris Tate (2026-11-18 22-53-18)](https://x.com/ctatedev/status/2122816672625275030) | Chris Tate announced the modern-web-guidance skill: the agent looks up Chrome's Modern Web Guidance, applies it to the code, then checks the result in a real browser (layout shift, reduced motion, dark mode, dialog focus and more); install with npx skills add vercel-labs/agent-browser. | file → Chris Tate - modern-web-guidance skill (AI Agent Skills MOC) | A tidy pattern of guidance lookup followed by verification in a real browser, which the frontend-design and browser skills could borrow. The tweet text names the checks but not how the lookup works, so it stays reference until Lucas has a frontend task that needs it. | agent-harness/agent-instructions/skills/writing/frontend-design/SKILL.md exists, and agent-harness/agent-instructions/skills/workstation/browser/SKILL.md already checks pages in a real browser; no repository file mentions Modern Web Guidance | - | - | yes | - |

Answer on the pull request in plain language: approve the table as it stands, change any card ("drop 3", "session for 2 on kira"), or ask. Captures added after your approval need a new one.

<details><summary>Card data</summary>

<!-- ril-cards -->
```json
{
  "topic_slug": "modern-web-guidance-skill",
  "title": "Modern Web Guidance agent skill",
  "bundle_goal": "Keep one tweet about the modern-web-guidance agent skill from vercel-labs/agent-browser as reference for the frontend-design skill; nothing in Lucas's setup changes.",
  "cards": [
    {
      "linked_urls": [
        "https://github.com/vercel-labs/agent-browser"
      ],
      "covered_evidence": [
        "agent-harness/agent-instructions/skills/writing/frontend-design/SKILL.md exists, and agent-harness/agent-instructions/skills/workstation/browser/SKILL.md already checks pages in a real browser; no repository file mentions Modern Web Guidance"
      ],
      "second_brain_direction": [],
      "systems": [],
      "runs_locally_on_chise": true,
      "capture": "Tweet from Chris Tate (2026-11-18 22-53-18).md",
      "tldr": "Chris Tate announced the modern-web-guidance skill: the agent looks up Chrome's Modern Web Guidance, applies it to the code, then checks the result in a real browser (layout shift, reduced motion, dark mode, dialog focus and more); install with npx skills add vercel-labs/agent-browser.",
      "origin_url": "https://x.com/ctatedev/status/2122816672625275030",
      "lucas_note": "",
      "action": "file",
      "reason": "A tidy pattern of guidance lookup followed by verification in a real browser, which the frontend-design and browser skills could borrow. The tweet text names the checks but not how the lookup works, so it stays reference until Lucas has a frontend task that needs it.",
      "entry": {
        "title": "Chris Tate - modern-web-guidance skill",
        "theme_moc": "AI Agent Skills MOC",
        "tags": [
          "topic/ai-agents"
        ],
        "why": "Pairs Chrome's own web guidance with a real-browser check of layout shift, reduced motion, dark mode and dialog focus, so the agent proves the fix instead of asserting it.",
        "what_to_steal": [
          "Lookup then apply then verify in a real browser as one loop for frontend changes",
          "The named checklist: layout shift, reduced motion, dark mode, dialog focus"
        ],
        "reuse_for": "extending the frontend-design skill with a verification step",
        "creator": "Chris Tate (@ctatedev)",
        "platform": "X"
      },
      "added_at": "2026-11-20T13:15:21+00:00"
    }
  ]
}
```

</details>
