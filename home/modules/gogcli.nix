{ pkgs, ... }:
let
  gogcli = pkgs.stdenv.mkDerivation {
    pname = "gogcli";
    version = "0.11.0";

    src = pkgs.fetchurl {
      url = "https://github.com/steipete/gogcli/releases/download/v0.11.0/gogcli_0.11.0_linux_amd64.tar.gz";
      sha256 = "sha256-ypi6VuKczTcT/nv4Nf3KAK4bl83LewvF45Pn7bQInIQ=";
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
