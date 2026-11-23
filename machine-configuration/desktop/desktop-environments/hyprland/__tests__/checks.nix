{
  helpers,
  pkgs,
  lib,
  self,
  inputs,
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

  cfg = helpers.homeManagerTestConfiguration [
    ../../quickshell/desktop-shell-selection-home-manager.nix
    ../session/graphical-services-activation.nix
  ];

  startGraphicalServicesActivation = cfg.home.activation.startGraphicalServices.data;

  defaultDesktopShellConfiguration = helpers.homeManagerTestConfiguration [
    ../../quickshell/desktop-shell-selection-home-manager.nix
    ../../quickshell/bar/quickshell-bar-home-manager.nix
  ];

  defaultDesktopShellFiles = defaultDesktopShellConfiguration.xdg.configFile;

  impastoDesktopShellConfiguration = helpers.homeManagerTestConfiguration [
    ../../quickshell/desktop-shell-selection-home-manager.nix
    ../../quickshell/bar/quickshell-bar-home-manager.nix
    ../mako.nix
    { custom.desktopShell.active = "impasto"; }
  ];

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
  domain-hyprland-hides-the-avatar-browser =
    mkEvalCheck "domain-hyprland-hides-the-avatar-browser"
      (lib.hasInfix "match:class ^(${inputs.avatar.lib.browserWindowClass})$" (
        builtins.readFile ../program-configuration/conf.d/windows.conf
      ))
      "windows.conf must send the window class the avatar flake exports as lib.browserWindowClass to special:avatar. The avatar's output browser announces that class while it renders for the virtual camera, and without the rule its window opens on the active workspace in front of whatever the user is doing";

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

  domain-hyprland-default-desktop-shell-is-the-quickshell-bar =
    mkEvalCheck "domain-hyprland-default-desktop-shell-is-the-quickshell-bar"
      (
        defaultDesktopShellConfiguration.custom.desktopShell.active == "quickshell-bar"
        &&
          lib.all (binding: lib.hasInfix binding defaultDesktopShellFiles."hypr-shell/bindings.conf".text)
            [
              "bindd = SUPER, J, Toggle left bar, exec, qs -c bar ipc --any-display call -- bar toggle"
              "bindd = SUPER, M, Media dashboard, exec, qs -c bar ipc --any-display call dashboard toggle"
              "bindd = SUPER, Q, Launcher, exec, qs -c bar ipc --any-display call launcher toggle"
              "bindd = SUPER, A, Notifications, exec, qs -c bar ipc --any-display call sidebar toggle"
            ]
        &&
          lib.hasInfix "systemctl --user start quickshell-bar.service mako.service\n"
            defaultDesktopShellFiles."hypr-shell/autostart.conf".text
        && defaultDesktopShellConfiguration.systemd.user.services ? quickshell-bar
      )
      "With the default selection the Hyprland session must keep today's behaviour: the four quickshell bar binds in hypr-shell/bindings.conf and a hypr-shell/autostart.conf that starts quickshell-bar.service and mako.service. Those binds and units left the static conf.d files when the shell became selectable, so losing them here leaves the session without a bar, launcher or notification daemon";

  domain-hyprland-impasto-desktop-shell-replaces-the-quickshell-bar-and-mako =
    mkEvalCheck "domain-hyprland-impasto-desktop-shell-replaces-the-quickshell-bar-and-mako"
      (
        !(impastoDesktopShellConfiguration.systemd.user.services ? quickshell-bar)
        && !(impastoDesktopShellConfiguration.systemd.user.services ? mako)
        && impastoDesktopShellConfiguration.xdg.configFile."hypr-shell/bindings.conf".text == ""
        && impastoDesktopShellConfiguration.xdg.configFile."hypr-shell/autostart.conf".text == ""
      )
      "Selecting impasto must leave exactly one desktop shell: no quickshell bar unit, and no mako unit because the selected shell owns org.freedesktop.Notifications itself. Two shells running together fight over layer-shell surfaces and the notification bus name";

  domain-hyprland-portal-backend-starts-without-waiting-for-the-frontend =
    mkEvalCheck "domain-hyprland-portal-backend-starts-without-waiting-for-the-frontend"
      (
        !(builtins.elem "xdg-desktop-portal.service" chiseSystem.home-manager.users.zanoni.systemd.user.services.xdg-desktop-portal-hyprland.Unit.After)
      )
      "xdg-desktop-portal D-Bus-activates the Hyprland backend while it is still starting. Ordering the backend After the frontend queues that activation behind the frontend's own start job, so every backend interface times out at 25 seconds, the frontend hangs for minutes and the Hyprland portal never starts when graphical-session.target pulls both at login";
}
