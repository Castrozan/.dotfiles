{ pkgs }:
let
  chromeGlobalUserDataDirectoryRelativeToHome = ".config/chrome-global";
  personalChromeProfileDirectoryName = "Profile 2";
  workChromeProfileDirectoryName = "Profile 1";

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

  chromeWorkProfileLauncherScript = ''
    exec ${chromeGlobalLauncherPackage}/bin/summon-chrome-global \
      --profile-directory="${workChromeProfileDirectoryName}" \
      "$@"
  '';

  chromeWorkProfileLauncherPackage = pkgs.writeShellScriptBin "summon-chrome-work-profile" chromeWorkProfileLauncherScript;
in
{
  inherit
    chromeGlobalUserDataDirectoryRelativeToHome
    chromeGlobalLauncherScript
    chromePersonalProfileLauncherScript
    chromeWorkProfileLauncherScript
    chromeGlobalLauncherPackage
    chromePersonalProfileLauncherPackage
    chromeWorkProfileLauncherPackage
    ;
}
