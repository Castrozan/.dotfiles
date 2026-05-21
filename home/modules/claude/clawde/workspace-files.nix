{
  config,
  lib,
  pkgs,
  ...
}:
let
  helpers = import ./lib.nix { inherit pkgs config lib; };
  inherit (helpers)
    cfg
    hasAgents
    homeDir
    agentNames
    agentWorkspaceDirectory
    ;

  workspaceRelativeToHome =
    name:
    let
      workspace = agentWorkspaceDirectory name;
    in
    lib.removePrefix "${homeDir}/" workspace;

  agentsWithDenyToolPatterns = builtins.filter (
    name: cfg.agents.${name}.denyToolPatterns != [ ]
  ) agentNames;

  agentWorkspaceSettingsFiles = lib.listToAttrs (
    map (name: {
      name = "${workspaceRelativeToHome name}/.claude/settings.json";
      value = {
        text = builtins.toJSON {
          permissions = {
            deny = cfg.agents.${name}.denyToolPatterns;
          };
        };
      };
    }) agentsWithDenyToolPatterns
  );
in
{
  config = lib.mkIf hasAgents {
    home.file = agentWorkspaceSettingsFiles;
  };
}
