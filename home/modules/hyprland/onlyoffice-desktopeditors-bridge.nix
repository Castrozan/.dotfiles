{ pkgs, ... }:
let
  onlyofficeDesktopEditorsBridgeLauncherPackage = pkgs.writeShellScriptBin "onlyoffice-desktopeditors-bridge" ''
    set -Eeuo pipefail

    readonly onlyofficeDesktopEditorsDefaultLauncherPath='${pkgs.onlyoffice-desktopeditors}/bin/onlyoffice-desktopeditors'
    readonly onlyofficeDesktopEditorsLauncherPathInsideFhsEnvironmentRootfs='/usr/bin/onlyoffice-desktopeditors'

    _resolveOnlyofficeDesktopEditorsBwrapLauncherScriptPath() {
      ${pkgs.coreutils}/bin/readlink -f "$onlyofficeDesktopEditorsDefaultLauncherPath"
    }

    _extractOnlyofficeDesktopEditorsFhsEnvironmentRootfsPathFromBwrapLauncherScript() {
      local onlyofficeDesktopEditorsBwrapLauncherScriptPath=""
      onlyofficeDesktopEditorsBwrapLauncherScriptPath="$(_resolveOnlyofficeDesktopEditorsBwrapLauncherScriptPath)"

      ${pkgs.gnugrep}/bin/grep -oE '/nix/store/[a-z0-9]{32}-onlyoffice-desktopeditors-[^[:space:]"]*-fhsenv-rootfs' "$onlyofficeDesktopEditorsBwrapLauncherScriptPath" \
        | ${pkgs.coreutils}/bin/head -n 1
    }

    _resolveOnlyofficeDesktopEditorsFallbackLauncherPath() {
      local onlyofficeDesktopEditorsFhsEnvironmentRootfsPath=""
      local onlyofficeDesktopEditorsFallbackLauncherPathInsideFhsEnvironmentRootfs=""

      onlyofficeDesktopEditorsFhsEnvironmentRootfsPath="$(_extractOnlyofficeDesktopEditorsFhsEnvironmentRootfsPathFromBwrapLauncherScript)"

      if [ -z "$onlyofficeDesktopEditorsFhsEnvironmentRootfsPath" ]; then
        return 1
      fi

      onlyofficeDesktopEditorsFallbackLauncherPathInsideFhsEnvironmentRootfs="${onlyofficeDesktopEditorsFhsEnvironmentRootfsPath}${onlyofficeDesktopEditorsLauncherPathInsideFhsEnvironmentRootfs}"

      if [ ! -e "$onlyofficeDesktopEditorsFallbackLauncherPathInsideFhsEnvironmentRootfs" ]; then
        return 1
      fi

      ${pkgs.coreutils}/bin/readlink -f "$onlyofficeDesktopEditorsFallbackLauncherPathInsideFhsEnvironmentRootfs"
    }

    _didOnlyofficeDesktopEditorsFailWithBwrapUserNamespacePermissions() {
      local onlyofficeDesktopEditorsStartupErrorOutputFilePath="$1"

      ${pkgs.gnugrep}/bin/grep -qE 'bwrap:.*(uid map|new namespace|Permission denied|Operation not permitted)' "$onlyofficeDesktopEditorsStartupErrorOutputFilePath"
    }

    _runOnlyofficeDesktopEditorsBridgeMain() {
      local onlyofficeDesktopEditorsStartupErrorOutputFilePath=""
      local onlyofficeDesktopEditorsBwrapLauncherExitCode=0
      local onlyofficeDesktopEditorsFallbackLauncherPath=""

      onlyofficeDesktopEditorsStartupErrorOutputFilePath="$(${pkgs.coreutils}/bin/mktemp -t onlyoffice-desktopeditors-bridge.XXXXXX)"
      trap '${pkgs.coreutils}/bin/rm -f "$onlyofficeDesktopEditorsStartupErrorOutputFilePath"' EXIT

      "$onlyofficeDesktopEditorsDefaultLauncherPath" "$@" \
        2> >(${pkgs.coreutils}/bin/tee "$onlyofficeDesktopEditorsStartupErrorOutputFilePath" >&2) \
        || onlyofficeDesktopEditorsBwrapLauncherExitCode=$?

      if [ "$onlyofficeDesktopEditorsBwrapLauncherExitCode" -eq 0 ]; then
        return 0
      fi

      if ! _didOnlyofficeDesktopEditorsFailWithBwrapUserNamespacePermissions "$onlyofficeDesktopEditorsStartupErrorOutputFilePath"; then
        return "$onlyofficeDesktopEditorsBwrapLauncherExitCode"
      fi

      onlyofficeDesktopEditorsFallbackLauncherPath="$(_resolveOnlyofficeDesktopEditorsFallbackLauncherPath)" || {
        printf '%s\n' "onlyoffice-desktopeditors-bridge could not resolve a direct fallback launcher from bwrap metadata." >&2
        return "$onlyofficeDesktopEditorsBwrapLauncherExitCode"
      }

      exec "$onlyofficeDesktopEditorsFallbackLauncherPath" "$@"
    }

    _runOnlyofficeDesktopEditorsBridgeMain "$@"
  '';

  onlyofficeDesktopEditorsDesktopEntryTextWithBridgeLauncher =
    builtins.replaceStrings
      [
        "Exec=${pkgs.onlyoffice-desktopeditors}/bin/onlyoffice-desktopeditors %U"
        "Exec=${pkgs.onlyoffice-desktopeditors}/bin/onlyoffice-desktopeditors --new:word"
        "Exec=${pkgs.onlyoffice-desktopeditors}/bin/onlyoffice-desktopeditors --new:cell"
        "Exec=${pkgs.onlyoffice-desktopeditors}/bin/onlyoffice-desktopeditors --new:slide"
        "Exec=${pkgs.onlyoffice-desktopeditors}/bin/onlyoffice-desktopeditors --new:form"
      ]
      [
        "Exec=onlyoffice-desktopeditors-bridge %U"
        "Exec=onlyoffice-desktopeditors-bridge --new:word"
        "Exec=onlyoffice-desktopeditors-bridge --new:cell"
        "Exec=onlyoffice-desktopeditors-bridge --new:slide"
        "Exec=onlyoffice-desktopeditors-bridge --new:form"
      ]
      (
        builtins.readFile "${pkgs.onlyoffice-desktopeditors}/share/applications/onlyoffice-desktopeditors.desktop"
      );
in
{
  home.packages = [ onlyofficeDesktopEditorsBridgeLauncherPackage ];

  home.file.".local/share/applications/onlyoffice-desktopeditors.desktop".text =
    onlyofficeDesktopEditorsDesktopEntryTextWithBridgeLauncher;
}
