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

  homeManagerModuleChecks = import ./home-manager-modules.nix moduleArgs;

  claudeChecks = import ../../home/modules/claude/tests/checks.nix moduleArgs;
  codexChecks = import ../../home/modules/codex/tests/checks.nix moduleArgs;
  openclawChecks = import ../../home/modules/openclaw/tests/checks.nix moduleArgs;
  openclawConfigChecks = import ../../home/modules/openclaw/tests/nix-config-checks.nix moduleArgs;

  terminalChecks = import ../../home/modules/terminal/tests/checks.nix domainArgs;
  editorChecks = import ../../home/modules/editor/tests/checks.nix domainArgs;
  browserChecks = import ../../home/modules/browser/tests/checks.nix domainArgs;
  desktopChecks = import ../../home/modules/desktop/tests/checks.nix domainArgs;
  devChecks = import ../../home/modules/dev/tests/checks.nix domainArgs;
  gamingChecks = import ../../home/modules/gaming/tests/checks.nix domainArgs;
  gnomeChecks = import ../../home/modules/gnome/tests/checks.nix domainArgs;
  securityChecks = import ../../home/modules/security/tests/checks.nix domainArgs;
  ollamaChecks = import ../../home/modules/ollama/tests/checks.nix domainArgs;
  opencodeChecks = import ../../home/modules/opencode/tests/checks.nix domainArgs;
  openclawMeshChecks = import ../../home/modules/openclaw-mesh/tests/checks.nix domainArgs;
  audioChecks = import ../../home/modules/audio/tests/checks.nix domainArgs;
  networkChecks = import ../../home/modules/network/tests/checks.nix domainArgs;
  systemChecks = import ../../home/modules/system/tests/checks.nix domainArgs;
  voiceChecks = import ../../home/modules/voice/tests/checks.nix domainArgs;
  sourcebotChecks = import ../../home/modules/sourcebot/tests/checks.nix domainArgs;
in
homeManagerModuleChecks
// claudeChecks
// codexChecks
// openclawChecks
// openclawConfigChecks
// terminalChecks
// editorChecks
// browserChecks
// desktopChecks
// devChecks
// gamingChecks
// gnomeChecks
// securityChecks
// ollamaChecks
// opencodeChecks
// openclawMeshChecks
// audioChecks
// networkChecks
// systemChecks
// voiceChecks
// sourcebotChecks
