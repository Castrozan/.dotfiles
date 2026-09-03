{ pkgs, lib, ... }:
let
  nightlyRunHour = 3;

  userProfileBinaryDirectories = [
    "$HOME/.nix-profile/bin"
    "/etc/profiles/per-user/$USER/bin"
    "/run/current-system/sw/bin"
    "/nix/var/nix/profiles/default/bin"
  ];

  testingPythonLibraryPath = ./scripts/lib;

  nightlyRunnerPythonSource = pkgs.writeText "dotfiles-nightly-deep-tests-source.py" (
    builtins.readFile ./scripts/nightly_deep_test_tiers.py
  );

  dotfiles-nightly-deep-tests = pkgs.writeShellScriptBin "dotfiles-nightly-deep-tests" ''
    export PATH="${
      lib.makeBinPath [
        pkgs.git
        pkgs.bash
      ]
    }:${lib.concatStringsSep ":" userProfileBinaryDirectories}:$PATH"
    export PYTHONPATH="${testingPythonLibraryPath}:''${PYTHONPATH:-}"
    exec ${pkgs.python312}/bin/python3 ${nightlyRunnerPythonSource} "$@"
  '';

  nightlyRunnerCommand = "${dotfiles-nightly-deep-tests}/bin/dotfiles-nightly-deep-tests";

  nightlyRunnerLogFilePath = "/tmp/dotfiles-nightly-deep-test-tiers.log";
in
{
  config = lib.mkMerge [
    { home.packages = [ dotfiles-nightly-deep-tests ]; }

    (lib.mkIf pkgs.stdenv.hostPlatform.isDarwin {
      launchd.agents.nightly-deep-test-tiers = {
        enable = true;
        config = {
          Label = "com.dotfiles.nightly-deep-test-tiers";
          ProgramArguments = [ nightlyRunnerCommand ];
          RunAtLoad = false;
          StartCalendarInterval = [
            {
              Hour = nightlyRunHour;
              Minute = 0;
            }
          ];
          StandardOutPath = nightlyRunnerLogFilePath;
          StandardErrorPath = nightlyRunnerLogFilePath;
        };
      };
    })

    (lib.mkIf pkgs.stdenv.hostPlatform.isLinux {
      systemd.user.services.nightly-deep-test-tiers = {
        Unit.Description = "Integration and runtime test tiers";
        Service = {
          Type = "oneshot";
          ExecStart = nightlyRunnerCommand;
        };
      };
      systemd.user.timers.nightly-deep-test-tiers = {
        Unit.Description = "Nightly 0${toString nightlyRunHour}:00 run of the integration and runtime test tiers";
        Timer = {
          OnCalendar = "0${toString nightlyRunHour}:00";
          Persistent = false;
        };
        Install.WantedBy = [ "timers.target" ];
      };
    })
  ];
}
