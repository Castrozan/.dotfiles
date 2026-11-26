{ pkgs }:
let
  fetchPrebuiltBinary = import ../../../../repository/nix-library/fetch-prebuilt-binary.nix {
    inherit pkgs;
  };

  version = "0.172.0";

  codexUpstreamReleaseDescriptorBySystem = {
    "x86_64-linux" = {
      releaseTargetTriple = "x86_64-unknown-linux-musl";
      sha256 = "63e3b00065ed7f62166d0522e17f663cb866a31d80d03e63365482ed34a1d991";
      buildInputs = with pkgs; [
        openssl
        libcap
        zlib
        ncurses
      ];
    };
    "aarch64-darwin" = {
      releaseTargetTriple = "aarch64-apple-darwin";
      sha256 = "0970016d48209a09c4039139629ed79b4a31c5e3d864e792c043419d98fa6466";
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
