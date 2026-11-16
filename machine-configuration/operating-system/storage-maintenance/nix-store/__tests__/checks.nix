{
  helpers,
  lib,
  self,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [
    ../stale-symlink-cleanup-home-manager.nix
  ];

  hasActivation = name: builtins.hasAttr name cfg.home.activation;

  chiseConfiguration = self.nixosConfigurations.chise.config;
  freeSpaceService = chiseConfiguration.systemd.services.nix-free-space-garbage-collection;
  freeSpaceTimer = chiseConfiguration.systemd.timers.nix-free-space-garbage-collection;
  minimumFreeBytes = chiseConfiguration.nix.settings.min-free;
  targetFreeBytes = chiseConfiguration.nix.settings.max-free;
  serviceStart = freeSpaceService.serviceConfig.ExecStart;
in
{
  domain-system-stale-symlink-cleanup =
    mkEvalCheck "domain-system-stale-symlink-cleanup" (hasActivation "removeStaleNixStoreSymlinks")
      "stale nix store symlink cleanup activation should exist";

  domain-system-nix-free-space-gc-replaces-calendar-gc =
    mkEvalCheck "domain-system-nix-free-space-gc-replaces-calendar-gc"
      (!chiseConfiguration.nix.gc.automatic && !(freeSpaceTimer.timerConfig ? OnCalendar))
      "nix garbage collection on chise must be triggered by free disk space, never by a calendar date";

  domain-system-nix-free-space-gc-daemon-thresholds =
    mkEvalCheck "domain-system-nix-free-space-gc-daemon-thresholds"
      (minimumFreeBytes > 0 && targetFreeBytes > minimumFreeBytes)
      "nix daemon min-free must be set and max-free must exceed it so builds collect garbage under disk pressure";

  domain-system-nix-free-space-gc-shares-daemon-thresholds =
    mkEvalCheck "domain-system-nix-free-space-gc-shares-daemon-thresholds"
      (
        lib.hasInfix "--minimum-free-bytes ${toString minimumFreeBytes}" serviceStart
        && lib.hasInfix "--target-free-bytes ${toString targetFreeBytes}" serviceStart
      )
      "the free space check must use the same thresholds as the nix daemon min-free and max-free";

  domain-system-nix-free-space-gc-keeps-rollback-generations =
    mkEvalCheck "domain-system-nix-free-space-gc-keeps-rollback-generations"
      (lib.hasInfix "--kept-generations 5" serviceStart)
      "the free space collection must keep the newest generations of every profile so rollback stays possible";

  domain-system-nix-free-space-gc-polls-while-idle =
    mkEvalCheck "domain-system-nix-free-space-gc-polls-while-idle"
      (
        builtins.elem "timers.target" freeSpaceTimer.wantedBy
        && freeSpaceTimer.timerConfig ? OnUnitActiveSec
      )
      "the free space check must run periodically so collection also happens when no build runs";
}
