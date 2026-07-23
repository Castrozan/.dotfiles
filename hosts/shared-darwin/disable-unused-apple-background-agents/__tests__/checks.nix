{
  pkgs,
  lib,
  ...
}:
let
  helpers = import ../../../../__tests__/nix-checks/helpers.nix {
    inherit pkgs lib;
    inputs = null;
    nixpkgs-version = null;
    home-version = null;
  };
  inherit (helpers) mkEvalCheck;

  disableUnusedAppleBackgroundAgentsConfig = import ../default.nix {
    inherit lib;
    username = "testuser";
  };
  postActivationScript =
    disableUnusedAppleBackgroundAgentsConfig.system.activationScripts.postActivation.text.content;

  representativeAgentLabels = [
    "com.apple.rcd"
    "com.apple.AMPLibraryAgent"
    "com.apple.photoanalysisd"
    "com.apple.mediaanalysisd"
    "com.apple.cloudd"
    "com.apple.bird"
    "com.apple.commerce"
    "com.apple.suggestd"
    "com.apple.siriactionsd"
    "com.apple.mediaremoted"
  ];

  everyRepresentativeAgentIsForcedDisabled = lib.all (
    agentLabel:
    lib.hasInfix ''launchctl disable "gui/'' postActivationScript
    && lib.hasInfix agentLabel postActivationScript
  ) representativeAgentLabels;

  bothDomainsTargeted =
    lib.hasInfix ''launchctl disable "gui/'' postActivationScript
    && lib.hasInfix ''launchctl disable "system/'' postActivationScript;
in
{
  macbook-unused-apple-background-agents-disabled =
    mkEvalCheck "macbook-unused-apple-background-agents-disabled"
      (everyRepresentativeAgentIsForcedDisabled && bothDomainsTargeted)
      "the postActivation sweep must launchctl-disable the unused Apple background agents (Music/media, iCloud, Photos, App Store, Siri/Shortcuts) across both the gui and system domains so they stop lingering after every rebuild";
}
