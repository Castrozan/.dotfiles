EXAMPLE_CARD_SHARED_FIELDS = {
    "linked_urls": ["https://github.com/example/state-machine-kit"],
    "covered_evidence": [
        "c74b5ca42 complexity lint already gates functions above five"
    ],
    "second_brain_direction": [
        "[[Lucas Zanoni - Workflows as the direction for agent work]]"
    ],
    "systems": ["dotfiles"],
    "runs_locally_on_chise": True,
}

EXAMPLE_CARDS_DOCUMENT = {
    "groups": [
        {
            "topic_slug": "agent-state-machines",
            "title": "Explicit state machines for agent code",
            "bundle_goal": "Turn implicit flags in agent wrappers into explicit state machines.",
            "target_pull_request": None,
            "session": {
                "host": "chise",
                "done_when": [
                    "the clawde wrapper flags are one explicit state machine with tests"
                ],
                "constraints": [
                    "work in a worktree",
                    "no behavior change without a test",
                ],
            },
            "cards": [
                {
                    **EXAMPLE_CARD_SHARED_FIELDS,
                    "capture": "Tweet from Steve Ruiz (2026-11-01 10-00-00).md",
                    "tldr": "A prompt that finds implicit state machines in a codebase.",
                    "origin_url": "https://x.com/steveruizok/status/1",
                    "lucas_note": "use this on clawde",
                    "action": "session",
                    "reason": "the wrapper has five boolean phases that already caused one bug",
                },
                {
                    **EXAMPLE_CARD_SHARED_FIELDS,
                    "capture": "Tweet from Eric Clemmons (2026-11-02 09-00-00).md",
                    "tldr": "Property-based and model-based testing with oracles.",
                    "origin_url": "https://x.com/ericclemmons/status/2",
                    "lucas_note": "",
                    "action": "file",
                    "reason": "reference for the session above, nothing to build alone",
                    "entry": {
                        "title": "Eric Clemmons - PBT MBT and oracles",
                        "theme_moc": "Engineering MOC",
                        "tags": ["topic/engineering"],
                        "why": "Names the oracle problem plainly.",
                        "what_to_steal": [
                            "model the system as a state machine and test against it"
                        ],
                        "reuse_for": "testing explicit state machines",
                        "creator": "Eric Clemmons (@ericclemmons)",
                        "platform": "X",
                    },
                },
            ],
        }
    ]
}
