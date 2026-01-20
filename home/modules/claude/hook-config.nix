let
  hooksPath = "~/.claude/hooks";
  runHook = "${hooksPath}/run-hook.sh";
in {
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

  PreToolUse = [
    {
      matcher = "Bash";
      hooks = [
        {
          type = "command";
          command = "${runHook} ${hooksPath}/tmux-reminder.py";
          timeout = 3000;
        }
        {
          type = "command";
          command = "${runHook} ${hooksPath}/dangerous-command-guard.py";
          timeout = 3000;
        }
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
          command = "${runHook} ${hooksPath}/delegation-reminder.py";
          timeout = 5000;
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

  PostToolUse = [
    {
      matcher = "Edit|Write";
      hooks = [
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
