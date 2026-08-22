# Hook output channels

A hook's JSON output has two separate audiences. Picking the wrong key means the message reaches nobody who can act on
it. Verified against the Claude Code 2.1.220 bundle and against live transcript records.

## `systemMessage` reaches the human only

It renders in the terminal as `<hookName> says: <content>` and lands in the transcript as
`type: "attachment"` / `hook_system_message`, never as a message in the API payload. The model does not see it, on any
event. Cost is zero prompt tokens. Use it for something the human needs to notice, never to steer an agent.

## `hookSpecificOutput.additionalContext` reaches the model

Text is injected into model context, and `hookEventName` is required alongside it. On `Stop` and `SubagentStop` it is
non-error feedback that keeps the conversation going so the model can act on it, which means an extra model turn every
time it fires. On `PreToolUse` and `PostToolUse` it just appends to that tool call's context.

## Blocking channels also reach the model

`PreToolUse` denies with `hookSpecificOutput.permissionDecision: "deny"` plus `permissionDecisionReason`.
`PostToolUse` and `Stop` block with top-level `decision: "block"` plus `reason`. The reason string
is model-facing, so a hook that blocks and also sets `systemMessage` is telling the model and the human separately, by
design.

## Consequence for advisory tiers

A soft tier that only sets `systemMessage` cannot change agent behavior. It is a human dashboard, so justify it as
terminal output or delete it. `line_count_limit_guard_handler.py` lost its 100-line and 150-line tiers for exactly this reason,
and the lingering-daemon advisory in `background_bash_anti_pattern_validator_handler.py` gained `additionalContext` because its
text is an instruction to the model.
