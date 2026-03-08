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

  cfg = helpers.homeManagerTestConfiguration [ ../. ];

  hasFile = name: builtins.hasAttr name cfg.home.file;
  hasService = name: builtins.hasAttr name cfg.systemd.user.services;
in
{
  domain-ollama-service-binary = mkEvalCheck "domain-ollama-service-binary" (
    hasService "ollama" && hasFile ".local/bin/ollama"
  ) "ollama should have service and binary";
}
