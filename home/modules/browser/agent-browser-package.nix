{ pkgs }:
let
  packageVersion = "0.21.4";
  nativeBinarySource = pkgs.fetchurl {
    url = "https://github.com/vercel-labs/agent-browser/releases/download/v${packageVersion}/agent-browser-linux-x64";
    hash = "sha256-x0qbmJTccs3UDA7leFScV9pIux+o6tBMqXWmVscx5D4=";
  };
in
pkgs.stdenvNoCC.mkDerivation {
  pname = "agent-browser";
  version = packageVersion;
  dontUnpack = true;
  installPhase = ''
    runHook preInstall
    mkdir -p "$out/bin"
    cp ${nativeBinarySource} "$out/bin/agent-browser"
    chmod +x "$out/bin/agent-browser"
    runHook postInstall
  '';

  meta = {
    description = "Browser automation CLI for AI agents (native Rust)";
    homepage = "https://github.com/vercel-labs/agent-browser";
    mainProgram = "agent-browser";
  };
}
