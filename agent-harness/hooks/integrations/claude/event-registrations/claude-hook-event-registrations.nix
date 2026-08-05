{
  lib,
  hostname,
  isDarwin ? false,
  privateConfigRoot ? ../../../../../private-config,
}:
let
  hooksPath = "~/.claude/hooks";
  runHook = "${hooksPath}/run-hook.sh";

  machinesRegistryFile = privateConfigRoot + "/machines.nix";
  machineAllowedProhibitedWordsFile =
    privateConfigRoot + "/machines/${hostname}/claude-prohibited-words-allowed.nix";
  machineAllowedProhibitedWords =
    if !(builtins.pathExists machinesRegistryFile) && isDarwin then
      throw ''
        private-config/machines.nix is missing from the flake source, so the per-machine
        prohibited-words allowlist would silently degrade to empty and the guard would block
        sessions that the machine allowlist is meant to exempt. Refusing to build the darwin
        hook registrations; rebuild from a flake source that carries the private-config
        submodule content (a git+file flake ref with ?submodules=1).
      ''
    else if builtins.pathExists machineAllowedProhibitedWordsFile then
      import machineAllowedProhibitedWordsFile
    else
      [ ];
  prohibitedWordsAllowedEnvironmentAssignment =
    "PROHIBITED_WORDS_ALLOWED="
    + lib.escapeShellArg (lib.concatStringsSep "," machineAllowedProhibitedWords);

  hooksEventDefinition = import ../../../runtime/event-to-dispatcher-map.nix;

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
