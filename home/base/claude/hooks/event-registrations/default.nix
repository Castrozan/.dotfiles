{
  lib,
  hostname,
}:
let
  hooksPath = "~/.claude/hooks";
  runHook = "${hooksPath}/run-hook.sh";

  machineAllowedProhibitedWordsFile =
    ../../../../../private-config/machines + "/${hostname}/claude-prohibited-words-allowed.nix";
  machineAllowedProhibitedWords =
    if builtins.pathExists machineAllowedProhibitedWordsFile then
      import machineAllowedProhibitedWordsFile
    else
      [ ];
  prohibitedWordsAllowedEnvironmentAssignment =
    "PROHIBITED_WORDS_ALLOWED="
    + lib.escapeShellArg (lib.concatStringsSep "," machineAllowedProhibitedWords);

  hooksEventDefinition = import ../../../../../agents/hooks/event-to-dispatcher-map.nix;

  claudeEventTimeouts = {
    PreToolUse = 10000;
    PostToolUse = 15000;
    SessionStart = 5000;
    UserPromptSubmit = 2000;
    Stop = 5000;
    SubagentStop = 5000;
  };

  claudeEventMatchers = {
    PreToolUse = ".*";
    PostToolUse = "Skill|Edit|Write";
    SessionStart = ".*";
    UserPromptSubmit = ".*";
    Stop = ".*";
    SubagentStop = ".*";
  };

  dispatcherRegistrationForEvent = event: dispatcher: [
    {
      matcher = claudeEventMatchers.${event};
      hooks = [
        {
          type = "command";
          command =
            if event == "PreToolUse" then
              "${prohibitedWordsAllowedEnvironmentAssignment} ${runHook} ${hooksPath}/${dispatcher}"
            else
              "${runHook} ${hooksPath}/${dispatcher}";
          timeout = claudeEventTimeouts.${event};
        }
      ];
    }
  ];

  dispatcherRegistrations = lib.mapAttrs (
    event: dispatcher: dispatcherRegistrationForEvent event dispatcher
  ) hooksEventDefinition.dispatchersByEvent;

  inlineExceptionRegistrations = lib.listToAttrs (
    map (
      event:
      lib.nameValuePair event [
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
      ]
    ) hooksEventDefinition.inlineExceptionEvents
  );
in
dispatcherRegistrations // inlineExceptionRegistrations
