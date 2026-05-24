{
  pkgs,
  config,
  ...
}:
let
  braveUserDataDirectoryRelativeToHome = "Library/Application Support/BraveSoftware/Brave-Browser";

  bravePreferencesOverridesJsonFile = ./preferences-overrides.json;

  mergeBraveDefaultProfilePreferencesScript = ''
    ${pkgs.python312}/bin/python3 \
      ${./scripts/merge-brave-preferences} \
      ${bravePreferencesOverridesJsonFile} \
      "$HOME/${braveUserDataDirectoryRelativeToHome}"
  '';
in
{
  home.activation.mergeBraveDefaultProfilePreferences = config.lib.dag.entryAfter [
    "writeBoundary"
  ] mergeBraveDefaultProfilePreferencesScript;
}
