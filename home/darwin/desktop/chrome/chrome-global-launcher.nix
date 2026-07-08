{ pkgs }:
let
  chromeGlobalUserDataDirectoryRelativeToHome = ".config/chrome-global";

  chromeGlobalLauncherScript = ''
    exec /usr/bin/open --new -a "Google Chrome" --args \
      --user-data-dir="$HOME/${chromeGlobalUserDataDirectoryRelativeToHome}" \
      "$@"
  '';
in
{
  inherit
    chromeGlobalUserDataDirectoryRelativeToHome
    chromeGlobalLauncherScript
    ;

  chromeGlobalLauncherPackage = pkgs.writeShellScriptBin "summon-chrome-global" chromeGlobalLauncherScript;
}
