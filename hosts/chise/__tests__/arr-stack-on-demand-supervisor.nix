{
  pkgs,
  lib,
}:
let
  helpers = import ../../../__tests__/nix-checks/helpers.nix {
    inherit pkgs lib;
    inputs = { };
    nixpkgs-version = "25.11";
    home-version = "25.11";
  };
  inherit (helpers) mkEvalCheck;

  evalSupervisor =
    settings:
    (lib.evalModules {
      specialArgs = { inherit pkgs; };
      modules = [
        ../../../nixos/modules/arr-stack-on-demand-supervisor
        {
          options.systemd = lib.mkOption {
            type = lib.types.attrs;
            default = { };
          };
          config.custom.arrStackOnDemandSupervisor = settings;
        }
      ];
    }).config;

  supervisorDisabled = evalSupervisor {
    enable = false;
    stackHomeDirectory = "/home/zanoni/arr-stack";
  };

  supervisorEnabled = evalSupervisor {
    enable = true;
    stackHomeDirectory = "/home/zanoni/arr-stack";
  };

  enabledService = supervisorEnabled.systemd.services.arr-stack-on-demand-supervisor;
  enabledTimer = supervisorEnabled.systemd.timers.arr-stack-on-demand-supervisor;
  enabledEnvironment = enabledService.environment;
in
{
  chise-arr-on-demand-disabled-defines-no-service =
    mkEvalCheck "chise-arr-on-demand-disabled-defines-no-service"
      (!(supervisorDisabled.systemd.services or { } ? arr-stack-on-demand-supervisor))
      "a host that does not opt in must get no supervisor service, so the download chain lifecycle stays fully manual where the module is off";

  chise-arr-on-demand-is-oneshot-with-state-directory =
    mkEvalCheck "chise-arr-on-demand-is-oneshot-with-state-directory"
      (
        enabledService.serviceConfig.Type == "oneshot"
        && enabledService.serviceConfig.StateDirectory == "arr-stack-on-demand-supervisor"
      )
      "the supervisor must be a oneshot with a persistent StateDirectory so each timer tick runs to completion and the idle baseline survives across ticks to make the grace period meaningful";

  chise-arr-on-demand-timer-polls-periodically =
    mkEvalCheck "chise-arr-on-demand-timer-polls-periodically"
      (
        builtins.elem "timers.target" enabledTimer.wantedBy
        && (enabledTimer.timerConfig.OnUnitActiveSec or "") != ""
        && enabledTimer.timerConfig.Unit == "arr-stack-on-demand-supervisor.service"
      )
      "the timer must be wanted by timers.target and re-fire on an active interval, or demand and idle state would never be re-evaluated and the chain would never come up or go down on its own";

  chise-arr-on-demand-runs-the-packaged-supervisor =
    mkEvalCheck "chise-arr-on-demand-runs-the-packaged-supervisor"
      (lib.hasInfix "on_demand_supervisor" enabledService.serviceConfig.ExecStart)
      "the service must launch the packaged supervisor directory so python resolves the __main__ entry with its sibling modules on the same store path";

  chise-arr-on-demand-never-stops-the-front-ends =
    mkEvalCheck "chise-arr-on-demand-never-stops-the-front-ends"
      (
        !(lib.hasInfix "jellyfin" enabledEnvironment.ARR_ON_DEMAND_SERVICES)
        && !(lib.hasInfix "jellyseerr" enabledEnvironment.ARR_ON_DEMAND_SERVICES)
      )
      "the on-demand service set must exclude jellyfin and jellyseerr so the always-on public front ends behind the funnel are never stopped by the idle sweep, only the download chain is";

  chise-arr-on-demand-chain-is-movie-and-tv-only =
    mkEvalCheck "chise-arr-on-demand-chain-is-movie-and-tv-only"
      (
        lib.hasInfix "radarr" enabledEnvironment.ARR_ON_DEMAND_SERVICES
        && lib.hasInfix "sonarr" enabledEnvironment.ARR_ON_DEMAND_SERVICES
        && !(lib.hasInfix "lidarr" enabledEnvironment.ARR_ON_DEMAND_SERVICES)
        && !(lib.hasInfix "readarr" enabledEnvironment.ARR_ON_DEMAND_SERVICES)
      )
      "the chain must cover radarr and sonarr since Jellyseerr requests are movie and TV only, and leave the never-requested lidarr and readarr down";

  chise-arr-on-demand-keeps-tailnet-ip-out-of-source =
    mkEvalCheck "chise-arr-on-demand-keeps-tailnet-ip-out-of-source"
      (
        enabledEnvironment.ARR_BIND_ADDRESS_KEY == "ARR_BIND_ADDR"
        && lib.hasInfix "127.0.0.1" enabledEnvironment.JELLYSEERR_URL
        && !(enabledEnvironment ? RADARR_URL)
        && !(enabledEnvironment ? SONARR_URL)
        && !(lib.hasInfix "http://" (
          builtins.toJSON (builtins.removeAttrs enabledEnvironment [ "JELLYSEERR_URL" ])
        ))
      )
      "the supervisor must learn the tailnet bind address from the build-generated .env at runtime and hold no radarr/sonarr URL literal, so the tailscale IP never enters the public nix source";

  chise-arr-on-demand-drives-compose-standalone =
    mkEvalCheck "chise-arr-on-demand-drives-compose-standalone"
      (
        lib.hasInfix "docker-compose" enabledEnvironment.DOCKER_COMPOSE_BIN
        && enabledEnvironment.ARR_COMPOSE_PROJECT == "arr-stack"
      )
      "the supervisor must drive the standalone docker-compose binary against the arr-stack project so bringing the chain up and down targets the same containers the stack already declares";

  chise-arr-on-demand-disk-guard-stops-fill-below-critical-floor =
    mkEvalCheck "chise-arr-on-demand-disk-guard-stops-fill-below-critical-floor"
      (
        enabledEnvironment.ARR_DISK_GUARD_FILL_SERVICE == "qbittorrent"
        && lib.elem enabledEnvironment.ARR_DISK_GUARD_FILL_SERVICE (
          lib.splitString " " enabledEnvironment.ARR_ON_DEMAND_SERVICES
        )
        &&
          (lib.toInt enabledEnvironment.ARR_DISK_GUARD_CRITICAL_GIGABYTES)
          < (lib.toInt enabledEnvironment.ARR_DISK_GUARD_WARNING_GIGABYTES)
        && lib.hasInfix "arr-stack" enabledEnvironment.ARR_DISK_GUARD_PATH
      )
      "the disk guard must stop the download client, which must itself be an on-demand service so the guard can hold it out of the keep-alive restart, once free space on the shared stack filesystem falls below a critical floor that sits under the warning floor, so a single large grab can never fill root to zero and brick the host";
}
