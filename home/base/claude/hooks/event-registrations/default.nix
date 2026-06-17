{ lib, hostname }:
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

  toolEventRegistrations = import ./tool-event-registrations.nix {
    inherit hooksPath runHook prohibitedWordsAllowedEnvironmentAssignment;
  };
  sessionEventRegistrations = import ./session-event-registrations.nix {
    inherit hooksPath runHook;
  };
in
toolEventRegistrations // sessionEventRegistrations
