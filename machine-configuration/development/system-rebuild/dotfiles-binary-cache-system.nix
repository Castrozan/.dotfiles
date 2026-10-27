let
  binaryCache = builtins.fromJSON (builtins.readFile ./dotfiles-binary-cache.json);
in
{
  nix.settings = {
    extra-substituters = [ binaryCache.url ];
    extra-trusted-public-keys = [ binaryCache.publicKey ];
  };
}
