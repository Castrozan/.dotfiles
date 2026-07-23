{
  pkgs,
  lib,
  inputs,
  nixpkgs-version,
  home-version,
}:
let
  helpers = import ../../../../__tests__/nix-checks/helpers.nix {
    inherit
      pkgs
      lib
      inputs
      nixpkgs-version
      home-version
      ;
  };
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [
    ../neovim.nix
    ../zed-editor.nix
  ];

  hasFile = name: builtins.hasAttr name cfg.home.file;
  hasDataFile = name: builtins.hasAttr name cfg.xdg.dataFile;
in
{
  domain-editor-neovim-config = mkEvalCheck "domain-editor-neovim-config" (
    cfg.programs.neovim.enable && hasFile ".config/nvim" && hasDataFile "nvim/site/spell/pt.utf-8.spl"
  ) "neovim should be enabled with config directory and the pt_br spell dictionary on runtimepath";
}
