{
  pkgs,
  lib,
  hostname,
  isDarwin ? false,
  ...
}:
let
  agentHookScripts = import ../../flat-hook-scripts-directory.nix { inherit pkgs lib; };

  privateConfigRoot = ../../../../private-configuration;

  machinesRegistryFile = privateConfigRoot + "/machines.nix";
  machineAllowedProhibitedWordsFile =
    privateConfigRoot + "/machines/${hostname}/claude-prohibited-words-allowed.nix";
  machineAllowedProhibitedWords =
    if !(builtins.pathExists machinesRegistryFile) && isDarwin then
      throw ''
        private-configuration/machines.nix is missing from the flake source, so the per-machine
        prohibited-words allowlist would silently degrade to empty and the guard would block
        sessions that the machine allowlist is meant to exempt. Refusing to build the Hermes
        hook bridge; rebuild from a flake source that carries the private-configuration submodule
        content (a git+file flake ref with ?submodules=1).
      ''
    else if builtins.pathExists machineAllowedProhibitedWordsFile then
      import machineAllowedProhibitedWordsFile
    else
      [ ];

  hermesHookDispatcher = pkgs.writeShellScript "hermes-hook-dispatcher" ''
    export PROHIBITED_WORDS_ALLOWED=${lib.escapeShellArg (lib.concatStringsSep "," machineAllowedProhibitedWords)}
    exec ${agentHookScripts}/run-hook.sh "${agentHookScripts}/$1" --surface=hermes
  '';
in
{
  hermesHookCommand = pkgs.writeShellScript "hermes-hook-bridge" ''
    exec ${pkgs.python312}/bin/python3 ${./translate_hermes_hook_call.py} ${hermesHookDispatcher}
  '';
}
