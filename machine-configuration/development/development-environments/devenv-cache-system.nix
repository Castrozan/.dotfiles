let
  binaryCache = builtins.fromJSON (builtins.readFile ./devenv-cache.json);
in
{
  nix.settings = {
    extra-substituters = [ binaryCache.cacheUrl ];
    extra-trusted-public-keys = [ binaryCache.publicKey ];
  };
}
