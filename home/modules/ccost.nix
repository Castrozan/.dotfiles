{ pkgs, ... }:
let
  fetchPrebuiltBinary = import ../../lib/fetch-prebuilt-binary.nix { inherit pkgs; };

  version = "0.2.0";

  ccost = fetchPrebuiltBinary {
    pname = "ccost";
    inherit version;
    url = "https://github.com/carlosarraes/ccost/releases/download/v${version}/ccost-linux-x86_64";
    sha256 = "0anl8d2qs4ca4h2zkvpqgsvxs1m9abwrsvynz74i13kais1gdmk8";
  };
in
{
  home.packages = [ ccost ];
}
