{ pkgs, ... }:
let
  fetchPrebuiltBinary = import ../../lib/fetch-prebuilt-binary.nix { inherit pkgs; };

  k9s = fetchPrebuiltBinary {
    pname = "k9s";
    version = "0.50.9";
    url = "https://github.com/derailed/k9s/releases/download/v0.50.9/k9s_linux_amd64.deb";
    sha256 = "048g8bh3likyj03gcqca7wwnj0xmpqh2axrqislipfpr56fqqdyw";
    binaryName = "k9s";
    meta = with pkgs.lib; {
      description = "Kubernetes CLI To Manage Your Clusters In Style!";
      homepage = "https://k9scli.io/";
      license = licenses.asl20;
      platforms = platforms.linux;
    };
  };
in
{
  home = {
    file = {
      ".config/k9s/config.yaml".source = ../../.config/k9s/config.yaml;
      ".config/k9s/aliases.yaml".source = ../../.config/k9s/aliases.yaml;
    };

    packages = [ k9s ];
  };
}
