{
  config,
  lib,
  pkgs,
  ...
}:
let
  gibibyte = 1024 * 1024 * 1024;
  minimumFreeBytes = 40 * gibibyte;
  targetFreeBytes = 80 * gibibyte;
  keptGenerations = 5;
  checkInterval = "15min";
  stateDirectory = "nix-free-space-garbage-collection";
in
{
  nix = {
    gc.automatic = false;
    settings = {
      min-free = minimumFreeBytes;
      max-free = targetFreeBytes;
    };
  };

  systemd.services.nix-free-space-garbage-collection = {
    description = "Prune old Nix generations and collect store garbage when free space runs low";
    path = [ config.nix.package ];
    serviceConfig = {
      Type = "oneshot";
      StateDirectory = stateDirectory;
      Nice = 19;
      IOSchedulingClass = "idle";
      ExecStart = lib.escapeShellArgs [
        "${pkgs.python3}/bin/python3"
        "${./scripts/free_space_garbage_collection.py}"
        "--minimum-free-bytes"
        (toString minimumFreeBytes)
        "--target-free-bytes"
        (toString targetFreeBytes)
        "--kept-generations"
        (toString keptGenerations)
        "--state-file"
        "/var/lib/${stateDirectory}/free-bytes-after-last-collection"
      ];
    };
  };

  systemd.timers.nix-free-space-garbage-collection = {
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnBootSec = "5min";
      OnUnitActiveSec = checkInterval;
    };
  };
}
