{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [ ../graphical-services-activation.nix ];

  startGraphicalServicesActivation = cfg.home.activation.startGraphicalServices.data;

  commandPackagesConfiguration = helpers.homeManagerTestConfiguration [
    ../hyprland-command-packages-home-manager.nix
  ];

  summonChromeGlobalPackage = lib.head (
    lib.filter (
      package: (lib.getName package) == "hypr-summon-chrome-global"
    ) commandPackagesConfiguration.home.packages
  );
in
{
  domain-hyprland-graphical-service-restart-is-time-bounded =
    mkEvalCheck "domain-hyprland-graphical-service-restart-is-time-bounded"
      (lib.hasInfix "/bin/timeout " startGraphicalServicesActivation)
      "The graphical service restart must run under a timeout. `systemctl --user restart` is a round trip to the user systemd manager, and an unresponsive manager makes the call BLOCK rather than fail, which wedges the switch with the new home generation already linked and the system profile still on the old one. The entry only runs when Hyprland is live, so the compositor is by construction busy whenever it fires";

  domain-hyprland-graphical-service-restart-tolerates-its-own-failure =
    mkEvalCheck "domain-hyprland-graphical-service-restart-tolerates-its-own-failure"
      (lib.hasInfix "|| true" startGraphicalServicesActivation)
      "The graphical service restart must end in `|| true`. Restarting mako, the hyprland portal and the focus daemon is a best-effort desktop nicety: nothing downstream in the activation consumes it and the machine keeps running without it, since a failed restart leaves the already-running instance in place. This check guards a DIFFERENT failure mode from the timeout check above and neither substitutes for the other: `timeout` bounds a hang, `|| true` absorbs a non-zero exit under set -e, and a wedged systemd manager hangs rather than exits";

  domain-hyprland-summon-chrome-global-uses-hardware-video-decoding-workaround =
    mkEvalCheck "domain-hyprland-summon-chrome-global-uses-hardware-video-decoding-workaround"
      (lib.hasInfix "google-chrome-without-broken-hardware-video-decoding" summonChromeGlobalPackage.text)
      "hypr-summon-chrome-global prepends its own Chrome to PATH before exec'ing google-chrome-stable, so it must point at the wrapped Chrome. Pointing it at latest.google-chrome instead shadows the wrapper for the launcher that actually starts the everyday browser, and HEVC playback silently breaks again while the desktop entry looks correctly configured";
}
