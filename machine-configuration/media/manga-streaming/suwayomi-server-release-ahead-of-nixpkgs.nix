{ latest }:
let
  releaseVersion = "2.3.2243";
  releaseJarHash = "sha256-ghFBsy4XDUoC08vf7Vd+2PB70iOD/19BMuu1rkDpjdU=";
in
latest.suwayomi-server.overrideAttrs {
  version = releaseVersion;
  src = latest.fetchurl {
    url = "https://github.com/Suwayomi/Suwayomi-Server/releases/download/v${releaseVersion}/Suwayomi-Server-v${releaseVersion}.jar";
    hash = releaseJarHash;
  };
}
