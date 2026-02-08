# Claude Code Hooks Documentation

## What Are Hooks?

Hooks are **trigger-based automations** that fire on specific events in Claude Code. Unlike skills (which you invoke), hooks run automatically when certain conditions are met.

Key characteristics:
- Execute shell commands at specific lifecycle events
- Can provide reminders, inject context, or block actions
- Run with your shell environment's credentials
- Support regex matchers to filter which tools trigger them

## Hook Types

| Hook | When It Fires | Can Block? | Use Case |
|------|---------------|------------|----------|
| **PreToolUse** | Before a tool executes | Yes (exit 2) | Validation, reminders, input modification |
| **PostToolUse** | After tool completes | No | Formatting, feedback, follow-up suggestions |
| **UserPromptSubmit** | When you send a message | Yes (exit 2) | Input validation, context injection |
| **Stop** | When Claude finishes responding | Yes | Completion checks, cleanup reminders |
| **SessionStart** | When session begins | No | Environment setup, context loading |
| **SessionEnd** | When session ends | No | Cleanup, logging |
| **PreCompact** | Before context compaction | No | Transcript backup |
| **Notification** | Permission requests | No | Custom alerts |

## Configuration Location

Hooks go in settings files (in precedence order):
```
~/.claude/settings.json           # User-wide (global)
.claude/settings.json             # Project (team-shared)
.claude/settings.local.json       # Local overrides (gitignored)
```

## Configured Hooks (Your Setup)

### PreToolUse Hooks

| Hook | Trigger | What It Does |
|------|---------|--------------|
| **Tmux Reminder** | Long-running commands (npm, cargo, pytest, nixos-rebuild, etc.) | Reminds to use tmux if not in a tmux session |
| **Destructive Warning** | rm -rf, git push --force, git reset --hard, chmod 777 | Warns about potentially dangerous commands |
| **Sensitive File** | .env, .pem, .key, secrets files | Warns when editing files that may contain secrets |
| **NixOS File** | flake.nix, configuration.nix, home.nix, default.nix | Reminds to rebuild after changes |
| **Skill Context** | Task tool usage | Reminds to provide full context to skills |

### PostToolUse Hooks

| Hook | Trigger | What It Does |
|------|---------|--------------|
| **Rebuild Feedback** | nixos-rebuild, home-manager switch | Notes about generation changes |
| **Commit Failure** | git commit with errors | Suggests checking pre-commit hooks |

### UserPromptSubmit Hooks

| Hook                   | Trigger Keywords                     | What It Does             |
| ---------------------- | ------------------------------------ | ------------------------ |
| **Deployment Context** | deploy, production, release, publish | Injects caution reminder |
| **Database Context**   | database, migration, sql, schema     | Injects backup reminder  |

### SessionStart Hooks

| Hook | What It Does |
|------|--------------|
| **Tmux Status** | Shows active tmux windows or suggests starting one |
| **Git Status** | Shows current branch and uncommitted changes |

### Stop Hooks

| Hook | What It Does |
|------|--------------|
| **Package Sync** | Reminds to run npm install if package.json was modified |

## How Hooks Work

### Input/Output Protocol

Hooks receive JSON via stdin:
```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/conversation.jsonl",
  "tool_name": "Bash",
  "tool_input": {
    "command": "npm test",
    "description": "Run tests"
  }
}
```

### Exit Codes

| Code | Behavior |
|------|----------|
| **0** | Success - action continues |
| **2** | Block - action is prevented |
| **Other** | Error - continues but shows warning |

### JSON Output

Hooks can output structured JSON:
```json
{
  "continue": true,
  "systemMessage": "Message shown to user",
  "additionalContext": "Context for Claude"
}
```

## Useful Hook Ideas

### For Your Workflow

1. **Git Branch Protection** - Warn before pushing to main/master
2. **Secret Detection** - Block commits containing API keys
3. **Auto-Format** - Run prettier/black after file edits
4. **Test Reminder** - After editing code, remind to run tests
5. **Documentation** - After creating functions, remind to document

### Example: Custom Python Hook

```python
#!/usr/bin/env python3
import json
import sys

data = json.load(sys.stdin)
command = data.get("tool_input", {}).get("command", "")

if "dangerous_pattern" in command:
    print("Blocked: dangerous pattern detected", file=sys.stderr)
    sys.exit(2)  # Block

sys.exit(0)  # Allow
```

Save to `~/.claude/hooks/` and reference in settings:
```json
{
  "type": "command",
  "command": "python3 ~/.claude/hooks/my_hook.py"
}
```

## Matcher Syntax

| Pattern | Matches |
|---------|---------|
| `"Write"` | Exact tool name |
| `"Edit\|Write"` | Multiple tools (OR) |
| `"Notebook.*"` | Regex pattern |
| `""` or `"*"` | All tools |
| `"Bash(npm*)"` | Tool with argument pattern |

## Best Practices

1. **Keep hooks fast** - Use 5-second timeouts, hooks shouldn't slow workflow
2. **Don't hard-block** - Prefer warnings (exit 0 with systemMessage) over blocking (exit 2)
3. **Test first** - Verify hooks work before relying on them
4. **Log for debugging** - Use `--debug` flag to see hook execution
5. **Use scripts for complex logic** - Put complex hooks in `~/.claude/hooks/`

## Debugging

Run Claude with debug mode:
```bash
claude --debug
```

Use `/hooks` slash command to view/edit hooks interactively.

## Requirements

The configured hooks use these tools (should be available in your NixOS system):
- `jq` - JSON parsing in bash hooks
- `python3` - For the Python hook scripts

If hooks fail, ensure these are in your path. On NixOS, add to your configuration:
```nix
environment.systemPackages = with pkgs; [ jq python3 ];
```

Or for home-manager:
```nix
home.packages = with pkgs; [ jq python3 ];
```

## Files

| File | Purpose |
|------|---------|
| `/home/zanoni/.claude/settings.json` | Main settings with hooks configuration |
| `/home/zanoni/.claude/hooks/` | Custom Python hook scripts |
| `/home/zanoni/.claude/hooks/dangerous-command-blocker.py` | Blocks/warns about dangerous commands |
| `/home/zanoni/.claude/hooks/tmux-reminder.py` | Reminds about tmux for long-running commands |
| `/home/zanoni/.claude/hooks/sensitive-file-guard.py` | Guards sensitive files from editing |
| `/home/zanoni/vault/ReadItLater Inbox/Claude-Code-Hooks-Documentation.md` | This documentation |

## Using Python Hooks Instead

The Python scripts in `~/.claude/hooks/` are more robust alternatives to inline bash. To use them, update your settings.json:

```json
{
  "matcher": "Bash",
  "hooks": [{
    "type": "command",
    "command": "/run/current-system/sw/bin/python3 ~/.claude/hooks/tmux-reminder.py"
  }]
}
```
