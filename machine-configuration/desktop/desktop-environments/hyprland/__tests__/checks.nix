{
  helpers,
  pkgs,
  lib,
  self,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  chiseSystem = self.nixosConfigurations.chise.config;

  wlogoutConfiguration = helpers.homeManagerTestConfiguration [ ../session/wlogout.nix ];

  wlogoutLogoutAction =
    (lib.findFirst (entry: entry.label == "logout") null wlogoutConfiguration.programs.wlogout.layout)
    .action;

  cfg = helpers.homeManagerTestConfiguration [ ../session/graphical-services-activation.nix ];

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

  domain-hyprland-session-is-managed-by-uwsm =
    mkEvalCheck "domain-hyprland-session-is-managed-by-uwsm"
      (
        chiseSystem.programs.hyprland.withUWSM
        && chiseSystem.programs.uwsm.enable
        && chiseSystem.services.displayManager.defaultSession == "hyprland-session-uwsm"
        && lib.hasPrefix "/nix/store/" chiseSystem.programs.uwsm.waylandCompositors.hyprland-session.binPath
      )
      "chise must launch Hyprland through uwsm by default, from the session entry the NixOS uwsm module writes with absolute paths. Without uwsm nothing activates graphical-session.target or clears WAYLAND_DISPLAY from the user manager when the compositor exits, so every unit gated on that variable keeps starting into a dead compositor and xdg-desktop-portal-hyprland restart-loops until the next login. The entry Hyprland ships instead resolves a bare `uwsm` through TryExec on the GDM daemon PATH, which lacks it, so GDM drops the login as never registered";

  domain-hyprland-logout-stops-the-uwsm-session =
    mkEvalCheck "domain-hyprland-logout-stops-the-uwsm-session"
      (
        lib.hasInfix "uwsm check is-active" wlogoutLogoutAction
        && lib.hasInfix "uwsm stop" wlogoutLogoutAction
      )
      "Logout must call `uwsm stop` when the session is uwsm-managed. The Hyprland exit dispatcher pulls the compositor out from under its clients and skips the ordered unit shutdown that clears the session environment; it stays only as the fallback for sessions started without uwsm";

  domain-hyprland-is-the-only-desktop-session =
    mkEvalCheck "domain-hyprland-is-the-only-desktop-session"
      (
        !chiseSystem.services.desktopManager.gnome.enable
        && chiseSystem.services.gnome.gnome-keyring.enable
        && chiseSystem.services.upower.enable
        && chiseSystem.security.polkit.enable
      )
      "chise runs only Hyprland. With the GNOME desktop enabled GDM falls back to the GNOME session whenever the uwsm entry is unavailable, landing the login in a desktop nothing here is configured for. The keyring, UPower and polkit that GNOME used to pull in stay enabled on their own because the Hyprland session unlocks the login keyring, the quickshell battery reads UPower and the polkit agent needs polkit";
}
