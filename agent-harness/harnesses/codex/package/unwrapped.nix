{ pkgs }:
let
  fetchPrebuiltBinary = import ../../../../repository/nix-library/fetch-prebuilt-binary.nix {
    inherit pkgs;
  };

  version = "0.167.0";

  codexUpstreamReleaseDescriptorBySystem = {
    "x86_64-linux" = {
      releaseTargetTriple = "x86_64-unknown-linux-musl";
      sha256 = "3bbf75e83de6b58aed28f2cf6e33ad423ec31fd4700a1457b94be557ea5a7c6e";
      buildInputs = with pkgs; [
        openssl
        libcap
        zlib
        ncurses
      ];
    };
    "aarch64-darwin" = {
      releaseTargetTriple = "aarch64-apple-darwin";
      sha256 = "af45ed45d940d7998809622c1c0296d3098ed7d7fad695284422c228bd454517";
      buildInputs = [ ];
    };
  };

  currentHostSystem = codexUpstreamReleaseDescriptorBySystem.${pkgs.stdenv.hostPlatform.system};

  codexReleaseAssetUrl =
    assetName:
    "https://github.com/openai/codex/releases/download/rust-v${version}/${assetName}-${currentHostSystem.releaseTargetTriple}.tar.gz";
in
fetchPrebuiltBinary {
  pname = "codex";
  inherit version;
  url = codexReleaseAssetUrl "codex-package";
  inherit (currentHostSystem) sha256 buildInputs;
  archivePrefixToInstall = ".";
  preserveCodeSignature = pkgs.stdenv.hostPlatform.isDarwin;
  meta.mainProgram = "codex";
}
