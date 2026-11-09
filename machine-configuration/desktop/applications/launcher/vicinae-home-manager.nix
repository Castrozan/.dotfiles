{
  config,
  healthCheckLib,
  lib,
  pkgs,
  ...
}:
let
  vicinaeToggleChord = import ./vicinae-toggle-chord.nix;
  vicinaeLaunchdLabel = "com.dotfiles.vicinae";
  vicinaeBinaryPath = "/Applications/Vicinae.app/Contents/MacOS/Vicinae";
  vicinaeConfigurationDirectory = ".config/vicinae";
  applicationScriptDirectory = "${config.home.homeDirectory}/.local/share/vicinae/scripts";
  applicationScriptsLaunchdLabel = "com.dotfiles.vicinae-application-scripts";
  generatedSettingsFileName = "nix-generated-settings.json";
  userSettingsPath = "${config.home.homeDirectory}/${vicinaeConfigurationDirectory}/settings.json";
  userSettingsSeed = pkgs.writeText "vicinae-user-settings-seed.json" (
    builtins.toJSON {
      imports = [ "./${generatedSettingsFileName}" ];
    }
  );
in
{
  home = {
    file = {
      "${vicinaeConfigurationDirectory}/${generatedSettingsFileName}".text = builtins.toJSON {
        telemetry.system_info = false;
        global_shortcuts.toggle = vicinaeToggleChord.vicinaeShortcut;
        providers = {
          applications.enabled = false;
          scripts.entrypoints."generated-application.com.google.Chrome.sh".alias = "gc";
        };
      };
      ".local/state/vicinae/login-item-registered".text = "";
    };

    activation = {
      seedVicinaeUserSettings = lib.hm.dag.entryBetween [ "setupLaunchAgents" ] [ "linkGeneration" ] ''
        if [ ! -e ${lib.escapeShellArg userSettingsPath} ]; then
          run install -m 0644 ${userSettingsSeed} ${lib.escapeShellArg userSettingsPath}
        fi
      '';

      createVicinaeApplicationScriptDirectory =
        lib.hm.dag.entryBetween [ "setupLaunchAgents" ] [ "linkGeneration" ]
          ''
            run mkdir -p ${lib.escapeShellArg applicationScriptDirectory}
          '';
    };
  };

  launchd.agents.vicinae-application-scripts = {
    enable = true;
    config = {
      Label = applicationScriptsLaunchdLabel;
      ProgramArguments = [
        "${pkgs.python312}/bin/python3"
        "${./scripts}/generate_vicinae_application_scripts.py"
        "--script-directory"
        applicationScriptDirectory
      ];
      RunAtLoad = true;
      WatchPaths = [
        "/Applications"
        "${config.home.homeDirectory}/Applications"
      ];
      StandardOutPath = "/tmp/vicinae-application-scripts.log";
      StandardErrorPath = "/tmp/vicinae-application-scripts.log";
    };
  };

  launchd.agents.vicinae = {
    enable = true;
    config = {
      Label = vicinaeLaunchdLabel;
      ProgramArguments = [ vicinaeBinaryPath ];
      EnvironmentVariables.VICINAE_DISABLE_HUD = "1";
      KeepAlive = true;
      RunAtLoad = true;
      StandardOutPath = "/tmp/vicinae.log";
      StandardErrorPath = "/tmp/vicinae.log";
    };
  };

  healthCheck.probes = [
    (healthCheckLib.mkLaunchdProbe {
      name = "vicinae launcher";
      label = vicinaeLaunchdLabel;
    })
  ];
}
