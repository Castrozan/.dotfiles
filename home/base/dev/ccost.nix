{ pkgs, ... }:
let
  fetchPrebuiltBinary = import ../../../lib/fetch-prebuilt-binary.nix { inherit pkgs; };

  version = "0.2.0";

  inherit (pkgs.stdenv.hostPlatform) system isDarwin;

  prebuiltBinaryBySystem = {
    "x86_64-linux" = {
      assetName = "ccost-linux-x86_64";
      sha256 = "0anl8d2qs4ca4h2zkvpqgsvxs1m9abwrsvynz74i13kais1gdmk8";
    };
    "aarch64-darwin" = {
      assetName = "ccost-darwin-aarch64";
      sha256 = "0kij0aw0lqcpjq8ly0272sv3szla4zymmycfbnb5gdqvinvlw1b5";
    };
    "x86_64-darwin" = {
      assetName = "ccost-darwin-x86_64";
      sha256 = "1v6wxjifc3g8nkznxi7vadxrgzp01jn15bk3bkh5k1j3v3647zir";
    };
  };

  prebuiltBinaryForCurrentSystem =
    prebuiltBinaryBySystem.${system}
      or (throw "ccost: no prebuilt binary published for system ${system}");

  ccost = fetchPrebuiltBinary {
    pname = "ccost";
    inherit version;
    url = "https://github.com/carlosarraes/ccost/releases/download/v${version}/${prebuiltBinaryForCurrentSystem.assetName}";
    inherit (prebuiltBinaryForCurrentSystem) sha256;
    preserveCodeSignature = isDarwin;
  };
in
{
  home.packages = [ ccost ];
}
