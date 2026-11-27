{
  config,
  lib,
  pkgs,
  ...
}:
let
  privateDiskImagePinPath = ../../../../private-configuration/terminal/workspace-manager/rex/rex-disk-image.nix;
  rexApplicationInstaller = ./scripts/ensure_rex_application.py;
in
lib.mkIf (builtins.pathExists privateDiskImagePinPath) (
  let
    diskImagePin = import privateDiskImagePinPath;
    rexDiskImage = pkgs.fetchurl { inherit (diskImagePin) url sha256; };
  in
  {
    system.activationScripts.postActivation.text = ''
      ${pkgs.python312}/bin/python3 ${rexApplicationInstaller} ${diskImagePin.build} ${rexDiskImage} ${config.system.primaryUser} || exit 1
    '';
  }
)
