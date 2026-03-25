let
  hooksPath = "~/.claude/hooks";
  runHook = "${hooksPath}/run-hook.sh";
in
{
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
    {
      matcher = ".*";
      hooks = [
        {
          type = "command";
          command = "${runHook} ${hooksPath}/deep-work-recovery.py";
          timeout = 5000;
        }
      ];
    }
  ];

  TeammateIdle = [
    {
      matcher = ".*";
      hooks = [
        {
          type = "command";
          command = "${runHook} ${hooksPath}/teammate-idle-quality-gate.py";
          timeout = 10000;
        }
      ];
    }
  ];

  TaskCompleted = [
    {
      matcher = ".*";
      hooks = [
        {
          type = "command";
          command = "${runHook} ${hooksPath}/task-completed-quality-gate.py";
          timeout = 30000;
        }
      ];
    }
  ];

  StopFailure = [
    {
      matcher = ".*";
      hooks = [
        {
          type = "command";
          command = "notify-send --app-name 'Claude Code' --urgency=critical 'Turn failed' \"$CLAUDE_STOP_REASON\" 2>/dev/null || true";
          timeout = 3000;
        }
      ];
    }
  ];

  PostCompact = [
    {
      matcher = ".*";
      hooks = [
        {
          type = "command";
          command = "${runHook} ${hooksPath}/deep-work-recovery.py";
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
          command = "${runHook} ${hooksPath}/workspace-directory-injector.py";
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
        {
          type = "command";
          command = "${runHook} ${hooksPath}/nix-rebuild-trigger.py";
          timeout = 3000;
        }
      ];
    }
  ];
}
