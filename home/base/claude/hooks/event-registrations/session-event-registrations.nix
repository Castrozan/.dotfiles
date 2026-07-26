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
          command = "${runHook} ${hooksPath}/session-start-dispatcher.py";
          timeout = 5000;
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
          command = "${runHook} ${hooksPath}/user-prompt-submit-dispatcher.py";
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
          command = "${runHook} ${hooksPath}/stop-dispatcher.py";
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
          command = "${runHook} ${hooksPath}/stop-dispatcher.py";
          timeout = 5000;
        }
      ];
    }
  ];
}
