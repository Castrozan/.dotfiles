{
  pkgs,
  lib,
  inputs,
  self,
}:
let
  helpers = import ../../../../tests/nix-checks/helpers.nix { inherit pkgs lib inputs; };
  inherit (helpers) mkEvalCheck;

  cfg =
    (inputs.home-manager.lib.homeManagerConfiguration {
      inherit pkgs;
      modules = [
        self.homeManagerModules.codex
        {
          home.username = "test";
          home.homeDirectory = "/home/test";
          home.stateVersion = "25.11";
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
