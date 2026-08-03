{
  pkgs,
  lib,
  hostname,
  isDarwin ? false,
  privateConfigRoot ? ../../../../private-config,
}:
let
  agentHookScripts = import ../../agent-hooks/flat-hook-scripts-directory.nix { inherit pkgs lib; };

  runCodexDispatcher =
    dispatcherFilename:
    "${agentHookScripts}/run-hook.sh ${agentHookScripts}/${dispatcherFilename} --surface=codex";

  machinesRegistryFile = privateConfigRoot + "/machines.nix";
  machineAllowedProhibitedWordsFile =
    privateConfigRoot + "/machines/${hostname}/claude-prohibited-words-allowed.nix";
  machineAllowedProhibitedWords =
    if !(builtins.pathExists machinesRegistryFile) && isDarwin then
      throw ''
        private-config/machines.nix is missing from the flake source, so the per-machine
        prohibited-words allowlist would silently degrade to empty and the guard would block
        sessions that the machine allowlist is meant to exempt. Refusing to build the codex
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
