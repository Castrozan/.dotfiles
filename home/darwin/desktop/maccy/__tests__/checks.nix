{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  maccyConfiguration = helpers.homeManagerTestConfigurationForDarwin [ ../default.nix ];

  preferenceWriteLines = lib.filter (line: lib.hasInfix "/usr/bin/defaults write" line) (
    lib.splitString "\n" maccyConfiguration.home.activation.configureMaccyDefaults.data
  );

  everyPreferenceWriteIsTimeBounded =
    preferenceWriteLines != [ ]
    && lib.all (line: lib.hasInfix "/bin/timeout " line) preferenceWriteLines;

  everyPreferenceWriteToleratesItsOwnFailure =
    preferenceWriteLines != [ ] && lib.all (line: lib.hasInfix "|| true" line) preferenceWriteLines;
in
{
  domain-desktop-maccy-preference-writes-are-time-bounded =
    mkEvalCheck "domain-desktop-maccy-preference-writes-are-time-bounded"
      everyPreferenceWriteIsTimeBounded
      "Every `defaults write` against the Maccy preference domain must run under a timeout, because an unbounded one blocks forever when the domain is unreachable from the activation's session instead of returning non-zero, and a hung activation wedges the whole switch with the new home generation already linked and /run/current-system still on the old one";

  domain-desktop-maccy-preference-writes-tolerate-their-own-failure =
    mkEvalCheck "domain-desktop-maccy-preference-writes-tolerate-their-own-failure"
      everyPreferenceWriteToleratesItsOwnFailure
      "Every `defaults write` against the Maccy preference domain must end in `|| true`, because home-manager runs activation under set -e, so a write that legitimately fails on a headless rebuild or is cut short by its own timeout would otherwise abort activation before any later generation step runs";
}
