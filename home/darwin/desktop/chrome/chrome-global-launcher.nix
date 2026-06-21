{ pkgs }:
let
  chromeGlobalUserDataDirectoryRelativeToHome = ".config/chrome-global";

  chromeGlobalLauncherScript = ''
    exec /usr/bin/open --new -a "Google Chrome" --args \
      --user-data-dir="$HOME/${chromeGlobalUserDataDirectoryRelativeToHome}" \
      "$@"
  '';

  chromeGlobalUrlOpenerScript = ''
    exec "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
      --user-data-dir="$HOME/${chromeGlobalUserDataDirectoryRelativeToHome}" \
      "$@"
  '';
in
{
  inherit
    chromeGlobalUserDataDirectoryRelativeToHome
    chromeGlobalLauncherScript
    chromeGlobalUrlOpenerScript
    ;

  chromeGlobalLauncherPackage = pkgs.writeShellScriptBin "summon-chrome-global" chromeGlobalLauncherScript;

  chromeGlobalUrlOpenerPackage = pkgs.writeShellScriptBin "open-url-in-chrome-global" chromeGlobalUrlOpenerScript;
}
