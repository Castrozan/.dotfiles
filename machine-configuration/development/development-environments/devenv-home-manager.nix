{
  config,
  lib,
  pkgs,
  inputs,
  hostname,
  ...
}:
{
  home.packages = [
    inputs.devenv.packages.${pkgs.stdenv.hostPlatform.system}.devenv
  ];

  home.activation.removeDevelopmentContainerPilot = lib.mkIf (hostname == "rin") (
    lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      pilot_path="${config.home.homeDirectory}/repo/shell/devenv.local.nix"
      if [ -f "$pilot_path" ]; then
        pilot_checksum="$(${pkgs.coreutils}/bin/sha256sum "$pilot_path" | ${pkgs.coreutils}/bin/cut -d ' ' -f 1)"
        if [ "$pilot_checksum" = "3b781ecb597d0f0d70a4e97387dc3cadb933e1a611fe6c50c10c284860da93d4" ]; then
          run ${pkgs.coreutils}/bin/rm "$pilot_path"
        fi
      fi
    ''
  );
}
