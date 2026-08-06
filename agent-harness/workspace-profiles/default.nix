{
  pkgs,
  lib,
  hostname,
  ...
}:
let
  declaredWorkspaceProfiles = import ./profile-declarations.nix { inherit hostname; };

  routingTableFile = import ./routing/routing-table.nix {
    inherit pkgs;
    workspaceProfiles = declaredWorkspaceProfiles;
  };

  resolverPackage = import ./routing/resolver-package.nix { inherit pkgs routingTableFile; };
in
{
  options.agentWorkspaceProfiles = {
    profiles = lib.mkOption {
      type = lib.types.listOf (lib.types.attrsOf lib.types.anything);
      default = declaredWorkspaceProfiles;
      readOnly = true;
      description = "Workspace profiles declared for this machine, each carrying the directory prefixes and git remote patterns that select it plus one payload section per harness. Every harness wrapper reads this same list, so a profile added here reaches claude, codex and opencode without a second declaration.";
    };

    routingTableFile = lib.mkOption {
      type = lib.types.path;
      default = routingTableFile;
      readOnly = true;
      description = "The routing-only projection of the declared profiles, the single input the harness-agnostic resolver reads. Payload sections are deliberately absent so a harness payload change never invalidates the resolver's inputs.";
    };

    resolverExecutable = lib.mkOption {
      type = lib.types.str;
      default = "${resolverPackage}/bin/resolve-workspace-profile";
      readOnly = true;
      description = "Absolute path to the resolver that maps a working directory to a profile name. Harness wrappers call it by this path rather than through PATH, because a wrapper launched from a stripped environment still has to route.";
    };
  };

  config.home.packages = [ resolverPackage ];
}
