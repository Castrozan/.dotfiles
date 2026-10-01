{
  lib,
  pkgs,
  ...
}:
let
  minimumKarabinerVersion = "16.3.0";
  karabinerInstallerPackage =
    pkgs.runCommand "karabiner-elements-installer-${minimumKarabinerVersion}"
      {
        nativeBuildInputs = [ pkgs.undmg ];
        src = pkgs.fetchurl {
          url = "https://github.com/pqrs-org/Karabiner-Elements/releases/download/v${minimumKarabinerVersion}/Karabiner-Elements-${minimumKarabinerVersion}.dmg";
          sha256 = "19cce7bed3d48a722242ca683bd1bae406b6a87fed520728d1c91dee175b75e4";
        };
      }
      ''
        undmg "$src"
        mkdir -p "$out"
        cp Karabiner-Elements.pkg "$out/"
      '';
  karabinerVersionInstaller = pkgs.writeText "ensure_karabiner_version.py" (
    builtins.replaceStrings
      [
        ''"@MINIMUM_KARABINER_VERSION@"''
        ''"@KARABINER_INSTALLER_PACKAGE@"''
      ]
      (map builtins.toJSON [
        minimumKarabinerVersion
        "${karabinerInstallerPackage}/Karabiner-Elements.pkg"
      ])
      (builtins.readFile ./scripts/ensure_karabiner_version.py)
  );
in
{
  system.activationScripts.preActivation.text = lib.mkBefore ''
    ${pkgs.python312}/bin/python3 ${karabinerVersionInstaller} || exit 1
  '';
}
