let
  selectedThemeName = "kanagawa";

  themesDirectory = ./themes;

  themeColorsToml = builtins.fromTOML (
    builtins.readFile (themesDirectory + "/${selectedThemeName}/colors.toml")
  );

  themeIsLight = builtins.pathExists (themesDirectory + "/${selectedThemeName}/light.mode");

  themeBackgroundFileNames = builtins.attrNames (
    builtins.readDir (themesDirectory + "/${selectedThemeName}/backgrounds")
  );

  sortedBackgroundFileNames = builtins.sort (a: b: a < b) themeBackgroundFileNames;

  firstBackgroundFileName = builtins.head sortedBackgroundFileNames;

  selectedWallpaperPath = builtins.path {
    path = themesDirectory + "/${selectedThemeName}/backgrounds/${firstBackgroundFileName}";
    name = "${selectedThemeName}-wallpaper-${firstBackgroundFileName}";
  };

  selectedColorsTomlPath = builtins.path {
    path = themesDirectory + "/${selectedThemeName}/colors.toml";
    name = "${selectedThemeName}-colors.toml";
  };
in
{
  name = selectedThemeName;
  colorsToml = themeColorsToml;
  colorsTomlPath = selectedColorsTomlPath;
  accentHex = themeColorsToml.accent;
  isLight = themeIsLight;
  wallpaperPath = selectedWallpaperPath;
}
