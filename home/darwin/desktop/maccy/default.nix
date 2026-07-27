{ config, pkgs, ... }:
{
  home.activation.configureMaccyDefaults = config.lib.dag.entryAfter [ "writeBoundary" ] ''
    ${pkgs.coreutils}/bin/timeout 5 /usr/bin/defaults write org.p0deje.Maccy KeyboardShortcuts_popup -string '{"carbonKeyCode":9,"carbonModifiers":768}' 2>/dev/null || true
    ${pkgs.coreutils}/bin/timeout 5 /usr/bin/defaults write org.p0deje.Maccy pasteByDefault -bool true 2>/dev/null || true
    ${pkgs.coreutils}/bin/timeout 5 /usr/bin/defaults write org.p0deje.Maccy SUEnableAutomaticChecks -bool false 2>/dev/null || true
    ${pkgs.coreutils}/bin/timeout 5 /usr/bin/defaults write org.p0deje.Maccy loginItemEnabled -bool false 2>/dev/null || true
  '';

  launchd.agents.maccy = {
    enable = true;
    config = {
      Label = "com.dotfiles.maccy";
      Program = "/Applications/Maccy.app/Contents/MacOS/Maccy";
      KeepAlive = true;
      RunAtLoad = true;
      StandardOutPath = "/tmp/maccy.log";
      StandardErrorPath = "/tmp/maccy.err.log";
    };
  };
}
