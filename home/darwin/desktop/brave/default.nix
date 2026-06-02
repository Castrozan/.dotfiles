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

    # Skip when the override content is already applied so a normal rebuild never
    # launches python against Brave's protected Application Support data and thus
    # never triggers the macOS "access data from other apps" TCC prompt. The
    # marker check is unprotected and short-circuits before the protected stat.
    if [ "$(cat "$sentinelFile" 2>/dev/null)" != "${braveProfilePreferencesAppliedMarker}" ] && [ -d "$braveUserDataDirectory" ]; then
      ${pkgs.python312}/bin/python3 \
        ${./scripts/merge-brave-preferences} \
        ${bravePreferencesOverridesJsonFile} \
        "$braveUserDataDirectory"
      mkdir -p "$sentinelDirectory"
      printf '%s' "${braveProfilePreferencesAppliedMarker}" >"$sentinelFile"
    fi
  '';
in
{
  home.activation.mergeBraveDefaultProfilePreferences = config.lib.dag.entryAfter [
    "writeBoundary"
  ] mergeBraveDefaultProfilePreferencesScript;
}
