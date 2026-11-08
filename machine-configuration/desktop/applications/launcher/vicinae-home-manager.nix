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
  generatedSettingsFileName = "nix-generated-settings.json";
  userSettingsPath = "${config.home.homeDirectory}/${vicinaeConfigurationDirectory}/settings.json";
  userSettingsSeed = pkgs.writeText "vicinae-user-settings-seed.json" (
    builtins.toJSON {
      imports = [ "./${generatedSettingsFileName}" ];
    }
  );
in
{
  home.file = {
    "${vicinaeConfigurationDirectory}/${generatedSettingsFileName}".text = builtins.toJSON {
      telemetry.system_info = false;
      global_shortcuts.toggle = vicinaeToggleChord.vicinaeShortcut;
    };
    ".local/state/vicinae/login-item-registered".text = "";
  };

  home.activation.seedVicinaeUserSettings =
    lib.hm.dag.entryBetween [ "setupLaunchAgents" ] [ "linkGeneration" ]
      ''
        if [ ! -e ${lib.escapeShellArg userSettingsPath} ]; then
          run install -m 0644 ${userSettingsSeed} ${lib.escapeShellArg userSettingsPath}
        fi
      '';

  launchd.agents.vicinae = {
    enable = true;
    config = {
      Label = vicinaeLaunchdLabel;
      ProgramArguments = [ vicinaeBinaryPath ];
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
