{ config, inputs, ... }:
{
  imports = [ inputs.neovim.homeManagerModules.default ];

  neovimConfiguration = {
    wallpaperThemeDirectory = "${config.home.homeDirectory}/.config/hypr-theme/current";
    obsidianWorkspaceName = "Zanoni";
    obsidianVaultDirectory = "${config.home.homeDirectory}/vault";
  };
}
