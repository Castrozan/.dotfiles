{
  config,
  lib,
  pkgs,
  hostname,
  ...
}:
{
  home.activation.seedDevelopmentContainerPilot = lib.mkIf (hostname == "rin") (
    lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      if [ -f "${config.home.homeDirectory}/repo/shell/devenv.nix" ]; then
        ${pkgs.coreutils}/bin/install -m 0644 ${./project-pilot.nix} "${config.home.homeDirectory}/repo/shell/devenv.local.nix"
      fi
    ''
  );
}
