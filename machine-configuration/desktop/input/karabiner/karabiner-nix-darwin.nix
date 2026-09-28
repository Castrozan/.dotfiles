{
  config,
  lib,
  pkgs,
  ...
}:
let
  minimumKarabinerVersion = "16.3.0";
in
{
  homebrew.casks = [ "karabiner-elements" ];

  system.activationScripts.preActivation.text = lib.mkBefore ''
    ${pkgs.python312}/bin/python3 ${./scripts/ensure_karabiner_version.py} \
      --minimum-version ${lib.escapeShellArg minimumKarabinerVersion} \
      --homebrew-binary ${lib.escapeShellArg "${config.homebrew.brewPrefix}/brew"} \
      --homebrew-user ${lib.escapeShellArg config.homebrew.user} || exit 1
  '';
}
