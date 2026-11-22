{ pkgs }:
let
  fetchPrebuiltBinary = import ../../../../repository/nix-library/fetch-prebuilt-binary.nix {
    inherit pkgs;
  };

  version = "0.171.0";

  codexUpstreamReleaseDescriptorBySystem = {
    "x86_64-linux" = {
      releaseTargetTriple = "x86_64-unknown-linux-musl";
      sha256 = "8391d67757496bfd14893eca6cbf0c96994bf2627566ff1f018f70600c9ef6b3";
      buildInputs = with pkgs; [
        openssl
        libcap
        zlib
        ncurses
      ];
    };
    "aarch64-darwin" = {
      releaseTargetTriple = "aarch64-apple-darwin";
      sha256 = "58c88032ec446e72922d911d8f03773102da20c16a6059cf21f6744bce57f210";
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
