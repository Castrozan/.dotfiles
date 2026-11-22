{
  config,
  lib,
  pkgs,
  inputs,
  hostname,
  ...
}:
let
  agentHarness = ../../../agent-harness;
  agentToAgentClient = agentHarness + "/agent-to-agent-communication/client";
  chromeForTesting = import ../../browsers/chrome/chrome-for-testing-package.nix { inherit pkgs; };
  rebuildSafeLaunchAgentLibrary =
    import ../../operating-system/launchd/rebuild-safe-launch-agent-library.nix
      { inherit config lib pkgs; };
in
{
  imports = [ inputs.avatar.homeManagerModules.default ];

  services.avatar = {
    enable = true;
    hostName = hostname;
    topology = {
      host = "chise";
      machines = [
        "chise"
        "kira"
        "rin"
      ];
    };
    servantRoster = agentHarness + "/servants/roster.txt";
    herdrPackage = inputs.herdr.packages.${pkgs.stdenv.hostPlatform.system}.default;
    a2aPackage = import (agentToAgentClient + "/a2a-client-package.nix") { inherit pkgs; };
    peerIdentityPythonPath = [
      (agentToAgentClient + "/scripts")
      (agentHarness + "/servants")
      (agentHarness + "/hooks/runtime/common")
    ];
    speechPackage = import ../media-generation/speech-package.nix { inherit pkgs; };
    mac = {
      browserApplication = "${chromeForTesting}/lib/Google Chrome for Testing.app";
      launchAgent = rebuildSafeLaunchAgentLibrary.mkRebuildSafeLaunchAgent;
    };
  };
}
