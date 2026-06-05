{ pkgs }:
let
  mergeChromiumProfilePreferencesScript = ./scripts/merge-chromium-profile-preferences;

  mkChromiumProfilePreferenceMergeActivationScript =
    {
      browserDisplayProcessName,
      browserUserDataDirectoryRelativeToHome,
      preferencesOverridesJsonFile,
      sentinelBasename,
    }:
    let
      preferencesAppliedMarker = "${mergeChromiumProfilePreferencesScript} ${preferencesOverridesJsonFile} ${browserDisplayProcessName}";
    in
    ''
      browserUserDataDirectory="$HOME/${browserUserDataDirectoryRelativeToHome}"
      sentinelDirectory="$HOME/.local/state/dotfiles-activation"
      sentinelFile="$sentinelDirectory/${sentinelBasename}"

      if [ "$(cat "$sentinelFile" 2>/dev/null)" != "${preferencesAppliedMarker}" ]; then
        if /usr/bin/pgrep -x "${browserDisplayProcessName}" >/dev/null 2>&1; then
          echo "INFO: ${browserDisplayProcessName} is running; preference merge deferred, sentinel left stale so a later rebuild retries." >&2
        elif [ -d "$browserUserDataDirectory" ]; then
          if ${pkgs.python312}/bin/python3 \
            ${mergeChromiumProfilePreferencesScript} \
            ${preferencesOverridesJsonFile} \
            "$browserUserDataDirectory" \
            "${browserDisplayProcessName}"; then
            mkdir -p "$sentinelDirectory"
            printf '%s' "${preferencesAppliedMarker}" >"$sentinelFile"
          else
            chromiumProfilePreferenceMergeExitStatus=$?
            echo "WARN: ${browserDisplayProcessName} preference merge exited $chromiumProfilePreferenceMergeExitStatus; sentinel left stale so a later rebuild retries." >&2
          fi
        fi
      fi
    '';
in
{
  inherit mergeChromiumProfilePreferencesScript mkChromiumProfilePreferenceMergeActivationScript;
}
