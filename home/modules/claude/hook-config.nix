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
  ];

  Stop = [
    # {
    #   matcher = ".*";
    #   hooks = [
    #     {
    #       type = "command";
    #       command = "${runHook} ${hooksPath}/end-of-work-compliance-review.py";
    #       timeout = 540000;
    #     }
    #   ];
    # }
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

  PreToolUse = [
    {
      matcher = ".*";
      hooks = [
        {
          type = "command";
          command = "${runHook} ${hooksPath}/memory-recall.py";
          timeout = 3000;
        }
        {
          type = "command";
          command = "${runHook} ${hooksPath}/prohibited-command-guard.py";
          timeout = 3000;
        }
      ];
    }
    {
      matcher = "Bash";
      hooks = [
        {
          type = "command";
          command = "${runHook} ${hooksPath}/workspace-directory-injector.py";
          timeout = 3000;
        }
        {
          type = "command";
          command = "${runHook} ${hooksPath}/background-bash-anti-pattern-validator.py";
          timeout = 3000;
        }
      ];
    }
    {
      matcher = "WebFetch|mcp__browser-use__browser_navigate";
      hooks = [
        {
          type = "command";
          command = "${runHook} ${hooksPath}/url-to-skill-router.py";
          timeout = 2000;
        }
      ];
    }
    {
      matcher = "Monitor";
      hooks = [
        {
          type = "command";
          command = "${runHook} ${hooksPath}/monitor-streaming-pattern-validator.py";
          timeout = 3000;
        }
      ];
    }
  ];

  PermissionRequest = [
    {
      matcher = ".*";
      hooks = [
        {
          type = "command";
          command = ''echo '{"hookSpecificOutput":{"hookEventName":"PermissionRequest","permissionDecision":"allow","permissionDecisionReason":"auto-approved"}}' '';
          timeout = 1000;
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
        {
          type = "command";
          command = "${runHook} ${hooksPath}/line-count-advisory-guard.py";
          timeout = 3000;
        }
      ];
    }
  ];
}
