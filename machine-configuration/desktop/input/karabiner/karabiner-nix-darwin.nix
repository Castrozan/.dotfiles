{
  config,
  lib,
  pkgs,
  ...
}:
let
  minimumKarabinerVersion = "16.3.0";
  karabinerVersionInstaller = pkgs.writeText "ensure_karabiner_version.py" (
    builtins.replaceStrings
      [
        ''"@MINIMUM_KARABINER_VERSION@"''
        ''"@HOMEBREW_BINARY@"''
        ''"@HOMEBREW_USER@"''
      ]
      (map builtins.toJSON [
        minimumKarabinerVersion
        "${config.homebrew.brewPrefix}/brew"
        config.homebrew.user
      ])
      (builtins.readFile ./scripts/ensure_karabiner_version.py)
  );
in
{
  homebrew.casks = [ "karabiner-elements" ];

  system.activationScripts.preActivation.text = lib.mkBefore ''
    ${pkgs.python312}/bin/python3 ${karabinerVersionInstaller} || exit 1
  '';
}
