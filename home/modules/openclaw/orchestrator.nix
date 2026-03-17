{ lib, ... }:
{
  imports = [
    ./config-options.nix
    ./config-engine.nix
    ./config-declarations.nix
    ./workspace-dirs.nix
    ./install.nix
    ./systemd-service.nix
    ./reliability/health-check.nix
    ./reliability/scheduled-backup.nix
    ./reliability/restart-watcher/restart-watcher.nix
    ./reliability/timeout-recovery.nix
    ./reliability/restart-watcher/ensure-services-after-rebuild.nix
    ./plugins/memory-sync.nix
    ./plugins/plugins.nix
    (
      { pkgs, ... }:
      {
        config.assertions = [
          {
            assertion = !pkgs.stdenv.isDarwin;
            message = "OpenClaw module must not be imported on macOS/Darwin. Remove the openclaw import from the darwin home configuration.";
          }
        ];
      }
    )
  ];

  _module.args.isNixOS = lib.mkDefault false;
}
