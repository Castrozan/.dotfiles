{
  pkgs,
  lib,
  inputs,
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

  cfg = helpers.homeManagerTestConfiguration [
    ../neovim.nix
    ../zed-editor.nix
  ];

  hasFile = name: builtins.hasAttr name cfg.home.file;
in
{
  domain-editor-neovim-config = mkEvalCheck "domain-editor-neovim-config" (
    cfg.programs.neovim.enable && hasFile ".config/nvim"
  ) "neovim should be enabled with config directory";
}
