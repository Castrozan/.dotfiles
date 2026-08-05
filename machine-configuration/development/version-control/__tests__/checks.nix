{
  helpers,
  ...
}:
let
  inherit (helpers) mkEvalCheck;
  configuration = helpers.homeManagerTestConfiguration [ ../lazygit-home-manager.nix ];
in
{
  domain-dev-lazygit-enabled =
    mkEvalCheck "domain-dev-lazygit-enabled" configuration.programs.lazygit.enable
      "lazygit should be enabled";
}
