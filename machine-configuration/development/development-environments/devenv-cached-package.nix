{ pkgs, inputs }:
let
  binaryCache = builtins.fromJSON (builtins.readFile ./devenv-cache.json);
  cachedPackage = builtins.appendContext binaryCache.storePath {
    ${binaryCache.storePath}.path = true;
  };
in
assert pkgs.lib.assertMsg (
  binaryCache.system == pkgs.stdenv.hostPlatform.system
) "The Devenv binary-cache pin must match the target system";
assert pkgs.lib.assertMsg (
  binaryCache.sourceNarHash == inputs.devenv.narHash
) "Update devenv-cache.json when changing the Devenv flake input";
pkgs.symlinkJoin {
  name = "devenv-${binaryCache.version}";
  inherit (binaryCache) version;
  paths = [ cachedPackage ];
  passthru = { inherit binaryCache; };
  meta = {
    description = "Devenv from its pinned signed binary cache";
    homepage = "https://devenv.sh";
    license = pkgs.lib.licenses.asl20;
    mainProgram = "devenv";
    platforms = [ binaryCache.system ];
  };
}
