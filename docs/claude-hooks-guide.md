# Claude Code Hooks Configuration Guide

This guide explains how to use Claude Code hooks in your NixOS dotfiles setup for enhanced development workflows.

## What are Hooks?

Hooks are **trigger-based automations** that fire on specific events in Claude Code. They're shell commands or scripts that run automatically at predefined points during Claude's execution, allowing you to:

- Add safety checks before dangerous commands
- Provide contextual reminders and tips
- Automate formatting and linting
- Track command execution times
- Enforce project conventions

Unlike skills (which you manually invoke with /command), hooks run automatically when their conditions are met.

## Quick Reference

### Hook Events

| Event | When | Can Block? | Example Use |
|-------|------|------------|-------------|
| **PreToolUse** | Before tool runs | Yes (exit 2) | Validate commands, warn about dangers, remind about tmux |
| **PostToolUse** | After tool completes | Yes | Auto-format, run linters, detect failures |
| **UserPromptSubmit** | User sends message | Yes | Context injection, project rules |
| **SessionStart** | Session begins | No | Show git status, environment, reminders |
| **Stop** | Claude finishes | Yes | Verify tests pass, check for uncommitted changes |
| **PermissionRequest** | Permission dialog | Yes | Auto-approve safe operations |

### Your Current Hooks

Located in `home/modules/claude/config.nix`:

1. **tmux-reminder.py** - Reminds to use tmux for long-running commands (npm, cargo, pytest, docker build)
2. **dangerous-command-guard.py** - Blocks `rm -rf /`, force push, DROP TABLE
3. **git-reminder.py** - Warns about uncommitted changes, suggests stashing
4. **sensitive-file-guard.py** - Guards .env, secrets, credentials files
5. **nix-rebuild-reminder.py** - Reminds to `home-manager switch` after .nix changes
6. **auto-format.py** - Auto-formats code after edits (prettier, ruff, nixpkgs-fmt)
7. **subagent-context-reminder.py** - Tips for using specialized subagents

### Hook Configuration in Nix

Your hooks are configured in `home/modules/claude/config.nix`:

```nix
hooks = {
  SessionStart = [
    {
      hooks = [{
        type = "command";
        command = "${../hooks/session-start.py}";
      }];
    }
  ];
  PreToolUse = [
    {
      matcher = "Bash";
      hooks = [
        { type = "command"; command = "${../hooks/tmux-reminder.py}"; }
        { type = "command"; command = "${../hooks/dangerous-command-guard.py}"; }
        { type = "command"; command = "${../hooks/git-reminder.py}"; }
      ];
    }
    {
      matcher = "Edit|Write";
      hooks = [
        { type = "command"; command = "${../hooks/sensitive-file-guard.py}"; }
      ];
    }
  ];
  PostToolUse = [
    {
      matcher = "Edit|Write";
      hooks = [
        { type = "command"; command = "${../hooks/nix-rebuild-reminder.py}"; }
        { type = "command"; command = "${../hooks/auto-format.py}"; }
      ];
    }
  ];
};
```

## Excellent Hook Ideas for Your Workflow

### Tmux Integration (Your Top Priority!)
```python
# Enhanced tmux reminder for specific commands
def needs_tmux(command):
    long_running = ["npm", "yarn", "pnpm", "cargo", "pytest", "make",
                   "docker build", "nix-build", "home-manager switch",
                   "nixos-rebuild", "watch", "serve", "dev"]
    return any(cmd in command for cmd in long_running)

if needs_tmux(command) and not os.environ.get("TMUX"):
    output = {
        "systemMessage": "💡 Consider using tmux for this long-running command. It allows you to detach and reattach sessions."
    }
```

### Git Workflow Enhancements
- **Worktree suggester** - When switching branches with changes, suggest using `/worktree`
- **Pre-push checker** - Run tests and linters before allowing push
- **Commit message formatter** - Ensure conventional commits format
- **PR readiness** - Check if branch is ready for PR (tests pass, no TODOs)

### NixOS-Specific Hooks
```python
# Remind about direnv after entering project
if os.path.exists(".envrc") and not os.environ.get("DIRENV_DIR"):
    output = {
        "systemMessage": "📁 This project has .envrc - run 'direnv allow' to load environment"
    }

# Suggest garbage collection after many rebuilds
rebuild_count = get_rebuild_count()  # Track in ~/.claude/state/
if rebuild_count > 10:
    output = {
        "systemMessage": "🗑️ Consider running 'nix-collect-garbage -d' to free space"
    }
```

### Development Safety
- **Database safety** - Extra confirmation for destructive DB operations
- **Secret detection** - Scan for API keys, tokens before commits
- **Branch protection** - Stricter rules for main/master/production
- **Build verification** - Ensure builds pass before marking tasks complete

### Context-Aware Reminders
```python
# Project-specific reminders based on directory
project_reminders = {
    "~/.dotfiles": [
        "Run home-manager switch after changes",
        "Test on both NixOS and Darwin",
        "Update flake.lock periodically"
    ],
    "~/projects/api": [
        "Run migrations after schema changes",
        "Update API docs after endpoint changes",
        "Check rate limits before deploying"
    ]
}
```

## Writing Custom Hooks

### Basic Template

```python
#!/usr/bin/env python3
"""hook-name.py - Brief description."""

import json
import sys

def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    # Extract relevant data
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # Your logic here
    if should_warn():
        output = {
            "continue": True,
            "systemMessage": "Warning message shown to user"
        }
        print(json.dumps(output))

    sys.exit(0)

if __name__ == "__main__":
    main()
```

### Input Data Structure

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/conversation.jsonl",
  "cwd": "/current/working/directory",
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": {
    "command": "npm test",
    "timeout": 120000
  }
}
```

### Output Options

```python
# Warning only
output = {
    "systemMessage": "Warning shown to user"
}

# Block action (exit 2)
print("Error message", file=sys.stderr)
sys.exit(2)

# Modify input
output = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "updatedInput": {"command": "modified command"}
    }
}

# Add context for Claude
output = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "additionalContext": "Extra info for Claude"
    }
}

# Auto-approve permission
output = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",  # or "deny", "ask"
        "permissionDecisionReason": "Safe file"
    }
}
```

## Best Practices

### Performance
- Keep hooks under 5 seconds
- Use timeouts to prevent hanging
- Cache expensive operations
- Run async when possible

### User Experience
- Prefer warnings over blocking
- Keep messages concise
- Avoid repetitive warnings
- Use `suppressOutput` for silent operations

### Security
- Validate all inputs
- Use absolute paths for scripts
- Never execute user input directly
- Check for path traversal (`..`)

### Reliability
- Handle missing data gracefully
- Test with `claude --debug`
- Log errors to stderr
- Use try/except blocks

## Debugging Hooks

```bash
# Run with debug output
claude --debug

# Test hook directly
echo '{"tool_name":"Bash","tool_input":{"command":"npm test"}}' | python3 ~/.claude/hooks/tmux-reminder.py

# Check hook execution in logs
tail -f ~/.claude/logs/hooks.log  # If logging is configured
```

## Configuration Examples

### Project-Specific Hooks

```json
// .claude/settings.json in project
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{
          "type": "command",
          "command": "echo 'Project-specific warning'"
        }]
      }
    ]
  }
}
```

### Conditional Hooks

```python
# Only run in production branch
import subprocess

def get_current_branch():
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

if get_current_branch() == "production":
    output = {
        "systemMessage": "⚠️  PRODUCTION BRANCH - Double-check changes!"
    }
    print(json.dumps(output))
```

### Time-Based Hooks

```python
from datetime import datetime

hour = datetime.now().hour
if 9 <= hour <= 17:  # Business hours
    output = {
        "systemMessage": "Business hours - avoid risky deployments"
    }
    print(json.dumps(output))
```

## Common Patterns

### 1. Command Modification
```python
# Replace commands
if "rm -rf" in command:
    modified = command.replace("rm -rf", "rm -i")
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "updatedInput": {"command": modified}
        }
    }
```

### 2. Context Awareness
```python
# Add context based on environment
if os.environ.get("NODE_ENV") == "production":
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": "Running in PRODUCTION environment"
        }
    }
```

### 3. Smart Permissions
```python
# Auto-approve safe operations
safe_paths = ["/docs/", "/tests/", "README"]
if any(path in file_path for path in safe_paths):
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "suppressOutput": True
        }
    }
```

## Tmux-Specific Hook Examples

Since you mentioned tmux as a priority, here are detailed examples:

### Smart Tmux Detection
```python
#!/usr/bin/env python3
"""tmux-smart-reminder.py - Context-aware tmux suggestions."""

def get_tmux_suggestion(command):
    """Provide specific tmux tips based on command."""

    suggestions = {
        "npm run dev": "tmux new -s dev 'npm run dev'",
        "cargo watch": "tmux new -s watch 'cargo watch'",
        "pytest --watch": "tmux new -s test 'pytest --watch'",
        "docker compose up": "tmux new -s docker 'docker compose up'",
    }

    for pattern, suggestion in suggestions.items():
        if pattern in command:
            return f"💡 Quick start: {suggestion}"

    return "💡 Consider: tmux new -s session-name"
```

### Tmux Session Manager Hook
```python
# List existing sessions if relevant
import subprocess

def get_tmux_sessions():
    result = subprocess.run(["tmux", "ls"], capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip().split('\n')
    return []

sessions = get_tmux_sessions()
if sessions and "dev" in command:
    session_list = '\n'.join(f"  - {s}" for s in sessions)
    output = {
        "systemMessage": f"📺 Existing tmux sessions:\n{session_list}\nAttach with: tmux a -t session-name"
    }
```

## Integration with Remember Instructions

Hooks can work with your remember instructions to provide consistent reminders:

### SessionStart Hook for Remember Items
```python
#!/usr/bin/env python3
"""session-context.py - Load remember instructions and project context."""

import json
import os
from pathlib import Path

def load_remember_items():
    """Load items from remember skill storage."""
    remember_file = Path.home() / ".claude" / "memory" / "remember.json"
    if remember_file.exists():
        with open(remember_file) as f:
            items = json.load(f)
            return [item for item in items if item.get("active", True)]
    return []

# Show relevant remember items at session start
items = load_remember_items()
if items:
    reminders = "\n".join(f"  • {item['content']}" for item in items[:5])
    print(json.dumps({
        "systemMessage": f"📝 Remember:\n{reminders}"
    }))
```

## Hook Development Workflow

1. **Create Hook Script**
   ```bash
   # Create new hook
   nvim ~/dotfiles/agents/hooks/my-new-hook.py
   chmod +x ~/dotfiles/agents/hooks/my-new-hook.py
   ```

2. **Add to Nix Config**
   ```nix
   # Edit home/modules/claude/config.nix
   PreToolUse = [
     {
       matcher = "Bash";
       hooks = [
         { type = "command"; command = "${../hooks/my-new-hook.py}"; }
       ];
     }
   ];
   ```

3. **Test and Deploy**
   ```bash
   # Test hook directly
   echo '{"tool_name":"Bash","tool_input":{"command":"npm test"}}' | \
     python3 ~/dotfiles/agents/hooks/my-new-hook.py

   # Apply configuration
   home-manager switch

   # Restart Claude Code to load new hooks
   ```

## Debugging Tips

### Enable Hook Debugging
```bash
# Add to your shell config
export CLAUDE_HOOK_DEBUG=1

# Or run Claude with debug flag
claude --debug
```

### Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| Hook not firing | Check matcher pattern, verify file permissions |
| Hook crashes Claude | Wrap in try/except, always exit 0 on error |
| Slow performance | Add timeout, cache expensive operations |
| Too many warnings | Use state file to track shown warnings |

## Remember: Hooks Should Enhance, Not Annoy

The goal is to make Claude Code work better for YOUR workflow by:
- Preventing mistakes before they happen (rm -rf protection)
- Adding context when needed (git status, tmux reminders)
- Automating repetitive tasks (formatting, linting)
- Maintaining consistency (commit conventions, project rules)

Keep them fast (<100ms), relevant, and helpful!