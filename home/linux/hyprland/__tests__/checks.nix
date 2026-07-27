{
  pkgs,
  lib,
  inputs,
  nixpkgs-version,
  home-version,
}:
let
  helpers = import ../../../../__tests__/nix-checks/helpers.nix {
    inherit
      pkgs
      lib
      inputs
      nixpkgs-version
      home-version
      ;
  };
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [ ../graphical-services-activation.nix ];

  startGraphicalServicesActivation = cfg.home.activation.startGraphicalServices.data;
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
}
