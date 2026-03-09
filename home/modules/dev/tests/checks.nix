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
    ../lazygit.nix
    ../bruno.nix
    ../devenv.nix
    ../ccost.nix
    ../mcporter.nix
  ];

  packageNames = map (p: p.name or p.pname or "unknown") cfg.home.packages;
  hasXdgConfig = name: builtins.hasAttr name cfg.xdg.configFile;
  hasPackageMatching = pattern: builtins.any (n: builtins.match pattern n != null) packageNames;
  brunoPreferences = builtins.fromJSON cfg.xdg.configFile."bruno/preferences.json".text;
in
{
  domain-dev-lazygit-enabled =
    mkEvalCheck "domain-dev-lazygit-enabled" cfg.programs.lazygit.enable
      "lazygit should be enabled";

  domain-dev-bruno-config =
    mkEvalCheck "domain-dev-bruno-config" (hasXdgConfig "bruno/preferences.json")
      "bruno config should be deployed";

  domain-dev-bruno-default-collection-path = mkEvalCheck "domain-dev-bruno-default-collection-path" (
    brunoPreferences.preferences.defaultCollectionPath == "/home/test/vault/bruno-collections"
  ) "bruno default collection path should follow config.home.homeDirectory";

  domain-dev-devenv-package =
    mkEvalCheck "domain-dev-devenv-package" (hasPackageMatching ".*devenv.*")
      "devenv package should be installed";
}
