{
  helpers,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [ ../fuzzel-home-manager.nix ];
in
{
  domain-desktop-fuzzel-enabled =
    mkEvalCheck "domain-desktop-fuzzel-enabled" cfg.programs.fuzzel.enable
      "fuzzel launcher should be enabled";
}
