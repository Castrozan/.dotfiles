{ pkgs, lib, ... }:
let
  zathuraColorScheme = {
    background = "#1e1e2e";
    foreground = "#cdd6f4";
    accent = "#89b4fa";
    highlight = "#f38ba8";
    revert = "#a6e3a1";
  };

  zathuraKeybindingsForVimLike = {
    "j" = "scroll down";
    "k" = "scroll up";
    "h" = "scroll left";
    "l" = "scroll right";
    "d" = "scroll half-down";
    "u" = "scroll half-up";
    "J" = "scroll full-down";
    "K" = "scroll full-up";
    "g" = "goto top";
    "G" = "goto bottom";
    "/" = "search forward";
    "?" = "search backward";
    "n" = "search next";
    "N" = "search previous";
    "i" = "recolor";
    "p" = "print";
    "r" = "rotate";
    "R" = "rotate";
  };

  zathuraDocumentDisplaySettings = {
    font = "FiraCode Nerd Font Mono 11";
    pages-per-row = "1";
    first-page-column = "1";
    enable-transparency = "true";
    smoothscroll = "true";
    adjust-open = "width";
    link-zoom = "true";
    link-hadjust = "true";
    show-hidden = "false";
    statusbar-home-tilde = "true";
    render-loading = "false";
    page-padding = "1";
    selection-clipboard = "clipboard";
  };

  zathuraConfiguration = lib.concatStringsSep "\n" (
    [
      "# Color scheme - Catppuccin-inspired"
      "set default-bg \"${zathuraColorScheme.background}\""
      "set default-fg \"${zathuraColorScheme.foreground}\""
      "set statusbar-bg \"${zathuraColorScheme.background}\""
      "set statusbar-fg \"${zathuraColorScheme.foreground}\""
      "set inputbar-bg \"${zathuraColorScheme.background}\""
      "set inputbar-fg \"${zathuraColorScheme.foreground}\""
      "set notification-bg \"${zathuraColorScheme.background}\""
      "set notification-fg \"${zathuraColorScheme.accent}\""
      "set notification-error-bg \"${zathuraColorScheme.background}\""
      "set notification-error-fg \"${zathuraColorScheme.highlight}\""
      "set notification-warning-bg \"${zathuraColorScheme.background}\""
      "set notification-warning-fg \"${zathuraColorScheme.highlight}\""
      "set recolor true"
      "set recolor-lightcolor \"${zathuraColorScheme.background}\""
      "set recolor-darkcolor \"${zathuraColorScheme.foreground}\""
      ""
      "# Document display settings"
    ]
    ++ (lib.mapAttrsToList (
      name: value: "set ${name} \"${toString value}\""
    ) zathuraDocumentDisplaySettings)
    ++ [
      ""
      "# Vim-like keybindings"
    ]
    ++ (lib.mapAttrsToList (key: command: "map ${key} ${command}") zathuraKeybindingsForVimLike)
    ++ [
      ""
      "# Additional keybindings"
      "map <C-c> abort"
      "map <Tab> toggle_index"
      "map <F1> toggle_statusbar"
      "map <F12> exec \"zathura --version\""
    ]
  );
in
{
  home.packages = [ pkgs.zathura ];

  home.file.".config/zathura/zathurarc".text = zathuraConfiguration;
}
