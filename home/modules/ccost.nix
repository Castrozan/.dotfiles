# ccost - Claude API usage tracking and cost analysis
# https://github.com/carlosarraes/ccost
{ pkgs, ... }:
let
  version = "0.2.0";
  sha256 = "0anl8d2qs4ca4h2zkvpqgsvxs1m9abwrsvynz74i13kais1gdmk8";

  ccost = pkgs.stdenv.mkDerivation {
    pname = "ccost";
    inherit version;

    src = pkgs.fetchurl {
      url = "https://github.com/carlosarraes/ccost/releases/download/v${version}/ccost-linux-x86_64";
      sha256 = sha256;
    };

    nativeBuildInputs = [ pkgs.autoPatchelfHook ];
    buildInputs = [ pkgs.stdenv.cc.cc.lib ];

    dontUnpack = true;
    dontStrip = true;

    installPhase = ''
      install -Dm755 $src $out/bin/ccost
    '';
  };
in
{
  home.packages = [ ccost ];
}
