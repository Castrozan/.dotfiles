{
  hooksPath,
  runHook,
}:
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
      matcher = "compact";
      hooks = [
        {
          type = "command";
          command = "${runHook} ${hooksPath}/compaction-context-recovery.py";
          timeout = 3000;
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
          command = "${runHook} ${hooksPath}/tldr-reminder.py";
          timeout = 2000;
        }
      ];
    }
  ];

  Stop = [
    {
      matcher = ".*";
      hooks = [
        {
          type = "command";
          command = "${runHook} ${hooksPath}/lint-turn-review.py";
          timeout = 5000;
        }
        {
          type = "command";
          command = "${runHook} ${hooksPath}/end-of-turn-format-guard.py";
          timeout = 5000;
        }
      ];
    }
  ];

  SubagentStop = [
    {
      matcher = ".*";
      hooks = [
        {
          type = "command";
          command = "${runHook} ${hooksPath}/lint-turn-review.py";
          timeout = 5000;
        }
      ];
    }
  ];
}
