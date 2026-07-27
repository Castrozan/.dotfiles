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
          command = "${prohibitedWordsAllowedEnvironmentAssignment} ${runHook} ${hooksPath}/pre-tool-use-dispatcher.py";
          timeout = 10000;
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
      matcher = "Skill|Edit|Write";
      hooks = [
        {
          type = "command";
          command = "${runHook} ${hooksPath}/post-tool-use-dispatcher.py";
          timeout = 15000;
        }
      ];
    }
  ];
}
