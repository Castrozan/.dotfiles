{ pkgs }:
{
  packages = pkgs.lib.optional pkgs.stdenv.hostPlatform.isDarwin (
    import ./computer-use-mcp-package.nix { inherit pkgs; }
  );
}
