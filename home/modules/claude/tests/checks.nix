{
  pkgs,
  lib,
  inputs,
  self,
  nixpkgs-version,
  home-version,
}:
let
  helpers = import ../../../../tests/nix-checks/helpers.nix {
    inherit
      pkgs
      lib
      inputs
      nixpkgs-version
      home-version
      ;
  };
  inherit (helpers) mkEvalCheck;

  cfg =
    (inputs.home-manager.lib.homeManagerConfiguration {
      inherit pkgs;
      modules = [
        self.homeManagerModules.claude-code
        {
          home = {
            username = "test";
            homeDirectory = "/home/test";
            inherit (helpers) stateVersion;
          };
        }
      ];
    }).config;

  fileNames = builtins.attrNames cfg.home.file;

  hasFilePrefix =
    prefix: builtins.any (n: builtins.substring 0 (builtins.stringLength prefix) n == prefix) fileNames;
in
{
  claude-settings-json =
    mkEvalCheck "claude-settings-json" (builtins.hasAttr ".claude/settings.json" cfg.home.file)
      "settings.json should be in home.file";

  claude-hooks-directory =
    mkEvalCheck "claude-hooks-directory" (hasFilePrefix ".claude/hooks/")
      "hooks directory entries should be in home.file";

  claude-skills-directory =
    mkEvalCheck "claude-skills-directory" (hasFilePrefix ".claude/skills/")
      "skills directory entries should be in home.file";

  claude-mcp-json =
    mkEvalCheck "claude-mcp-json" (builtins.hasAttr ".claude/mcp.json" cfg.home.file)
      "mcp.json should be in home.file";

  claude-bin-wrapper =
    mkEvalCheck "claude-bin-wrapper" (builtins.hasAttr ".local/bin/claude" cfg.home.file)
      ".local/bin/claude should be in home.file";
}
