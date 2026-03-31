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

  hasService = name: builtins.hasAttr name cfg.systemd.user.services;

  wireplumberLocaleDropinPath = "systemd/user/wireplumber.service.d/force-c-locale-for-ascii-safe-device-descriptions.conf";
  wireplumberLocaleDropinExists = builtins.hasAttr wireplumberLocaleDropinPath cfg.xdg.configFile;
  wireplumberLocaleDropinContainsLangC =
    wireplumberLocaleDropinExists
    && builtins.match ".*LANG=C.*" cfg.xdg.configFile.${wireplumberLocaleDropinPath}.text != null;
in
{
  domain-audio-bluetooth-service =
    mkEvalCheck "domain-audio-bluetooth-service" (hasService "bluetooth-audio-autoswitch")
      "bluetooth audio autoswitch service should exist";

  domain-audio-wireplumber-locale-dropin =
    mkEvalCheck "domain-audio-wireplumber-locale-dropin" wireplumberLocaleDropinContainsLangC
      "WirePlumber systemd drop-in must set LANG=C to prevent non-ASCII device descriptions that break pactl JSON output";
}
