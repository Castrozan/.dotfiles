{
  stdenv,
  fetchurl,
  lib,
}:
let
  version = "0.1.2";
  platformReleases = {
    aarch64-darwin = {
      target = "aarch64-apple-darwin";
      hash = "sha256-wxr4nMQpnLmzkWjPU81nlMaRT6V90jLviY0jqP4/lFg=";
    };
    x86_64-linux = {
      target = "x86_64-unknown-linux-musl";
      hash = "sha256-JW4+twwENemJagOWhnx1cruUtMeRPlQcM69oJme/S0o=";
    };
  };
  platformRelease = platformReleases.${stdenv.hostPlatform.system};
in
stdenv.mkDerivation {
  pname = "hex-orchestrator";
  inherit version;

  src = fetchurl {
    url = "https://github.com/k4black/hex/releases/download/v${version}/hex-cli-${platformRelease.target}.tar.xz";
    inherit (platformRelease) hash;
  };

  dontConfigure = true;
  dontBuild = true;
  dontFixup = true;

  installPhase = ''
    runHook preInstall
    install -Dm755 hex "$out/bin/hex-orchestrator"
    runHook postInstall
  '';

  meta = {
    description = "Bounded, resumable workflow runner for coding-agent CLIs";
    homepage = "https://github.com/k4black/hex";
    license = lib.licenses.mit;
    mainProgram = "hex-orchestrator";
    platforms = builtins.attrNames platformReleases;
  };
}
