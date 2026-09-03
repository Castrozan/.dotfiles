{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  hammerspoonConfiguration = helpers.homeManagerTestConfigurationForDarwin [
    ../hammerspoon-home-manager.nix
  ];

  preferenceWriteLines = lib.filter (line: lib.hasInfix "/usr/bin/defaults write" line) (
    lib.splitString "\n" hammerspoonConfiguration.home.activation.suppressHammerspoonConsoleAtLaunch.data
  );

  everyPreferenceWriteIsTimeBounded =
    preferenceWriteLines != [ ]
    && lib.all (line: lib.hasInfix "/bin/timeout " line) preferenceWriteLines;

  everyPreferenceWriteToleratesItsOwnFailure =
    preferenceWriteLines != [ ] && lib.all (line: lib.hasInfix "|| true" line) preferenceWriteLines;
  hammerspoonInitContent = builtins.readFile ../init.lua;
  commandControlMRevealsMenuBar = lib.hasInfix (
    "hs.hotkey.bind({ \"cmd\", \"ctrl\" }, \"m\", function()\n"
    + "\tmenuBarReveal.brieflyReveal()\n"
    + "end)"
  ) hammerspoonInitContent;
in
{
  domain-desktop-hammerspoon-preference-writes-are-time-bounded =
    mkEvalCheck "domain-desktop-hammerspoon-preference-writes-are-time-bounded"
      everyPreferenceWriteIsTimeBounded
      "Every `defaults write` against the Hammerspoon preference domain must run under a timeout, because Hammerspoon holds that domain live and an unbounded write blocks forever when the domain is unreachable from the activation's session instead of returning non-zero, wedging the switch with the new home generation already linked and /run/current-system still on the old one";

  domain-desktop-hammerspoon-preference-writes-tolerate-their-own-failure =
    mkEvalCheck "domain-desktop-hammerspoon-preference-writes-tolerate-their-own-failure"
      everyPreferenceWriteToleratesItsOwnFailure
      "Every `defaults write` against the Hammerspoon preference domain must end in `|| true`, because home-manager runs activation under set -e, so a write that legitimately fails on a headless rebuild or is cut short by its own timeout would otherwise abort activation before any later generation step runs; suppressing the console window is cosmetic and must never be able to fail a switch";

  domain-desktop-hammerspoon-codex-notification-wezterm-summon-is-deployed =
    mkEvalCheck "domain-desktop-hammerspoon-codex-notification-wezterm-summon-is-deployed"
      (
        builtins.hasAttr ".hammerspoon/wezterm_summon.lua" hammerspoonConfiguration.home.file
        && lib.hasInfix "function summonWezTermToCurrentWorkspace()" hammerspoonInitContent
      )
      "The Darwin Codex notification driver calls summonWezTermToCurrentWorkspace through hs -c, so Hammerspoon must deploy its implementation and expose that exact global function";

  domain-desktop-hammerspoon-command-control-m-reveals-menu-bar =
    mkEvalCheck "domain-desktop-hammerspoon-command-control-m-reveals-menu-bar"
      commandControlMRevealsMenuBar
      "Cmd+Ctrl+M must invoke the shared pointer-free menu bar reveal capability so the direct keybind preserves the same auto-hide behavior as workspace and window switching";
}
