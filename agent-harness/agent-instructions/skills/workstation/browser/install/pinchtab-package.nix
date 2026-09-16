{
  pkgs,
}:
let
  version = "0.13.2";
  inherit (pkgs.stdenv.hostPlatform) system;
  releaseBinaryBySystem = {
    "aarch64-darwin" = {
      asset = "pinchtab-darwin-arm64";
      hash = "sha256-Dy/bvYYaJAfxt95ElmvVuQukJaRtLWp1q57ovsBUPdU=";
    };
    "x86_64-darwin" = {
      asset = "pinchtab-darwin-amd64";
      hash = "sha256-bAr98ZE5yzs2JRGovvORgUG697/t4aHpkYI9z+B9FQE=";
    };
    "x86_64-linux" = {
      asset = "pinchtab-linux-amd64";
      hash = "sha256-ystOX/baA5hjvAG7bG8gvLJnDLCaGHCmZwKbZ+W+z50=";
    };
  };
  selectedReleaseBinary =
    releaseBinaryBySystem.${system} or (throw "pinchtab: unsupported system ${system}");
  pinchtabReleaseBinary = pkgs.fetchurl {
    url = "https://github.com/pinchtab/pinchtab/releases/download/v${version}/${selectedReleaseBinary.asset}";
    inherit (selectedReleaseBinary) hash;
  };
in
pkgs.stdenv.mkDerivation {
  pname = "pinchtab";
  inherit version;

  dontUnpack = true;

  nativeBuildInputs = pkgs.lib.optionals pkgs.stdenv.isLinux [
    pkgs.autoPatchelfHook
  ];
  buildInputs = pkgs.lib.optionals pkgs.stdenv.isLinux [
    pkgs.stdenv.cc.cc.lib
  ];

  installPhase = ''
    runHook preInstall
    install -Dm755 ${pinchtabReleaseBinary} $out/bin/pinchtab
    runHook postInstall
  '';

  meta = {
    description = "PinchTab browser control CLI for AI agents (chromedp, stealth)";
    homepage = "https://github.com/pinchtab/pinchtab";
    mainProgram = "pinchtab";
  };
}
