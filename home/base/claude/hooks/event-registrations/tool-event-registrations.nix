{
  hooksPath,
  runHook,
  prohibitedWordsAllowedEnvironmentAssignment,
}:
{
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
        {
          type = "command";
          command = "${prohibitedWordsAllowedEnvironmentAssignment} ${runHook} ${hooksPath}/prohibited-words-guard.py";
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
      matcher = "mcp__codex__codex";
      hooks = [
        {
          type = "command";
          command = "${runHook} ${hooksPath}/codex-sandbox-downgrade-guard.py";
          timeout = 2000;
        }
      ];
    }
    {
      matcher = "WebFetch";
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
    {
      matcher = "Write|Edit";
      hooks = [
        {
          type = "command";
          command = "${runHook} ${hooksPath}/agent-instruction-file-authoring-router.py";
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
      matcher = "Skill";
      hooks = [
        {
          type = "command";
          command = "${runHook} ${hooksPath}/record-instructions-skill-invocation.py";
          timeout = 3000;
        }
      ];
    }
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
          command = "${runHook} ${hooksPath}/record-edited-source-file.py";
          timeout = 3000;
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
