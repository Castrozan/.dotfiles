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
    ../dconf.nix
    ../gtk.nix
  ];
in
{
  domain-gnome-gtk-enabled =
    mkEvalCheck "domain-gnome-gtk-enabled" cfg.gtk.enable
      "gtk theming should be enabled";

  domain-gnome-dconf-settings =
    mkEvalCheck "domain-gnome-dconf-settings"
      (builtins.hasAttr "org/gnome/desktop/interface" cfg.dconf.settings)
      "dconf settings should be configured";
}
