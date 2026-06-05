{
  pkgs,
  config,
  ...
}:
let
  braveUserDataDirectoryRelativeToHome = "Library/Application Support/BraveSoftware/Brave-Browser";

  bravePreferencesOverridesJsonFile = ./preferences-overrides.json;

  braveProfilePreferencesAppliedMarker = "${./scripts/merge-brave-preferences} ${bravePreferencesOverridesJsonFile}";

  mergeBraveDefaultProfilePreferencesScript = ''
    braveUserDataDirectory="$HOME/${braveUserDataDirectoryRelativeToHome}"
    sentinelDirectory="$HOME/.local/state/dotfiles-activation"
    sentinelFile="$sentinelDirectory/brave-preferences-applied"

    # Both the sentinel marker check and the pgrep check are unprotected and run
    # before the "[ -d ]" stat of Brave's Application Support data, which is the
    # access that triggers the macOS "access data from other apps" TCC prompt. The
    # sentinel is written only after the merge actually applies, so a merge that is
    # deferred because Brave is running leaves the sentinel stale and a later
    # rebuild retries it once Brave is closed, without ever prompting meanwhile.
    if [ "$(cat "$sentinelFile" 2>/dev/null)" != "${braveProfilePreferencesAppliedMarker}" ]; then
      if /usr/bin/pgrep -x "Brave Browser" >/dev/null 2>&1; then
        echo "INFO: Brave is running; preference merge deferred, sentinel left stale so a later rebuild retries." >&2
      elif [ -d "$braveUserDataDirectory" ]; then
        if ${pkgs.python312}/bin/python3 \
          ${./scripts/merge-brave-preferences} \
          ${bravePreferencesOverridesJsonFile} \
          "$braveUserDataDirectory"; then
          mkdir -p "$sentinelDirectory"
          printf '%s' "${braveProfilePreferencesAppliedMarker}" >"$sentinelFile"
        else
          braveProfilePreferencesMergeExitStatus=$?
          echo "WARN: Brave preference merge exited $braveProfilePreferencesMergeExitStatus; sentinel left stale so a later rebuild retries." >&2
        fi
      fi
    fi
  '';
in
{
  home.activation.mergeBraveDefaultProfilePreferences = config.lib.dag.entryAfter [
    "writeBoundary"
  ] mergeBraveDefaultProfilePreferencesScript;
}
