{
  config,
  lib,
  pkgs,
  ...
}:
let
  healthCheckLib = import ./health-check-probe-library.nix { inherit lib; };

  probeSubmodule = lib.types.submodule {
    options = {
      category = lib.mkOption {
        type = lib.types.enum [
          "bin"
          "app"
          "config"
          "daemon"
          "secret"
          "auth"
          "nix"
          "misc"
        ];
        description = "Probe category for --category filtering.";
      };
      name = lib.mkOption {
        type = lib.types.str;
        description = "Human-readable probe label.";
      };
      probe = lib.mkOption {
        type = lib.types.lines;
        description = "Bash snippet that exits 0 on success. Build via healthCheckLib helpers; do not write raw shell at the call site.";
      };
      applicableWhen = lib.mkOption {
        type = lib.types.nullOr lib.types.lines;
        default = null;
        description = "Bash snippet deciding whether the probe applies right now. Exit 0 runs the probe; any non-zero exit skips it and its stdout is shown as the reason. Use for components that are dormant by design outside their schedule, so their absence never reads as a failure.";
      };
    };
  };

  healthCheckScript = import ./health-check-script.nix {
    inherit pkgs lib;
    inherit (config.healthCheck) probes;
  };
in
{
  options.healthCheck.probes = lib.mkOption {
    type = lib.types.listOf probeSubmodule;
    default = [ ];
    description = "Liveness probes. Each module appends its own via healthCheckLib helpers.";
  };

  config = {
    _module.args.healthCheckLib = healthCheckLib;
    home.packages = [ healthCheckScript ];
  };
}
