{
  pkgs,
  themeColorsToml,
  themeIsLight,
  selectedWallpaperPath,
  removeHashFromColor,
}:
{
  enable = true;
  autoEnable = false;

  image = selectedWallpaperPath;
  polarity = if themeIsLight then "light" else "dark";

  base16Scheme = {
    base00 = removeHashFromColor themeColorsToml.background;
    base01 = removeHashFromColor themeColorsToml.color0;
    base02 = removeHashFromColor themeColorsToml.selection_background;
    base03 = removeHashFromColor themeColorsToml.color8;
    base04 = removeHashFromColor themeColorsToml.color7;
    base05 = removeHashFromColor themeColorsToml.foreground;
    base06 = removeHashFromColor themeColorsToml.color15;
    base07 = removeHashFromColor themeColorsToml.cursor;
    base08 = removeHashFromColor themeColorsToml.color1;
    base09 = removeHashFromColor themeColorsToml.color9;
    base0A = removeHashFromColor themeColorsToml.color3;
    base0B = removeHashFromColor themeColorsToml.color2;
    base0C = removeHashFromColor themeColorsToml.color6;
    base0D = removeHashFromColor themeColorsToml.color4;
    base0E = removeHashFromColor themeColorsToml.color5;
    base0F = removeHashFromColor themeColorsToml.accent;
  };

  fonts = {
    monospace = {
      package = pkgs.nerd-fonts.fira-code;
      name = "FiraCode Nerd Font Mono";
    };
    sansSerif = {
      package = pkgs.inter;
      name = "Inter";
    };
    serif = {
      package = pkgs.noto-fonts;
      name = "Noto Serif";
    };
    emoji = {
      package = pkgs.noto-fonts-color-emoji;
      name = "Noto Color Emoji";
    };
    sizes = {
      terminal = 16;
      applications = 14;
      desktop = 12;
      popups = 14;
    };
  };

  opacity = {
    terminal = 1.0;
  };

  targets = {
    kitty.enable = true;
    wezterm.enable = true;
    bat.enable = true;
    btop.enable = true;
    yazi.enable = false;
    lazygit.enable = true;

    tmux.enable = false;
    neovim.enable = false;
    vim.enable = false;
    fzf.enable = false;
  };
}
