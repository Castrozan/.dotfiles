let
  selectedThemeName = "kanagawa";

  themesDirectory = ../../../../static/themes;

  themeColorsToml = builtins.fromTOML (
    builtins.readFile (themesDirectory + "/${selectedThemeName}/colors.toml")
  );

  themeIsLight = builtins.pathExists (themesDirectory + "/${selectedThemeName}/light.mode");

  themeBackgroundFileNames = builtins.attrNames (
    builtins.readDir (themesDirectory + "/${selectedThemeName}/backgrounds")
  );

  sortedBackgroundFileNames = builtins.sort (a: b: a < b) themeBackgroundFileNames;

  firstBackgroundFileName = builtins.head sortedBackgroundFileNames;

  selectedWallpaperPath =
    themesDirectory + "/${selectedThemeName}/backgrounds/${firstBackgroundFileName}";
in
{
  name = selectedThemeName;
  colorsToml = themeColorsToml;
  accentHex = themeColorsToml.accent;
  isLight = themeIsLight;
  wallpaperPath = selectedWallpaperPath;
}
