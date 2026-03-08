{ pkgs, ... }:
let
  fetchPrebuiltBinary = import ../../lib/fetch-prebuilt-binary.nix { inherit pkgs; };

  gogcli = fetchPrebuiltBinary {
    pname = "gogcli";
    version = "0.11.0";
    url = "https://github.com/steipete/gogcli/releases/download/v0.11.0/gogcli_0.11.0_linux_amd64.tar.gz";
    sha256 = "sha256-ypi6VuKczTcT/nv4Nf3KAK4bl83LewvF45Pn7bQInIQ=";
    binaryName = "gog";
    archiveBinaryPath = "gog";
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
