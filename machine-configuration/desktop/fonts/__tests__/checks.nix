{
  helpers,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [ ../fonts-home-manager.nix ];
in
{
  domain-desktop-fontconfig-enabled =
    mkEvalCheck "domain-desktop-fontconfig-enabled" cfg.fonts.fontconfig.enable
      "fontconfig should be enabled";
}
