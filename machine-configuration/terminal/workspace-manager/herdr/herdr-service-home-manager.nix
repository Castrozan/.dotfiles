{
  config,
  inputs,
  lib,
  pkgs,
  ...
}:
let
  rebuildSafeLaunchAgentLib =
    import ../../../operating-system/launchd/rebuild-safe-launch-agent-library.nix
      {
        inherit config lib pkgs;
      };
  herdrPackage = inputs.herdr.packages.${pkgs.stdenv.hostPlatform.system}.default;
  serverPath = lib.concatStringsSep ":" [
    "/etc/profiles/per-user/${config.home.username}/bin"
    "${config.home.homeDirectory}/.nix-profile/bin"
    "/run/current-system/sw/bin"
    "/nix/var/nix/profiles/default/bin"
    "/usr/bin"
    "/bin"
  ];
  serverRunning = "${herdrPackage}/bin/herdr session list --json 2>/dev/null | ${pkgs.jq}/bin/jq -e -f ${./scripts/default-server-running.jq} >/dev/null";
  activeServerPackageFile = "${config.xdg.stateHome}/herdr/active-server-package";
  systemdHandoffImporter = pkgs.writeShellApplication {
    name = "herdr-systemd-handoff-importer";
    text = ''
      ${pkgs.systemd}/bin/systemd-notify --pid=parent
      exec ${herdrPackage}/bin/herdr "$@"
    '';
  };
  handoffImportExecutable =
    if pkgs.stdenv.hostPlatform.isLinux then
      "${systemdHandoffImporter}/bin/herdr-systemd-handoff-importer"
    else
      "${herdrPackage}/bin/herdr";
  herdrServerReconciler = pkgs.writeShellApplication {
    name = "reconcile-herdr-server";
    text = ''
      export HERDR_EXECUTABLE=${herdrPackage}/bin/herdr
      export HERDR_IMPORT_EXECUTABLE=${handoffImportExecutable}
      export HERDR_PACKAGE_IDENTITY=${herdrPackage}
      export HERDR_ACTIVE_PACKAGE_FILE=${activeServerPackageFile}
      exec ${pkgs.python3}/bin/python3 ${./scripts/reconcile-herdr-server.py} "$@"
    '';
  };
  herdrServer = pkgs.writeShellApplication {
    name = "herdr-server";
    text = ''
      while ${serverRunning}; do
        ${pkgs.coreutils}/bin/sleep 5
      done
      ${herdrServerReconciler}/bin/reconcile-herdr-server record-active
      exec ${herdrPackage}/bin/herdr server
    '';
  };
  legacyServerImporter = pkgs.writeShellApplication {
    name = "herdr-legacy-server-importer";
    text = ''
      runtime_user_id="$(${pkgs.coreutils}/bin/id -u)"
      export XDG_RUNTIME_DIR="/run/user/$runtime_user_id"
      export HERDR_LEGACY_SERVER_PID="$PPID"
      export HERDR_SYSTEMCTL="''${HERDR_SYSTEMCTL:-${pkgs.systemd}/bin/systemctl}"
      export HERDR_BUSCTL="''${HERDR_BUSCTL:-${pkgs.systemd}/bin/busctl}"
      export HERDR_LEGACY_UNIT="''${HERDR_LEGACY_UNIT:-clawde-herdr-server.service}"
      export HERDR_TARGET_UNIT="''${HERDR_TARGET_UNIT:-herdr.service}"
      ${pkgs.python3}/bin/python3 ${./scripts/adopt-legacy-herdr-server.py} prepare-import
      exec ${herdrPackage}/bin/herdr "$@"
    '';
  };
  waitForHerdrServer = pkgs.writeShellApplication {
    name = "wait-for-herdr-server";
    text = ''
      for _ in $(${pkgs.coreutils}/bin/seq 1 300); do
        if ${serverRunning}; then
          exit 0
        fi
        ${pkgs.coreutils}/bin/sleep 0.1
      done
      exit 1
    '';
  };
in
{
  config = lib.mkMerge [
    {
      home.activation.reconcileHerdrServer =
        lib.hm.dag.entryAfter
          (
            [ "reloadHerdrAfterConfigSeed" ]
            ++ lib.optionals pkgs.stdenv.hostPlatform.isLinux [ "adoptLegacyHerdrServer" ]
            ++ lib.optionals pkgs.stdenv.hostPlatform.isDarwin [ "setupLaunchAgents" ]
          )
          ''
            run ${herdrServerReconciler}/bin/reconcile-herdr-server reconcile
          '';
    }

    (lib.mkIf pkgs.stdenv.hostPlatform.isLinux {
      systemd.user.services.herdr = {
        Unit = {
          Description = "Shared Herdr server";
          X-RestartIfChanged = false;
          X-StopIfChanged = false;
        };
        Service = {
          ExecStart = "${herdrServer}/bin/herdr-server";
          ExecStartPost = "${waitForHerdrServer}/bin/wait-for-herdr-server";
          Environment = [
            "HOME=${config.home.homeDirectory}"
            "PATH=${serverPath}"
          ];
          NotifyAccess = "all";
          Restart = "always";
          RestartSec = 1;
          MemoryHigh = "8G";
          Delegate = true;
        };
        Install.WantedBy = [ "default.target" ];
      };

      home.activation.adoptLegacyHerdrServer = lib.hm.dag.entryAfter [ "reloadSystemd" ] ''
        run ${pkgs.coreutils}/bin/env \
          HERDR_SYSTEMCTL=${pkgs.systemd}/bin/systemctl \
          HERDR_BUSCTL=${pkgs.systemd}/bin/busctl \
          HERDR_EXECUTABLE=${herdrPackage}/bin/herdr \
          HERDR_IMPORT_EXECUTABLE=${legacyServerImporter}/bin/herdr-legacy-server-importer \
          HERDR_RECONCILER=${herdrServerReconciler}/bin/reconcile-herdr-server \
          HERDR_LEGACY_UNIT=clawde-herdr-server.service \
          HERDR_TARGET_UNIT=herdr.service \
          ${pkgs.python3}/bin/python3 ${./scripts/adopt-legacy-herdr-server.py} adopt
      '';
    })

    (lib.mkIf pkgs.stdenv.hostPlatform.isDarwin (
      rebuildSafeLaunchAgentLib.mkRebuildSafeLaunchAgent {
        name = "herdr";
        label = "com.dotfiles.herdr";
        package = herdrServer;
        executableName = "herdr-server";
        serviceConfig = {
          EnvironmentVariables = {
            HOME = config.home.homeDirectory;
            PATH = serverPath;
          };
          RunAtLoad = true;
          KeepAlive = true;
          StandardOutPath = "${config.home.homeDirectory}/Library/Logs/herdr-server.log";
          StandardErrorPath = "${config.home.homeDirectory}/Library/Logs/herdr-server.log";
        };
      }
    ))
  ];
}
