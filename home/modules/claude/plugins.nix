{ pkgs }:
let
  languageServers = {
    typescript = {
      packages = with pkgs; [
        typescript-language-server
        typescript
      ];
    };
    java = {
      packages = with pkgs; [ jdt-language-server ];
    };
    nix = {
      packages = with pkgs; [
        nixd
        nixfmt-rfc-style
      ];
    };
    bash = {
      packages = with pkgs; [ bash-language-server ];
    };
  };

  allPackagesFromLanguageServers = pkgs.lib.flatten (
    pkgs.lib.mapAttrsToList (_: cfg: cfg.packages) languageServers
  );

in
{
  packages = allPackagesFromLanguageServers;
  inherit languageServers;
}
