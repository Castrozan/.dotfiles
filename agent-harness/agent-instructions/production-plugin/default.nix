{
  pkgs,
  lib,
  hostname,
  homeDirectory,
  chromePackage,
  isDarwin ? pkgs.stdenv.isDarwin,
}:
let
  distribution = import ../../plugin-distribution { inherit pkgs; };
  artifacts = import ./artifacts.nix {
    inherit
      pkgs
      lib
      hostname
      homeDirectory
      chromePackage
      isDarwin
      ;
  };
  artifactEntries = artifacts.entries;
  version =
    "1.0.0+"
    + builtins.substring 0 12 (
      builtins.hashString "sha256" (
        builtins.toJSON artifactEntries
        + builtins.hashFile "sha256" ./default.nix
        + "${distribution.package}"
      )
    );
  manifest = {
    "$schema" = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json";
    name = "dotfiles";
    inherit version;
    description = "Shared agent instructions, skills, agents, hooks, workflows and supporting assets.";
    extensions."com.openai".interface.displayName = "Dotfiles";
  };
  nativeManifest = {
    inherit (manifest) name description;
    inherit version;
    skills = "./skills";
    mcpServers = "./.claude-plugin/mcp.json";
  };
  inventory = {
    package = manifest.name;
    inherit version;
    artifacts = map (entry: {
      inherit (entry) name;
      source = "${entry.path}";
    }) artifactEntries;
    inherit (artifacts) discovery;
  };
  sourceParts = pkgs.linkFarm "dotfiles-agent-plugin-parts" (
    artifactEntries
    ++ [
      {
        name = "plugin.json";
        path = pkgs.writeText "dotfiles-plugin.json" (builtins.toJSON manifest);
      }
      {
        name = ".claude-plugin/plugin.json";
        path = pkgs.writeText "dotfiles-claude-plugin.json" (builtins.toJSON nativeManifest);
      }
      {
        name = "artifact-inventory.json";
        path = pkgs.writeText "dotfiles-artifact-inventory.json" (builtins.toJSON inventory);
      }
    ]
  );
in
pkgs.runCommand "dotfiles-agent-plugin" { } ''
  mkdir -p "$out"
  cp -rL ${sourceParts}/. "$out"/
''
