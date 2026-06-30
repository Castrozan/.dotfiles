{
  pkgs,
  lib,
  inputs,
  self,
  nixpkgs-version,
  home-version,
}:
let
  domainArgs = {
    inherit
      pkgs
      lib
      inputs
      nixpkgs-version
      home-version
      ;
  };

  moduleArgs = domainArgs // {
    inherit self;
  };

  claudeChecks = import ../../home/base/claude/tests/checks.nix moduleArgs;
  codexChecks = import ../../home/base/codex/tests/checks.nix moduleArgs;

  terminalChecks = import ../../home/base/terminal/tests/checks.nix domainArgs;
  editorChecks = import ../../home/base/editor/tests/checks.nix domainArgs;
  browserChecks = import ../../home/base/browser/tests/checks.nix domainArgs;
  braveDesktopChecks = import ../../home/darwin/desktop/brave/tests/checks.nix domainArgs;
  chromeDesktopChecks = import ../../home/darwin/desktop/chrome/tests/checks.nix domainArgs;
  karabinerDesktopChecks = import ../../home/darwin/desktop/karabiner/tests/checks.nix domainArgs;
  cloudflareTunnelConnectorChecks = import ../../home/darwin/cloudflare-tunnel-connector/tests/checks.nix domainArgs;
  desktopChecks = import ../../home/base/desktop/tests/checks.nix domainArgs;
  devChecks = import ../../home/base/dev/tests/checks.nix domainArgs;
  gamingChecks = import ../../home/base/gaming/tests/checks.nix domainArgs;
  gnomeChecks = import ../../home/linux/gnome/tests/checks.nix domainArgs;
  securityChecks = import ../../home/base/security/tests/checks.nix domainArgs;
  ollamaChecks = import ../../home/base/ollama/tests/checks.nix domainArgs;
  opencodeChecks = import ../../home/base/opencode/tests/checks.nix domainArgs;
  audioChecks = import ../../home/linux/audio/tests/checks.nix domainArgs;
  networkChecks = import ../../home/base/network/tests/checks.nix domainArgs;
  systemChecks = import ../../home/base/system/tests/checks.nix domainArgs;
  voiceChecks = import ../../home/linux/voice/tests/checks.nix domainArgs;
  sourcebotChecks = import ../../home/base/sourcebot/tests/checks.nix domainArgs;

  chiseChecks = import ../../hosts/chise/tests/checks.nix moduleArgs;
  chromeDarwinPolicyChecks = import ../../hosts/shared-darwin/chrome/tests/checks.nix domainArgs;
  braveDarwinPolicyChecks = import ../../hosts/shared-darwin/brave/tests/checks.nix domainArgs;
in
claudeChecks
// codexChecks
// terminalChecks
// editorChecks
// browserChecks
// braveDesktopChecks
// chromeDesktopChecks
// karabinerDesktopChecks
// cloudflareTunnelConnectorChecks
// desktopChecks
// devChecks
// gamingChecks
// gnomeChecks
// securityChecks
// ollamaChecks
// opencodeChecks
// audioChecks
// networkChecks
// systemChecks
// voiceChecks
// sourcebotChecks
// chiseChecks
// chromeDarwinPolicyChecks
// braveDarwinPolicyChecks
