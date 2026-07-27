{
  pkgs,
  lib,
  hostname,
  ...
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

  codexHooksConfiguration = {
    hooks = {
      SessionStart = [
        {
          matcher = "startup|resume|clear|compact";
          hooks = [
            {
              type = "command";
              command = runCodexDispatcher "session-start-dispatcher.py";
              timeout = 5;
              statusMessage = "Loading deep-work context";
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
              command = "${prohibitedWordsAllowedEnvironmentAssignment} ${runCodexDispatcher "pre-tool-use-dispatcher.py"}";
              timeout = 5;
            }
          ];
        }
      ];
      PostToolUse = [
        {
          matcher = ".*";
          hooks = [
            {
              type = "command";
              command = runCodexDispatcher "post-tool-use-dispatcher.py";
              timeout = 15;
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
              command = runCodexDispatcher "stop-dispatcher.py";
              timeout = 15;
            }
          ];
        }
      ];
    };
  };
in
{
  home.file.".codex/hooks.json".text = builtins.toJSON codexHooksConfiguration;
}
