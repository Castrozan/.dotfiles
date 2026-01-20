# Hook configuration for Claude Code settings.json
# This file defines which hooks run at each lifecycle event.
# The actual hook scripts are symlinked by hook-symlinks.nix
let
  hooksPath = "~/.claude/hooks";
  runHook = "${hooksPath}/run-hook.sh";
in {
  # Run at session start
  SessionStart = [
    {
      matcher = ".*";
      hooks = [
        {
          type = "command";
          command = "${runHook} ${hooksPath}/session-context.py";
          timeout = 5000;
        }
      ];
    }
  ];

  # Run before tool execution
  PreToolUse = [
    {
      matcher = "Bash";
      hooks = [
        # Tmux and timing
        {
          type = "command";
          command = "${runHook} ${hooksPath}/tmux-reminder.py";
          timeout = 3000;
        }
        {
          type = "command";
          command = "${runHook} ${hooksPath}/command-timing.py";
          timeout = 2000;
        }
        # Safety checks
        {
          type = "command";
          command = "${runHook} ${hooksPath}/dangerous-command-guard.py";
          timeout = 3000;
        }
        # Git workflow
        {
          type = "command";
          command = "${runHook} ${hooksPath}/git-reminder.py";
          timeout = 5000;
        }
        {
          type = "command";
          command = "${runHook} ${hooksPath}/branch-protection.py";
          timeout = 5000;
        }
        {
          type = "command";
          command = "${runHook} ${hooksPath}/worktree-reminder.py";
          timeout = 5000;
        }
        {
          type = "command";
          command = "${runHook} ${hooksPath}/test-before-commit.py";
          timeout = 5000;
        }
        {
          type = "command";
          command = "${runHook} ${hooksPath}/delegation-reminder.py";
          timeout = 5000;
        }
      ];
    }
    {
      matcher = "Edit|Write";
      hooks = [
        {
          type = "command";
          command = "${runHook} ${hooksPath}/sensitive-file-guard.py";
          timeout = 3000;
        }
      ];
    }
    {
      matcher = "Task";
      hooks = [
        {
          type = "command";
          command = "${runHook} ${hooksPath}/subagent-context-reminder.py";
          timeout = 3000;
        }
      ];
    }
  ];

  # Run after tool execution
  PostToolUse = [
    {
      matcher = "Bash";
      hooks = [
        {
          type = "command";
          command = "${runHook} ${hooksPath}/command-timing.py";
          timeout = 2000;
        }
      ];
    }
    {
      matcher = "Edit|Write";
      hooks = [
        {
          type = "command";
          command = "${runHook} ${hooksPath}/nix-rebuild-reminder.py";
          timeout = 3000;
        }
        {
          type = "command";
          command = "${runHook} ${hooksPath}/auto-format.py";
          timeout = 15000;
        }
        {
          type = "command";
          command = "${runHook} ${hooksPath}/lint-on-edit.py";
          timeout = 30000;
        }
      ];
    }
  ];

  # Run when user submits a prompt
  UserPromptSubmit = [
    {
      matcher = ".*";
      hooks = [
        {
          type = "command";
          command = "${runHook} ${hooksPath}/delegation-reminder.py";
          timeout = 3000;
        }
      ];
    }
  ];
}
