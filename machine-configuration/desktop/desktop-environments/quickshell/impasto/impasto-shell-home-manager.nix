{
  config,
  lib,
  pkgs,
  inputs,
  ...
}:
let
  impastoShellPackage = inputs.impasto.packages.${pkgs.stdenv.hostPlatform.system}.impasto-shell;
  inherit (impastoShellPackage) quickshellConfigurationName;

  firstRunSettings = pkgs.writeText "impasto-first-run-settings.json" (
    builtins.toJSON (
      {
        barAutohide = true;
        dockAutohide = true;
        themeTargets = [ ];
        shakeToFind = false;
        barRight = [
          "tray"
          "stats"
          "vpn"
          "keyboardlight"
          "notifications"
          "network"
          "bluetooth"
          "volume"
          "battery"
        ];
      }
      // config.custom.desktopShell.impastoFirstRunSettings
    )
  );

  callImpastoCommand =
    target: function:
    "${impastoShellPackage}/bin/impasto-shell ipc --any-display call ${target} ${function}";
in
{
  options.custom.desktopShell.impastoFirstRunSettings = lib.mkOption {
    type = lib.types.attrsOf lib.types.anything;
    default = { };
    description = "Machine-specific Impasto settings merged into the file seeded on its first run.";
  };

  config = lib.mkIf (config.custom.desktopShell.active == "impasto") {
    home.packages = [
      impastoShellPackage
      pkgs.inter
      pkgs.whitesur-icon-theme
    ];

    xdg.configFile."quickshell/${quickshellConfigurationName}".source =
      "${impastoShellPackage}/${impastoShellPackage.quickshellConfigurationDirectory}";

    xdg.dataFile = {
      "impasto/palette-board.json".source =
        "${impastoShellPackage}/share/impasto/data/palette-board.json";
      "impasto/palette-board.png".source = "${impastoShellPackage}/share/impasto/data/palette-board.png";
      "wallpapers" = {
        source = "${impastoShellPackage}/share/impasto/wallpapers";
        recursive = true;
      };
    };

    home.activation.seedImpastoFirstRunSettings =
      lib.hm.dag.entryBetween [ "reloadSystemd" ] [ "writeBoundary" ]
        ''
          impastoSettingsFile="''${XDG_STATE_HOME:-$HOME/.local/state}/quickshell/settings.json"
          if [ ! -e "$impastoSettingsFile" ]; then
            $DRY_RUN_CMD install -D -m 644 ${firstRunSettings} "$impastoSettingsFile"
          fi
        '';

    custom.desktopShell = {
      sessionServices = [ "impasto-shell.service" ];
      hyprlandBindings = ''
        bindd = SUPER, J, Pin or hide the bar, exec, ${callImpastoCommand "bar" "pin"}
        bindd = SUPER, M, Media, global, quickshell:media
        bindd = SUPER, Q, Launcher, global, quickshell:launcher
        bindd = SUPER, A, Notifications and controls, global, quickshell:controls
      '';
    };

    systemd.user.services.impasto-shell = {
      Unit = {
        Description = "Impasto desktop shell";
        After = [ "graphical-session.target" ];
        PartOf = [ "graphical-session.target" ];
        ConditionEnvironment = "WAYLAND_DISPLAY";
        X-Restart-Triggers = [ "${impastoShellPackage}" ];
      };

      Service = {
        Type = "simple";
        ExecStart = "${impastoShellPackage}/bin/impasto-shell";
        Environment = [
          "QT_QPA_PLATFORM=wayland"
          "IMPASTO_LOCK_COMMAND=hyprlock"
        ];
        Restart = "always";
        RestartSec = "1s";
      };

      Install = {
        WantedBy = [ "graphical-session.target" ];
      };
    };
  };
}
