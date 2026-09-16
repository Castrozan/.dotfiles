{
  pkgs,
  ...
}:
{
  home.sessionVariables = {
    MOZ_DISABLE_RDD_SANDBOX = "1";
  };

  programs.firefox = {
    enable = true;
    package = pkgs.firefox;

    policies = import ./browser-policies.nix;

    profiles.default = {
      isDefault = true;

      settings = import ./default-profile-preferences.nix;

      search = import ./search-engines.nix;
    };
  };
}
