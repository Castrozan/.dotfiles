{
  config,
  lib,
  pkgs,
  ...
}:
let
  helpers = import ./lib.nix { inherit pkgs config lib; };
  inherit (helpers)
    hasAgents
    agentNames
    runtimeLocations
    buildAgentLaunchConfigByName
    ;

  agentLaunchConfigFiles = lib.listToAttrs (
    map (name: {
      name = runtimeLocations.agentLaunchConfigRelativeToHome name;
      value = {
        text = builtins.toJSON (buildAgentLaunchConfigByName name);
      };
    }) agentNames
  );
in
{
  config = lib.mkIf hasAgents {
    home.file = agentLaunchConfigFiles;
  };
}
