{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  appearanceConfiguration = helpers.homeManagerTestConfigurationForDarwin [ ../default.nix ];

  activationLines = lib.splitString "\n" appearanceConfiguration.home.activation.applyMacosThemeAppearance.data;

  preferenceCommandLines = lib.filter (line: lib.hasInfix "/usr/bin/defaults " line) activationLines;

  timeoutExportLines = lib.filter (
    line: lib.hasInfix "export TIMEOUT_BINARY_PATH=" line
  ) activationLines;

  everyPreferenceCommandIsTimeBounded =
    preferenceCommandLines != [ ]
    && lib.all (line: lib.hasInfix "\"$TIMEOUT_BINARY_PATH\" " line) preferenceCommandLines;

  theTimeoutBinaryResolvesToARealExecutable =
    timeoutExportLines != [ ] && lib.all (line: lib.hasInfix "/bin/timeout" line) timeoutExportLines;

  everyPreferenceCommandToleratesItsOwnFailure =
    preferenceCommandLines != [ ] && lib.all (line: lib.hasInfix "||" line) preferenceCommandLines;
in
{
  domain-desktop-theming-darwin-preference-commands-are-time-bounded =
    mkEvalCheck "domain-desktop-theming-darwin-preference-commands-are-time-bounded"
      everyPreferenceCommandIsTimeBounded
      "Every `defaults` command in the macOS appearance activation must run under the timeout binary, because these target the global domain `-g` held by cfprefsd, they run unconditionally on every activation of every darwin machine, and `|| true` guards only a non-zero exit while a wedged cfprefsd makes the command hang instead of fail, wedging the switch with the new home generation already linked and /run/current-system still on the old one";

  domain-desktop-theming-darwin-timeout-binary-resolves-to-a-real-executable =
    mkEvalCheck "domain-desktop-theming-darwin-timeout-binary-resolves-to-a-real-executable"
      theTimeoutBinaryResolvesToARealExecutable
      "TIMEOUT_BINARY_PATH must be exported as a concrete path to a timeout executable, because the bound on every `defaults` command is applied by expanding that variable; were it exported empty or unset the expansion would run the wrong program, each command would fail into its own `||` fallback, and the appearance would silently never be applied while activation still reported success";

  domain-desktop-theming-darwin-preference-commands-tolerate-their-own-failure =
    mkEvalCheck "domain-desktop-theming-darwin-preference-commands-tolerate-their-own-failure"
      everyPreferenceCommandToleratesItsOwnFailure
      "Every `defaults` command in the macOS appearance activation must carry a `||` fallback, because home-manager runs activation under set -e where a headless rebuild with no GUI session, or a command cut short by its own timeout, would otherwise abort activation before later generation steps run; matching the theme's accent colour is cosmetic and must never be able to fail a switch";
}
