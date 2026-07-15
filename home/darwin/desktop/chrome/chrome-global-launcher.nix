{ pkgs }:
let
  chromeGlobalUserDataDirectoryRelativeToHome = ".config/chrome-global";
  personalChromeProfileDirectoryName = "Profile 2";

  chromeGlobalLauncherScript = ''
    exec /usr/bin/open --new -a "Google Chrome" --args \
      --user-data-dir="$HOME/${chromeGlobalUserDataDirectoryRelativeToHome}" \
      "$@"
  '';

  chromeGlobalLauncherPackage = pkgs.writeShellScriptBin "summon-chrome-global" chromeGlobalLauncherScript;

  chromePersonalProfileLauncherScript = ''
    exec ${chromeGlobalLauncherPackage}/bin/summon-chrome-global \
      --profile-directory="${personalChromeProfileDirectoryName}" \
      "$@"
  '';

  chromePersonalProfileLauncherPackage = pkgs.writeShellScriptBin "summon-chrome-personal-profile" chromePersonalProfileLauncherScript;
in
{
  inherit
    chromeGlobalUserDataDirectoryRelativeToHome
    chromeGlobalLauncherScript
    chromePersonalProfileLauncherScript
    chromeGlobalLauncherPackage
    chromePersonalProfileLauncherPackage
    ;
}
