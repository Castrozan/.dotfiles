{
  pkgs,
  lib,
  hostname,
  ...
}:
let
  codexHookScripts = import ./hook-scripts.nix { inherit pkgs lib; };

  runCodexHookScript =
    scriptFilename: "${pkgs.python3}/bin/python3 ${codexHookScripts}/${scriptFilename}";

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
              command = "cat ~/.dotfiles/.deep-work/*/context.md 2>/dev/null || true";
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
              command = runCodexHookScript "memory-recall.py";
              timeout = 5;
            }
            {
              type = "command";
              command = runCodexHookScript "prohibited-command-guard.py";
              timeout = 3;
            }
            {
              type = "command";
              command = "${prohibitedWordsAllowedEnvironmentAssignment} ${runCodexHookScript "prohibited-words-guard.py"}";
              timeout = 3;
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
              command = runCodexHookScript "auto-format.py";
              timeout = 15;
            }
            {
              type = "command";
              command = runCodexHookScript "record-edited-source-file.py";
              timeout = 3;
            }
            {
              type = "command";
              command = runCodexHookScript "nix-rebuild-trigger.py";
              timeout = 5;
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
              command = runCodexHookScript "lint-turn-review.py";
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
