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

  chiseSessionServicesNotStoppedWithTheSession = lib.attrNames (
    lib.filterAttrs (
      _: service:
      builtins.elem "graphical-session.target" (service.Install.WantedBy or [ ])
      && !(builtins.elem "graphical-session.target" (service.Unit.PartOf or [ ]))
    ) chiseSystem.home-manager.users.zanoni.systemd.user.services
  );

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
        && chiseSystem.services.greetd.enable
        && !chiseSystem.services.displayManager.gdm.enable
        && lib.hasInfix "/bin/uwsm start -F -- /nix/store/" chiseSystem.services.greetd.settings.default_session.command
        && lib.hasInfix "/bin/start-hyprland" chiseSystem.services.greetd.settings.default_session.command
        && chiseSystem.security.pam.services.greetd.enableGnomeKeyring
      )
      "chise must log in through greetd straight into Hyprland under uwsm, by absolute path. Without uwsm nothing activates graphical-session.target or clears WAYLAND_DISPLAY from the user manager when the compositor exits, so every unit gated on that variable keeps starting into a dead compositor and xdg-desktop-portal-hyprland restart-loops until the next login. GDM brought a GNOME greeter that idle-suspended the machine and rejected the uwsm entry Hyprland ships, whose bare `uwsm` TryExec it resolves on a PATH that lacks it. The greetd PAM stack must unlock the login keyring the session's secret service relies on";

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

  domain-hyprland-login-prompt-owns-its-console =
    mkEvalCheck "domain-hyprland-login-prompt-owns-its-console"
      (
        chiseSystem.boot.consoleLogLevel <= 3
        && builtins.elem "systemd.show_status=error" chiseSystem.boot.kernelParams
        && chiseSystem.systemd.services.greetd.serviceConfig.StandardError == "journal"
      )
      "tuigreet draws on the same virtual terminal the kernel and systemd print boot status to, and the arr-stack provisioners finish minutes into the boot, so their status lines land on top of the login prompt and garble it. Only errors may reach that console, and greetd's own stderr belongs in the journal";

  domain-hyprland-session-services-stop-with-the-session =
    mkEvalCheck "domain-hyprland-session-services-stop-with-the-session"
      (chiseSessionServicesNotStoppedWithTheSession == [ ])
      "Every user service wanted by graphical-session.target must also be PartOf it, so `uwsm stop` and compositor crashes stop it with the session. Otherwise it outlives Hyprland, crashes on the vanished Wayland socket and Restart= loops it into a failed unit, because automatic restarts skip ConditionEnvironment. Offending services: ${toString chiseSessionServicesNotStoppedWithTheSession}";

  domain-hyprland-portal-backend-starts-without-waiting-for-the-frontend =
    mkEvalCheck "domain-hyprland-portal-backend-starts-without-waiting-for-the-frontend"
      (
        !(builtins.elem "xdg-desktop-portal.service" chiseSystem.home-manager.users.zanoni.systemd.user.services.xdg-desktop-portal-hyprland.Unit.After)
      )
      "xdg-desktop-portal D-Bus-activates the Hyprland backend while it is still starting. Ordering the backend After the frontend queues that activation behind the frontend's own start job, so every backend interface times out at 25 seconds, the frontend hangs for minutes and the Hyprland portal never starts when graphical-session.target pulls both at login";
}
