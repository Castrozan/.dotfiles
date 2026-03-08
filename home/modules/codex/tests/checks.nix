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
        self.homeManagerModules.codex
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
  codex-bin-wrapper =
    mkEvalCheck "codex-bin-wrapper" (builtins.hasAttr ".local/bin/codex" cfg.home.file)
      ".local/bin/codex should be in home.file";

  codex-skills-directory =
    mkEvalCheck "codex-skills-directory" (hasFilePrefix ".codex/skills/")
      "skills directory entries should be in home.file";
}
