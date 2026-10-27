{
  pkgs,
  lib,
  latest,
  inputs,
}:
let
  fetchPrebuiltBinary = import ../../../repository/nix-library/fetch-prebuilt-binary.nix {
    inherit pkgs;
  };

  version = "0.162.0";

  codexUpstreamReleaseDescriptorBySystem = {
    "x86_64-linux" = {
      releaseTargetTriple = "x86_64-unknown-linux-musl";
      sha256 = "4f573944c1d2059109d75a2f4d0cc9c03697288224a5e407717a9de98fc010c5";
      buildInputs = with pkgs; [
        openssl
        libcap
        zlib
        ncurses
      ];
    };
    "aarch64-darwin" = {
      releaseTargetTriple = "aarch64-apple-darwin";
      sha256 = "5809ee90a9c3b59d438bb2663aefa0b43d86f825438b65d4504b31f82343628b";
      buildInputs = [ ];
    };
  };

  currentHostSystem = codexUpstreamReleaseDescriptorBySystem.${pkgs.stdenv.hostPlatform.system};

  codexReleaseAssetUrl =
    assetName:
    "https://github.com/openai/codex/releases/download/rust-v${version}/${assetName}-${currentHostSystem.releaseTargetTriple}.tar.gz";

  codexReleasePackage = fetchPrebuiltBinary {
    pname = "codex";
    inherit version;
    url = codexReleaseAssetUrl "codex-package";
    inherit (currentHostSystem) sha256 buildInputs;
    archivePrefixToInstall = ".";
    preserveCodeSignature = pkgs.stdenv.hostPlatform.isDarwin;
    meta.mainProgram = "codex";
  };
in
import ./status-line/package.nix {
  inherit
    latest
    lib
    inputs
    version
    ;
  releasePackage = codexReleasePackage;
}
