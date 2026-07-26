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
          command = "${runHook} ${hooksPath}/pre-tool-use-dispatcher.py";
          timeout = 10000;
        }
        {
          type = "command";
          command = "${prohibitedWordsAllowedEnvironmentAssignment} ${runHook} ${hooksPath}/prohibited-words-guard.py";
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
          command = "${runHook} ${hooksPath}/post-tool-use-dispatcher.py";
          timeout = 15000;
        }
      ];
    }
    {
      matcher = "Edit|Write";
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
