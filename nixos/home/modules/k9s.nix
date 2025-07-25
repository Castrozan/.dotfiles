{ pkgs, ... }:
let
  inherit (pkgs) lib stdenv dpkg;
  k9s = stdenv.mkDerivation rec {
    pname = "k9s";
    version = "0.50.9";

    src = pkgs.fetchurl {
      url = "https://github.com/derailed/k9s/releases/download/v${version}/k9s_linux_amd64.deb";
      sha256 = "048g8bh3likyj03gcqca7wwnj0xmpqh2axrqislipfpr56fqqdyw";
    };

    nativeBuildInputs = [ dpkg ];

    unpackPhase = ''
      dpkg -x $src .
    '';

    installPhase = ''
      mkdir -p $out/bin
      mv usr/bin/k9s $out/bin
    '';

    meta = with lib; {
      description = "Kubernetes CLI To Manage Your Clusters In Style!";
      homepage = "https://k9scli.io/";
      license = licenses.asl20;
      platforms = platforms.linux;
    };
  };
in
{
  home.file.".config/k9s/config.yaml".source = ../../../.config/k9s/config.yaml;
  home.file.".config/k9s/aliases.yaml".source = ../../../.config/k9s/aliases.yaml;

  home.packages = [ k9s ];
}
