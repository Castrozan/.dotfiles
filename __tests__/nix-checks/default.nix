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

  claudeChecks = import ../../home/base/claude/__tests__/checks.nix moduleArgs;
  clawdeChecks = import ../../home/base/clawde/__tests__/checks.nix moduleArgs;
  codexChecks = import ../../home/base/codex/__tests__/checks.nix moduleArgs;

  terminalChecks = import ../../home/base/terminal/__tests__/checks.nix domainArgs;
  editorChecks = import ../../home/base/editor/__tests__/checks.nix domainArgs;
  browserChecks = import ../../home/base/browser/__tests__/checks.nix domainArgs;
  braveDesktopChecks = import ../../home/darwin/desktop/brave/__tests__/checks.nix domainArgs;
  chromeDesktopChecks = import ../../home/darwin/desktop/chrome/__tests__/checks.nix domainArgs;
  karabinerDesktopChecks = import ../../home/darwin/desktop/karabiner/__tests__/checks.nix domainArgs;
  maccyDesktopChecks = import ../../home/darwin/desktop/maccy/__tests__/checks.nix domainArgs;
  hammerspoonDesktopChecks = import ../../home/darwin/desktop/hammerspoon/__tests__/checks.nix domainArgs;
  cloudflareTunnelConnectorChecks = import ../../home/darwin/cloudflare-tunnel-connector/__tests__/checks.nix domainArgs;
  desktopChecks = import ../../home/base/desktop/__tests__/checks.nix domainArgs;
  screensaverChecks = import ../../home/base/desktop/screensaver/__tests__/checks.nix domainArgs;
  themingDarwinChecks = import ../../home/base/desktop/theming/darwin/__tests__/checks.nix domainArgs;
  devChecks = import ../../home/base/dev/__tests__/checks.nix domainArgs;
  obsidianHeadlessChecks = import ../../home/base/media/obsidian/__tests__/checks.nix domainArgs;
  gamingChecks = import ../../home/base/gaming/__tests__/checks.nix domainArgs;
  gnomeChecks = import ../../home/linux/gnome/__tests__/checks.nix domainArgs;
  hyprlandChecks = import ../../home/linux/hyprland/__tests__/checks.nix domainArgs;
  securityChecks = import ../../home/base/security/__tests__/checks.nix domainArgs;
  a2aAgentChecks = import ../../home/base/agents/a2a/__tests__/checks.nix domainArgs;
  ollamaChecks = import ../../home/base/ollama/__tests__/checks.nix domainArgs;
  opencodeChecks = import ../../home/base/opencode/__tests__/checks.nix domainArgs;
  audioChecks = import ../../home/linux/audio/__tests__/checks.nix domainArgs;
  networkChecks = import ../../home/base/network/__tests__/checks.nix domainArgs;
  systemChecks = import ../../home/base/system/__tests__/checks.nix domainArgs;
  voiceChecks = import ../../home/linux/voice/__tests__/checks.nix domainArgs;
  sourcebotChecks = import ../../home/base/sourcebot/__tests__/checks.nix domainArgs;

  chiseChecks = import ../../hosts/chise/__tests__/checks.nix moduleArgs;
  rinChecks = import ../../hosts/rin/__tests__/checks.nix moduleArgs;
  chromeDarwinPolicyChecks = import ../../hosts/shared-darwin/chrome/__tests__/checks.nix domainArgs;
  claudeDarwinPolicyChecks = import ../../hosts/shared-darwin/claude/__tests__/checks.nix domainArgs;
  braveDarwinPolicyChecks = import ../../hosts/shared-darwin/brave/__tests__/checks.nix domainArgs;
  disableUnusedAppleBackgroundAgentsChecks = import ../../hosts/shared-darwin/disable-unused-apple-background-agents/__tests__/checks.nix domainArgs;
  displaysDarwinChecks = import ../../hosts/shared-darwin/displays/__tests__/checks.nix domainArgs;
in
claudeChecks
// clawdeChecks
// codexChecks
// terminalChecks
// editorChecks
// browserChecks
// braveDesktopChecks
// chromeDesktopChecks
// karabinerDesktopChecks
// maccyDesktopChecks
// hammerspoonDesktopChecks
// cloudflareTunnelConnectorChecks
// desktopChecks
// screensaverChecks
// themingDarwinChecks
// devChecks
// obsidianHeadlessChecks
// gamingChecks
// gnomeChecks
// hyprlandChecks
// securityChecks
// a2aAgentChecks
// ollamaChecks
// opencodeChecks
// audioChecks
// networkChecks
// systemChecks
// voiceChecks
// sourcebotChecks
// chiseChecks
// rinChecks
// chromeDarwinPolicyChecks
// claudeDarwinPolicyChecks
// braveDarwinPolicyChecks
// disableUnusedAppleBackgroundAgentsChecks
// displaysDarwinChecks
