{
  lib,
  pkgs,
  ...
}:
let
  inherit (pkgs.stdenv.hostPlatform) isLinux;
in
{
  home.sessionVariables = lib.mkIf isLinux {
    MOZ_DISABLE_RDD_SANDBOX = "1";
  };

  programs.firefox = {
    enable = true;

    policies = import ./browser-policies.nix;

    profiles.default = {
      isDefault = true;

      settings = import ./default-profile-preferences.nix;

      search = import ./search-engines.nix;
    };
  };
}
