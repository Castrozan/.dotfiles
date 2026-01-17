---
name: exit
description: Safely terminate the current Claude Code session. Use when user explicitly asks to end session AND all work is complete and verified.
---

# Exit Skill

Safely terminate ONLY this Claude Code session without affecting other running sessions.

## When to Use

Use ONLY when ALL conditions are met:
1. User explicitly requests session end ("exit", "goodbye", "done", "kill session")
2. All tasks are complete and verified
3. Changes are committed (if applicable)

## Safety Verification

Before terminating, MUST verify:
1. Parent process is actually Claude Code (not something else)
2. Summarize what was accomplished
3. Confirm with user before killing

## Implementation

```bash
# Step 1: Verify parent is Claude process
PARENT_CMD=$(ps -p $PPID -o comm= 2>/dev/null)
if [[ "$PARENT_CMD" != "claude" ]]; then
  echo "Safety check failed: Parent process is '$PARENT_CMD', not 'claude'"
  echo "Aborting session exit. User should type /exit manually."
  exit 1
fi

# Step 2: Get session info for confirmation
echo "Session PID: $PPID"
echo "Parent verified as Claude Code process"
echo "Sending SIGTERM for clean shutdown..."

# Step 3: Kill ONLY this session
kill -TERM $PPID
```

## Workflow

1. **Summarize work** - List what was accomplished
2. **Verify safety** - Run parent process check
3. **Confirm** - Ask user "Ready to terminate session?"
4. **Execute** - Run the kill command

## What This Does

- `$PPID` = Parent Process ID = Claude Code process for THIS session
- `kill -TERM` = Graceful shutdown signal (allows cleanup)
- Safety check prevents killing wrong process

## What NOT to Do

NEVER:
- Use `pkill -f claude` (kills ALL Claude sessions)
- Use `killall claude` (kills ALL Claude sessions)
- Skip the parent process verification
- Kill without user confirmation

## Example Session

```
User: "All done, kill this session"

Claude: Here's what we accomplished:
- Added feature X
- Fixed bug Y
- All tests passing
- Changes committed

Let me verify and terminate the session.

[Runs safety check - parent is 'claude' ✓]
[Sends SIGTERM to PID 969784]

[Session ends]
```

## Fallback

If safety check fails or user prefers manual exit:
- Tell user to type `/exit` or press `Ctrl+D`
