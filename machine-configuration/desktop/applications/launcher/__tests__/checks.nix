{
  helpers,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [ ../fuzzel-home-manager.nix ];

  vicinaeToggleChord = import ../vicinae-toggle-chord.nix;
  vicinaeConfiguration = helpers.homeManagerTestConfigurationForDarwin [
    ../../../../operating-system/health-check/health-check-home-manager.nix
    ../vicinae-home-manager.nix
  ];
  vicinaeGeneratedSettings =
    builtins.fromJSON
      vicinaeConfiguration.home.file.".config/vicinae/nix-generated-settings.json".text;
  vicinaeLaunchConfiguration = vicinaeConfiguration.launchd.agents.vicinae.config;
  launcherKarabinerRule = builtins.head (
    import ../../../input/karabiner/rules/window-management-rules.nix { }
  );
in
{
  domain-desktop-fuzzel-enabled =
    mkEvalCheck "domain-desktop-fuzzel-enabled" cfg.programs.fuzzel.enable
      "fuzzel launcher should be enabled";

  domain-desktop-vicinae-telemetry-disabled =
    mkEvalCheck "domain-desktop-vicinae-telemetry-disabled"
      (vicinaeGeneratedSettings.telemetry.system_info == false)
      "Vicinae system telemetry defaults to on and must be disabled by the generated settings";

  domain-desktop-vicinae-karabiner-sends-registered-chord =
    mkEvalCheck "domain-desktop-vicinae-karabiner-sends-registered-chord"
      (
        vicinaeGeneratedSettings.global_shortcuts.toggle == vicinaeToggleChord.vicinaeShortcut
        && (builtins.head launcherKarabinerRule.manipulators).to == [ vicinaeToggleChord.karabinerOutput ]
      )
      "Cmd+Q must send the same chord Vicinae registers as its toggle shortcut";

  domain-desktop-vicinae-login-item-registration-suppressed =
    mkEvalCheck "domain-desktop-vicinae-login-item-registration-suppressed"
      (builtins.hasAttr ".local/state/vicinae/login-item-registered" vicinaeConfiguration.home.file)
      "Vicinae's own login item would race the launchd agent, and the loser exits and respawns forever under KeepAlive";

  domain-desktop-vicinae-launch-agent-keeps-cask-binary-alive =
    mkEvalCheck "domain-desktop-vicinae-launch-agent-keeps-cask-binary-alive"
      (
        vicinaeLaunchConfiguration.ProgramArguments == [
          "/Applications/Vicinae.app/Contents/MacOS/Vicinae"
        ]
        && vicinaeLaunchConfiguration.KeepAlive == true
      )
      "The launch agent must keep the Homebrew cask's bundle executable running";
}
