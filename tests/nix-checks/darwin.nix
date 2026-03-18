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

  linuxOnlyCheckNames = [
    "domain-browser-chrome-desktop-entry"
    "domain-browser-firefox-enabled"
    "domain-desktop-clipse-service-config"
    "domain-desktop-fontconfig-enabled"
    "domain-desktop-fuzzel-enabled"
    "domain-terminal-fish-conf-d-deployed"
  ];

  excludeLinuxOnlyChecks =
    checks: lib.filterAttrs (name: _: !builtins.elem name linuxOnlyCheckNames) checks;

  claudeChecks = import ../../home/modules/claude/tests/checks.nix moduleArgs;
  codexChecks = import ../../home/modules/codex/tests/checks.nix moduleArgs;
  terminalChecks = import ../../home/modules/terminal/tests/checks.nix domainArgs;
  editorChecks = import ../../home/modules/editor/tests/checks.nix domainArgs;
  browserChecks = import ../../home/modules/browser/tests/checks.nix domainArgs;
  desktopChecks = import ../../home/modules/desktop/tests/checks.nix domainArgs;
  devChecks = import ../../home/modules/dev/tests/checks.nix domainArgs;
  macbookChecks = import ../../hosts/macbook/tests/checks.nix domainArgs;
in
excludeLinuxOnlyChecks (
  macbookChecks
  // claudeChecks
  // codexChecks
  // terminalChecks
  // editorChecks
  // browserChecks
  // desktopChecks
  // devChecks
)
