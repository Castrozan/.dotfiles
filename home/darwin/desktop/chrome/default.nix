{
  pkgs,
  config,
  ...
}:
let
  chromiumProfilePreferenceMerge = import ../chromium-preferences/profile-preference-merge.nix {
    inherit pkgs;
  };

  chromeGlobalLauncher = import ./chrome-global-launcher.nix { inherit pkgs; };

  installChromeGlobalDefaultBrowserHandlerScript = ./scripts/install-chrome-global-default-browser-handler.sh;
  linkDefaultChromeProfileToChromeGlobalScript = ./scripts/link-default-chrome-profile-to-chrome-global.sh;
  chromeGlobalDefaultBrowserHandlerBundleIdentifier = "com.lucaszanoni.chrome-global-link-handler";
  chromeGlobalDefaultBrowserHandlerApplicationName = "Chrome Global Link Handler";
  chromeGlobalUrlOpenerBinary = "${chromeGlobalLauncher.chromeGlobalUrlOpenerPackage}/bin/open-url-in-chrome-global";
  defaultBrowserHandlerSentinelMarker = "${installChromeGlobalDefaultBrowserHandlerScript} ${chromeGlobalUrlOpenerBinary} ${pkgs.duti}/bin/duti ${chromeGlobalDefaultBrowserHandlerBundleIdentifier} ${chromeGlobalDefaultBrowserHandlerApplicationName}";
in
{
  home = {
    packages = [
      chromeGlobalLauncher.chromeGlobalLauncherPackage
      chromeGlobalLauncher.chromeGlobalUrlOpenerPackage
    ];

    activation = {
      mergeChromeGlobalProfilePreferences =
        config.lib.dag.entryAfter
          [
            "writeBoundary"
          ]
          (
            chromiumProfilePreferenceMerge.mkChromiumProfilePreferenceMergeActivationScript {
              browserDisplayProcessName = "Google Chrome";
              browserUserDataDirectoryRelativeToHome = ".config/chrome-global";
              preferencesOverridesJsonFile = ./preferences-overrides.json;
              sentinelBasename = "chrome-global-preferences-applied";
            }
          );

      linkDefaultChromeProfileToChromeGlobalProfile =
        config.lib.dag.entryAfter
          [
            "writeBoundary"
          ]
          ''
            ${pkgs.bash}/bin/bash ${linkDefaultChromeProfileToChromeGlobalScript} \
              "$HOME/${chromeGlobalLauncher.chromeGlobalUserDataDirectoryRelativeToHome}" \
              "$HOME/Library/Application Support/Google/Chrome" \
              "Google Chrome" || echo "WARN: default Chrome profile symlink step failed; a later rebuild retries." >&2
          '';

      installChromeGlobalDefaultBrowserHandler =
        config.lib.dag.entryAfter
          [
            "writeBoundary"
          ]
          ''
            sentinelDirectory="$HOME/.local/state/dotfiles-activation"
            sentinelFile="$sentinelDirectory/chrome-global-default-browser-handler"

            if [ "$(cat "$sentinelFile" 2>/dev/null)" != "${defaultBrowserHandlerSentinelMarker}" ]; then
              if ${pkgs.bash}/bin/bash ${installChromeGlobalDefaultBrowserHandlerScript} \
                "${chromeGlobalUrlOpenerBinary}" \
                "${pkgs.duti}/bin/duti" \
                "${chromeGlobalDefaultBrowserHandlerBundleIdentifier}" \
                "${chromeGlobalDefaultBrowserHandlerApplicationName}"; then
                mkdir -p "$sentinelDirectory"
                printf '%s' "${defaultBrowserHandlerSentinelMarker}" >"$sentinelFile"
              else
                echo "WARN: chrome-global default-browser handler install failed; sentinel left stale so a later rebuild retries." >&2
              fi
            fi
          '';
    };
  };
}
