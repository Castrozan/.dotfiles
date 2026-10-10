{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;
  evaluate =
    enabled:
    (lib.evalModules {
      specialArgs = {
        inherit pkgs;
        username = "test-user";
      };
      modules = [
        ../arr-download-cleanup-nixos.nix
        {
          options.systemd = lib.mkOption {
            type = lib.types.attrs;
            default = { };
          };
          options.networking = lib.mkOption {
            type = lib.types.attrs;
            default = { };
          };
          config.custom.arrDownloadCleanup = {
            enable = enabled;
            stackHomeDirectory = "/home/test-user/arr-stack";
            qbittorrentPasswordSecretFile = "/run/agenix/qbittorrent";
            jellyfinApiKeySecretFile = "/run/agenix/jellyfin";
          };
        }
      ];
    }).config;
  disabled = evaluate false;
  enabled = evaluate true;
  service = enabled.systemd.services.arr-download-cleanup;
  connection =
    app:
    builtins.head (
      builtins.fromJSON (builtins.readFile (../../desired-state + "/${app}/notification.json"))
    );
in
{
  arr-download-cleanup-disabled = mkEvalCheck "arr-download-cleanup-disabled" (
    !(disabled.systemd.services ? arr-download-cleanup)
  ) "Hosts that do not enable download cleanup must get no service.";
  arr-download-cleanup-is-durable-and-restricted =
    mkEvalCheck "arr-download-cleanup-is-durable-and-restricted"
      (
        service.serviceConfig.StateDirectory == "arr-download-cleanup"
        && service.serviceConfig.ProtectSystem == "strict"
        && service.serviceConfig.User == "test-user"
        && builtins.length service.serviceConfig.LoadCredential == 2
        && service.unitConfig.RequiresMountsFor == [ "/home/test-user/arr-stack/data" ]
        && lib.hasSuffix "bootstrap" service.serviceConfig.ExecStartPre
      )
      "Cleanup must bootstrap persistent state, run without root, and depend on its data drive.";
  arr-download-cleanup-hooks-track-grabs-and-title-deletions =
    mkEvalCheck "arr-download-cleanup-hooks-track-grabs-and-title-deletions"
      (
        (connection "radarr").onGrab
        && (connection "radarr").onMovieDelete
        && !(connection "radarr").onMovieFileDelete
        && (connection "sonarr").onGrab
        && (connection "sonarr").onSeriesDelete
        && !(connection "sonarr").onEpisodeFileDelete
      )
      "Native hooks must record exact download identities and exclude file upgrades from whole-title cleanup.";
}
