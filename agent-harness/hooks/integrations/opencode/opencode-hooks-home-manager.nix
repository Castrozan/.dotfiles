{
  pkgs,
  lib,
  hostname,
  isDarwin ? false,
  ...
}:
let
  agentHookScripts = import ../../home-manager/flat-hook-scripts-directory.nix { inherit pkgs lib; };

  privateConfigRoot = ../../../../private-config;

  machinesRegistryFile = privateConfigRoot + "/machines.nix";
  machineAllowedProhibitedWordsFile =
    privateConfigRoot + "/machines/${hostname}/claude-prohibited-words-allowed.nix";
  machineAllowedProhibitedWords =
    if !(builtins.pathExists machinesRegistryFile) && isDarwin then
      throw ''
        private-config/machines.nix is missing from the flake source, so the per-machine
        prohibited-words allowlist would silently degrade to empty and the guard would block
        sessions that the machine allowlist is meant to exempt. Refusing to build the OpenCode
        hook bridge; rebuild from a flake source that carries the private-config submodule
        content (a git+file flake ref with ?submodules=1).
      ''
    else if builtins.pathExists machineAllowedProhibitedWordsFile then
      import machineAllowedProhibitedWordsFile
    else
      [ ];

  opencodeHookDispatcher = pkgs.writeShellScript "opencode-hook-dispatcher" ''
    export PROHIBITED_WORDS_ALLOWED=${lib.escapeShellArg (lib.concatStringsSep "," machineAllowedProhibitedWords)}
    exec ${agentHookScripts}/run-hook.sh "${agentHookScripts}/$1" --surface=opencode
  '';

  opencodeHookBridge = pkgs.replaceVars ./opencode-hook-bridge.js {
    inherit opencodeHookDispatcher;
  };
in
{
  home.file.".config/opencode/plugins/opencode-hook-bridge.js".source = opencodeHookBridge;
}
