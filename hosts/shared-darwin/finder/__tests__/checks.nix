{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  finderConfig = import ../default.nix;
  finderCustomPreferences = finderConfig.system.defaults.CustomUserPreferences."com.apple.finder";
in
{
  macbook-finder-create-desktop-disabled = mkEvalCheck "macbook-finder-create-desktop-disabled" (
    !finderCustomPreferences.CreateDesktop
  ) "Finder CreateDesktop must be disabled to prevent Finder from managing the desktop layer";
}
