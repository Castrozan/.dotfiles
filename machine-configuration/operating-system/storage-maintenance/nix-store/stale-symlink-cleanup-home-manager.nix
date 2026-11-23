{
  config,
  lib,
  pkgs,
  ...
}:

let
  homeDir = config.home.homeDirectory;
  configurationDirectory = "${homeDir}/.config";
  scanSecondsPerDirectory = 20;

  directoriesToScan = [
    configurationDirectory
    "${homeDir}/.claude"
    "${homeDir}/.local"
    "${homeDir}/.codex"
  ];

  removeStaleNixStoreSymlinks = pkgs.writeShellApplication {
    name = "remove-stale-nix-store-symlinks";
    runtimeInputs = [
      pkgs.coreutils
      pkgs.findutils
      pkgs.gnused
    ];
    text = builtins.readFile ./scripts/remove-stale-nix-store-symlinks.sh;
  };
in
{
  home.activation.removeStaleNixStoreSymlinks = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    ${removeStaleNixStoreSymlinks}/bin/remove-stale-nix-store-symlinks \
      ${toString scanSecondsPerDirectory} ${
        lib.escapeShellArgs ([ configurationDirectory ] ++ directoriesToScan)
      }
  '';
}
