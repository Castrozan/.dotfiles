{ helpers, ... }:
let
  configuration = helpers.homeManagerTestConfiguration [ ../neovim-home-manager.nix ];
  settings = configuration.neovimConfiguration;
in
{
  domain-editor-neovim-host-settings = helpers.mkEvalCheck "domain-editor-neovim-host-settings" (
    settings.wallpaperThemeDirectory == "/home/test/.config/hypr-theme/current"
    && settings.obsidianWorkspaceName == "Zanoni"
    && settings.obsidianVaultDirectory == "/home/test/vault"
  ) "dotfiles must supply Neovim with the shared theme and Obsidian workspace settings";
}
