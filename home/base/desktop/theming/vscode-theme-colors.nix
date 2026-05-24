{ pkgs, themeColorsToml }:
let
  vscodeThemeColorCustomizations = {
    "activityBar.background" = themeColorsToml.background;
    "activityBar.foreground" = themeColorsToml.foreground;
    "activityBar.border" = themeColorsToml.color8;
    "activityBarBadge.background" = themeColorsToml.accent;
    "sideBar.background" = themeColorsToml.background;
    "sideBar.foreground" = themeColorsToml.foreground;
    "sideBar.border" = themeColorsToml.color8;
    "sideBarTitle.foreground" = themeColorsToml.foreground;
    "sideBarSectionHeader.background" = themeColorsToml.background;
    "editor.background" = themeColorsToml.background;
    "editor.foreground" = themeColorsToml.foreground;
    "editorGroupHeader.tabsBackground" = themeColorsToml.background;
    "editorGutter.background" = themeColorsToml.background;
    "editorRuler.foreground" = themeColorsToml.color8;
    "tab.activeBackground" = themeColorsToml.background;
    "tab.activeForeground" = themeColorsToml.foreground;
    "tab.inactiveBackground" = themeColorsToml.background;
    "tab.inactiveForeground" = themeColorsToml.color8;
    "tab.border" = themeColorsToml.background;
    "titleBar.activeBackground" = themeColorsToml.background;
    "titleBar.activeForeground" = themeColorsToml.foreground;
    "titleBar.inactiveBackground" = themeColorsToml.background;
    "titleBar.inactiveForeground" = themeColorsToml.color8;
    "titleBar.border" = themeColorsToml.background;
    "statusBar.background" = themeColorsToml.background;
    "statusBar.foreground" = themeColorsToml.foreground;
    "statusBar.border" = themeColorsToml.color8;
    "statusBar.debuggingBackground" = themeColorsToml.color3;
    "statusBar.noFolderBackground" = themeColorsToml.background;
    "panel.background" = themeColorsToml.background;
    "panel.border" = themeColorsToml.color8;
    "panelTitle.activeForeground" = themeColorsToml.foreground;
    "panelTitle.inactiveForeground" = themeColorsToml.color8;
    "terminal.background" = themeColorsToml.background;
    "terminal.foreground" = themeColorsToml.foreground;
    "terminal.ansiBlack" = themeColorsToml.color0;
    "terminal.ansiRed" = themeColorsToml.color1;
    "terminal.ansiGreen" = themeColorsToml.color2;
    "terminal.ansiYellow" = themeColorsToml.color3;
    "terminal.ansiBlue" = themeColorsToml.color4;
    "terminal.ansiMagenta" = themeColorsToml.color5;
    "terminal.ansiCyan" = themeColorsToml.color6;
    "terminal.ansiWhite" = themeColorsToml.color7;
    "terminal.ansiBrightBlack" = themeColorsToml.color8;
    "terminal.ansiBrightRed" = themeColorsToml.color9;
    "terminal.ansiBrightGreen" = themeColorsToml.color10;
    "terminal.ansiBrightYellow" = themeColorsToml.color11;
    "terminal.ansiBrightBlue" = themeColorsToml.color12;
    "terminal.ansiBrightMagenta" = themeColorsToml.color13;
    "terminal.ansiBrightCyan" = themeColorsToml.color14;
    "terminal.ansiBrightWhite" = themeColorsToml.color15;
    "terminalCursor.foreground" = themeColorsToml.cursor;
    "list.activeSelectionBackground" = themeColorsToml.color8;
    "list.activeSelectionForeground" = themeColorsToml.foreground;
    "list.hoverBackground" = themeColorsToml.color8;
    "list.focusBackground" = themeColorsToml.color8;
    "focusBorder" = themeColorsToml.accent;
    "input.background" = themeColorsToml.background;
    "input.foreground" = themeColorsToml.foreground;
    "input.border" = themeColorsToml.color8;
    "dropdown.background" = themeColorsToml.background;
    "dropdown.foreground" = themeColorsToml.foreground;
    "dropdown.border" = themeColorsToml.color8;
    "quickInput.background" = themeColorsToml.background;
    "quickInput.foreground" = themeColorsToml.foreground;
    "badge.background" = themeColorsToml.accent;
    "badge.foreground" = themeColorsToml.foreground;
    "scrollbarSlider.background" = themeColorsToml.color8;
    "scrollbarSlider.hoverBackground" = themeColorsToml.color8;
    "scrollbarSlider.activeBackground" = themeColorsToml.accent;
    "widget.border" = themeColorsToml.color8;
    "widget.shadow" = themeColorsToml.background;
    "breadcrumb.background" = themeColorsToml.background;
    "breadcrumb.foreground" = themeColorsToml.color8;
    "breadcrumb.focusForeground" = themeColorsToml.foreground;
  };

  vscodeColorCustomizationsJsonFile = pkgs.writeText "vscode-theme-color-customizations.json" (
    builtins.toJSON vscodeThemeColorCustomizations
  );

  vscodeSettingsRelativePath =
    if pkgs.stdenv.isDarwin then
      "Library/Application Support/Code/User/settings.json"
    else
      ".config/Code/User/settings.json";
in
''
  VSCODE_SETTINGS_FILE="$HOME/${vscodeSettingsRelativePath}"
  if [ -f "$VSCODE_SETTINGS_FILE" ]; then
    ${pkgs.python312}/bin/python3 ${./inject-vscode-theme-colors.py} "$VSCODE_SETTINGS_FILE" "${vscodeColorCustomizationsJsonFile}"
  fi
''
