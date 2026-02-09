{ pkgs, ... }:
let
  gogcli = pkgs.stdenv.mkDerivation {
    pname = "gogcli";
    version = "0.9.0";

    src = pkgs.fetchurl {
      url = "https://github.com/steipete/gogcli/releases/download/v0.9.0/gogcli_0.9.0_linux_amd64.tar.gz";
      sha256 = "0lwn3mf3s6k4h0qazglrfc1jkrh9zfa4a1z0c3xyb2m4kjjla410";
    };

    sourceRoot = ".";

    nativeBuildInputs = [ pkgs.autoPatchelfHook ];

    installPhase = ''
      install -Dm755 gog $out/bin/gog
    '';

    meta = with pkgs.lib; {
      description = "CLI for Google Suite - Gmail, Calendar, Drive, Sheets, and more";
      homepage = "https://github.com/steipete/gogcli";
      license = licenses.mit;
      platforms = [ "x86_64-linux" ];
    };
  };
in
{
  home.packages = [ gogcli ];
}
