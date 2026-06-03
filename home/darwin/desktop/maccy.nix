{ config, ... }:
{
  home.activation.configureMaccyDefaults = config.lib.dag.entryAfter [ "writeBoundary" ] ''
    # Maccy's preferences live in a sandboxed container that is unwritable until
    # the app has run once and is absent on a headless rebuild over SSH, where
    # `defaults write ... ; exiting` returns non-zero. home-manager runs
    # activation under set -e, so each write is guarded with `|| true` to keep a
    # headless rebuild from aborting before later generations run. The launchd
    # agent still launches Maccy, which re-reads these on next start.
    /usr/bin/defaults write org.p0deje.Maccy KeyboardShortcuts_popup -string '{"carbonKeyCode":9,"carbonModifiers":768}' 2>/dev/null || true
    /usr/bin/defaults write org.p0deje.Maccy pasteByDefault -bool true 2>/dev/null || true
    /usr/bin/defaults write org.p0deje.Maccy SUEnableAutomaticChecks -bool false 2>/dev/null || true
    /usr/bin/defaults write org.p0deje.Maccy loginItemEnabled -bool false 2>/dev/null || true
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
