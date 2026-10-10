{
  pkgs,
  lib,
  hostname,
  isDarwin ? false,
  privateConfigRoot ? ../../../../private-configuration,
}:
let
  scripts = import ../../../hooks/flat-hook-scripts-directory.nix { inherit pkgs lib; };
  dispatchers = (import ../../../hooks/runtime/event-to-dispatcher-map.nix).dispatchersByEvent;
  registry = privateConfigRoot + "/machines.nix";
  allowlist = privateConfigRoot + "/machines/${hostname}/claude-prohibited-words-allowed.nix";
  allowedWords =
    if isDarwin && !(builtins.pathExists registry) then
      throw "Rulesync hook generation requires private-configuration/machines.nix on Darwin"
    else if builtins.pathExists allowlist then
      import allowlist
    else
      [ ];
  allowlistAssignment = "PROHIBITED_WORDS_ALLOWED=${lib.escapeShellArg (lib.concatStringsSep "," allowedWords)} ";
  command =
    event:
    (lib.optionalString (event == "PreToolUse") allowlistAssignment)
    + "@runner@ ${scripts}/${dispatchers.${event}} --surface=@surface@";
  registration = event: timeout: {
    type = "command";
    inherit timeout;
    command = command event;
  };
in
{
  version = 1;
  hooks = {
    sessionStart = [ (registration "SessionStart" 5) ];
    preToolUse = [ ((registration "PreToolUse" 5) // { matcher = ".*"; }) ];
    postToolUse = [ ((registration "PostToolUse" 15) // { matcher = ".*"; }) ];
    stop = [ (registration "Stop" 15) ];
  };
  claudecode.hooks = {
    sessionStart = [ ((registration "SessionStart" 5) // { matcher = ".*"; }) ];
    preToolUse = [ ((registration "PreToolUse" 10) // { matcher = ".*"; }) ];
    postToolUse = [ ((registration "PostToolUse" 15) // { matcher = "Skill|Edit|Write"; }) ];
    stop = [ (registration "Stop" 5) ];
    subagentStop = [ (registration "SubagentStop" 5) ];
    permissionRequest = [
      {
        type = "command";
        matcher = ".*";
        command = ''echo '{"hookSpecificOutput":{"hookEventName":"PermissionRequest","permissionDecision":"allow","permissionDecisionReason":"auto-approved"}}' '';
        timeout = 1;
      }
    ];
  };
  codexcli.hooks = {
    sessionStart = [ ((registration "SessionStart" 5) // { matcher = ".*"; }) ];
    beforeSubmitPrompt = [ (registration "UserPromptSubmit" 5) ];
  };
  opencode.apiVersion = 2;
}
