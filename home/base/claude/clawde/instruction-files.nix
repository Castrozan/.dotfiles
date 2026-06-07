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
    buildAgentClaudeMarkdownContentByName
    ;

  agentInstructionsFiles = lib.listToAttrs (
    map (name: {
      name = runtimeLocations.agentInstructionsRelativeToHome name;
      value = {
        text = buildAgentClaudeMarkdownContentByName name;
      };
    }) agentNames
  );
in
{
  config = lib.mkIf hasAgents {
    home.file = agentInstructionsFiles;
  };
}
