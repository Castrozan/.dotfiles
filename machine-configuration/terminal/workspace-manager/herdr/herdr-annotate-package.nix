{ pkgs, lib }:
let
  release = {
    aarch64-darwin = {
      target = "aarch64-apple-darwin";
      annotationHash = "sha256-IjQ5Khzt9LCwVhtMpU2nWqUTnfKW29Tlk3HPf6IB+rc=";
      reviewHash = "sha256-fQV/Oho6ojywpEhD/tPwTUmKHaUhl83sAhLG+OFhjLI=";
    };
    x86_64-linux = {
      target = "x86_64-unknown-linux-gnu";
      annotationHash = "sha256-P1cRHCOtcGIWP2FkxWQrdJMJ08xZdDC+He8I3A2r1xI=";
      reviewHash = "sha256-+qZROtGkdXooYelVcBaPLIEY8hm36NalF1oAj+I0/gs=";
    };
  };
  platformRelease = release.${pkgs.stdenv.hostPlatform.system};
in
pkgs.stdenv.mkDerivation {
  pname = "herdr-annotate";
  version = "0.4.0";

  src = pkgs.fetchFromGitHub {
    owner = "plannotator";
    repo = "herdr-annotate";
    rev = "7c8f5a177b8285dc56efc471ef04f7ab44a2b4b6";
    hash = "sha256-f+/2mDs8d5JICqbwzC7/tIYdLlb8NPJuV00Odp4CMSU=";
  };

  annotationRuntime = pkgs.fetchurl {
    url = "https://github.com/plannotator/herdr-annotate/releases/download/rust-lite-v0.1.0/herdr-annotate-${platformRelease.target}";
    hash = platformRelease.annotationHash;
  };
  reviewRuntime = pkgs.fetchurl {
    url = "https://github.com/plannotator/plannotator-tui/releases/download/v0.8.0/plannotator-tui-${platformRelease.target}";
    hash = platformRelease.reviewHash;
  };

  nativeBuildInputs = [
    pkgs.makeWrapper
  ]
  ++ lib.optional pkgs.stdenv.hostPlatform.isLinux pkgs.autoPatchelfHook;
  buildInputs = lib.optional pkgs.stdenv.hostPlatform.isLinux pkgs.stdenv.cc.cc.lib;
  runtimePath = lib.makeBinPath (
    [ pkgs.bash ]
    ++ lib.optionals pkgs.stdenv.hostPlatform.isLinux [
      pkgs.wl-clipboard
      pkgs.xclip
    ]
  );

  dontConfigure = true;
  dontBuild = true;
  dontStrip = true;
  installPhase = builtins.readFile ./scripts/install-herdr-annotate.sh;

  doInstallCheck = true;
  installCheckPhase = ''
    runHook preInstallCheck
    "$out/bin/herdr-annotate" --version
    "$out/bin/plannotator-tui" --version
    runHook postInstallCheck
  '';

  meta = {
    description = "Terminal annotations and document review for Herdr";
    homepage = "https://github.com/plannotator/herdr-annotate";
    license = lib.licenses.mit;
    platforms = builtins.attrNames release;
  };
}
