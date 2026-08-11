{ pkgs }:
pkgs.stdenvNoCC.mkDerivation {
  pname = "seanime";
  version = "3.10.2";

  src = pkgs.fetchurl {
    url = "https://github.com/5rahim/seanime/releases/download/v3.10.2/seanime-3.10.2_Linux_x86_64.tar.gz";
    hash = "sha256-xTWYBsaaqLMHOwkZLY3eDMZsA6lIHuSKw3xGMkbyn/0=";
  };

  sourceRoot = ".";
  dontConfigure = true;
  dontBuild = true;

  installPhase = ''
    runHook preInstall
    install -Dm755 seanime $out/bin/seanime
    runHook postInstall
  '';
}
