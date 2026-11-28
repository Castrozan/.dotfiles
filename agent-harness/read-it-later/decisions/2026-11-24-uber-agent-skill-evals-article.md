# Uber Engineering: evaluating a million agent skill invocations a month

**Bundle goal:** Keep one Uber Engineering X article on evaluating agent skill invocations at scale as reference beside the repository's skill routing and policy evaluation suites; the article body was not readable at triage, so nothing in Lucas's setup changes until it is read.

| # | Capture | TL;DR | Action | Why | Already covered | Second Brain direction | Systems | Local | Lucas's note |
|---|---|---|---|---|---|---|---|---|---|
| 1 | [Tweet from Uber Engineering (2026-11-24 17-51-48)](https://x.com/UberEng/status/2125008806249930999) | Uber Engineering posted an X article titled 'How Uber Evals 1 Million Agent Skill Invocations a Month'; only its opening is readable here, defining a skill as a Markdown file that teaches an agent one job such as creating a pull request, querying a metrics store or outlining a sales presentation. | file → Uber Engineering - Evaluating a million agent skill invocations a month (AI Agent Skills MOC) | The article body could not be read: the origin gave only the title and a two-line preview, Chrome was not running on chise and no launcher for it exists, and a web search found no copy of the post. It is kept as a reference because the subject, evaluating skill invocations at production volume, sits beside Lucas's own skill routing evaluation suite. Lucas can drop it instead if a title and preview are not enough to keep. | agent-harness/quality/evaluations/suites/skill_routing.yaml and agent-harness/quality/evaluations/suites/policy already evaluate skill routing and instruction compliance in the dotfiles; no Second Brain entry covers skill evaluation | - | dotfiles | no | - |

Answer on the pull request in plain language: approve the table as it stands, change any card ("drop 3", "session for 2 on kira"), or ask. Captures added after your approval need a new one.

<details><summary>Card data</summary>

<!-- ril-cards -->
```json
{
  "topic_slug": "uber-agent-skill-evals-article",
  "title": "Uber Engineering: evaluating a million agent skill invocations a month",
  "bundle_goal": "Keep one Uber Engineering X article on evaluating agent skill invocations at scale as reference beside the repository's skill routing and policy evaluation suites; the article body was not readable at triage, so nothing in Lucas's setup changes until it is read.",
  "cards": [
    {
      "linked_urls": [
        "https://x.com/i/article/2120222611070500864"
      ],
      "covered_evidence": [
        "agent-harness/quality/evaluations/suites/skill_routing.yaml and agent-harness/quality/evaluations/suites/policy already evaluate skill routing and instruction compliance in the dotfiles; no Second Brain entry covers skill evaluation"
      ],
      "second_brain_direction": [],
      "systems": [
        "dotfiles"
      ],
      "runs_locally_on_chise": false,
      "capture": "Tweet from Uber Engineering (2026-11-24 17-51-48).md",
      "tldr": "Uber Engineering posted an X article titled 'How Uber Evals 1 Million Agent Skill Invocations a Month'; only its opening is readable here, defining a skill as a Markdown file that teaches an agent one job such as creating a pull request, querying a metrics store or outlining a sales presentation.",
      "origin_url": "https://x.com/UberEng/status/2125008806249930999",
      "lucas_note": "",
      "action": "file",
      "reason": "The article body could not be read: the origin gave only the title and a two-line preview, Chrome was not running on chise and no launcher for it exists, and a web search found no copy of the post. It is kept as a reference because the subject, evaluating skill invocations at production volume, sits beside Lucas's own skill routing evaluation suite. Lucas can drop it instead if a title and preview are not enough to keep.",
      "entry": {
        "title": "Uber Engineering - Evaluating a million agent skill invocations a month",
        "theme_moc": "AI Agent Skills MOC",
        "tags": [
          "topic/engineering"
        ],
        "why": "An enterprise-scale account of evaluating agent skill invocations, filed from the article title and opening only because its body was unreadable when captured.",
        "what_to_steal": [
          "Read the full article for how skill invocations are scored at volume before changing the skill routing or policy evaluation suites"
        ],
        "reuse_for": "judging whether the dotfiles skill routing evaluations need production-scale sampling",
        "creator": "Uber Engineering (@UberEng)",
        "platform": "X"
      },
      "added_at": "2026-11-24T21:20:53+00:00"
    }
  ]
}
```

</details>
