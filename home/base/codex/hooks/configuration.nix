{
  pkgs,
  lib,
  hostname,
}:
let
  agentHookScripts = import ../../agent-hooks/flat-hook-scripts-directory.nix { inherit pkgs lib; };

  runCodexDispatcher =
    dispatcherFilename:
    "${agentHookScripts}/run-hook.sh ${agentHookScripts}/${dispatcherFilename} --surface=codex";

  machineAllowedProhibitedWordsFile =
    ../../../../private-config/machines + "/${hostname}/claude-prohibited-words-allowed.nix";
  machineAllowedProhibitedWords =
    if builtins.pathExists machineAllowedProhibitedWordsFile then
      import machineAllowedProhibitedWordsFile
    else
      [ ];
  prohibitedWordsAllowedEnvironmentAssignment =
    "PROHIBITED_WORDS_ALLOWED="
    + lib.escapeShellArg (lib.concatStringsSep "," machineAllowedProhibitedWords);

  hooksEventDefinition = import ../../../../agents/hooks/event-to-dispatcher-map.nix;

  codexSupportedHookEvents = [
    "SessionStart"
    "PreToolUse"
    "PostToolUse"
    "Stop"
  ];

  codexEventTimeouts = {
    SessionStart = 5;
    PreToolUse = 5;
    PostToolUse = 15;
    Stop = 15;
  };

  codexHookEvents =
    lib.mapAttrs
      (event: dispatcher: [
        {
          matcher = ".*";
          hooks = [
            {
              type = "command";
              command =
                if event == "PreToolUse" then
                  "${prohibitedWordsAllowedEnvironmentAssignment} ${runCodexDispatcher dispatcher}"
                else
                  runCodexDispatcher dispatcher;
              timeout = codexEventTimeouts.${event};
            }
          ];
        }
      ])
      (
        lib.filterAttrs (
          event: _: lib.elem event codexSupportedHookEvents
        ) hooksEventDefinition.dispatchersByEvent
      );
in
codexHookEvents
