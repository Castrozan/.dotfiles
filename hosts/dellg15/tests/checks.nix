{
  pkgs,
  lib,
  self,
  ...
}:
let
  helpers = import ../../../tests/nix-checks/helpers.nix {
    inherit pkgs lib;
    inputs = { };
    nixpkgs-version = "25.11";
    home-version = "25.11";
  };
  inherit (helpers) mkEvalCheck;

  nixosCfg = self.nixosConfigurations.zanoni.config;
in
{
  dellg15-nix-daemon-max-jobs = mkEvalCheck "dellg15-nix-daemon-max-jobs" (
    nixosCfg.nix.settings.max-jobs <= 6
  ) "max-jobs must be <= 6 to prevent memory saturation on 16GB RAM";

  dellg15-nix-daemon-cores = mkEvalCheck "dellg15-nix-daemon-cores" (
    nixosCfg.nix.settings.cores > 0 && nixosCfg.nix.settings.cores <= 2
  ) "cores must be 1-2 to leave CPU headroom for interactive processes";

  dellg15-nix-daemon-cpu-sched-policy = mkEvalCheck "dellg15-nix-daemon-cpu-sched-policy" (
    nixosCfg.nix.daemonCPUSchedPolicy == "batch"
  ) "nix-daemon must use batch CPU scheduling for background throughput";

  dellg15-nix-daemon-io-sched-class = mkEvalCheck "dellg15-nix-daemon-io-sched-class" (
    nixosCfg.nix.daemonIOSchedClass == "idle"
  ) "nix-daemon must use idle IO scheduling to avoid starving interactive IO";

  dellg15-nix-daemon-nice = mkEvalCheck "dellg15-nix-daemon-nice" (
    nixosCfg.systemd.services.nix-daemon.serviceConfig.Nice == 19
  ) "nix-daemon must run at Nice=19 (lowest CPU priority)";

  dellg15-earlyoom-enabled =
    mkEvalCheck "dellg15-earlyoom-enabled" nixosCfg.services.earlyoom.enable
      "earlyoom must be enabled to prevent kernel OOM freezes";

  dellg15-zram-enabled =
    mkEvalCheck "dellg15-zram-enabled" nixosCfg.zramSwap.enable
      "zram swap must be enabled for compressed in-memory swap";

  dellg15-keyboard-backlight-service-enabled =
    mkEvalCheck "dellg15-keyboard-backlight-service-enabled"
      (nixosCfg.systemd.services.dim-keyboard-backlight.enable or true)
      "dim-keyboard-backlight service must be defined";

  dellg15-keyboard-backlight-service-oneshot =
    mkEvalCheck "dellg15-keyboard-backlight-service-oneshot"
      (nixosCfg.systemd.services.dim-keyboard-backlight.serviceConfig.Type == "oneshot")
      "dim-keyboard-backlight must be a oneshot service";

  dellg15-keyboard-backlight-service-remain-after-exit =
    mkEvalCheck "dellg15-keyboard-backlight-service-remain-after-exit"
      nixosCfg.systemd.services.dim-keyboard-backlight.serviceConfig.RemainAfterExit
      "dim-keyboard-backlight must remain after exit";

  dellg15-keyboard-backlight-scripts-installed =
    mkEvalCheck "dellg15-keyboard-backlight-scripts-installed"
      (
        let
          packageNames = map (p: p.name or "") nixosCfg.environment.systemPackages;
          hasScript = name: builtins.any (n: lib.hasPrefix name n) packageNames;
        in
        hasScript "set-keyboard-backlight-brightness"
        && hasScript "set-keyboard-backlight-color"
        && hasScript "reset-keyboard-backlight"
      )
      "all three keyboard backlight scripts must be in system packages";
}
