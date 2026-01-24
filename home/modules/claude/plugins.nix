{ pkgs }:
let
  languageServers = {
    typescript = {
      packages = with pkgs; [
        typescript-language-server
        typescript
      ];
      claudePlugin = "typescript-lsp@claude-plugins-official";
    };
    java = {
      packages = with pkgs; [ jdt-language-server ];
      claudePlugin = "jdtls-lsp@claude-plugins-official";
    };
    nix = {
      packages = with pkgs; [
        nixd
        nixfmt-rfc-style
      ];
      claudePlugin = null;
    };
    bash = {
      packages = with pkgs; [ bash-language-server ];
      claudePlugin = null;
    };
  };

  standalonePlugins = { };

  languageServersWithClaudePlugin = pkgs.lib.filterAttrs (
    _: cfg: cfg.claudePlugin != null
  ) languageServers;

  lspPluginsAsEnabledFormat = pkgs.lib.mapAttrs' (_: cfg: {
    name = cfg.claudePlugin;
    value = true;
  }) languageServersWithClaudePlugin;

  allPackagesFromLanguageServers = pkgs.lib.flatten (
    pkgs.lib.mapAttrsToList (_: cfg: cfg.packages) languageServers
  );

in
{
  packages = allPackagesFromLanguageServers;
  enabledPlugins = lspPluginsAsEnabledFormat // standalonePlugins;
  inherit languageServers standalonePlugins;
}
