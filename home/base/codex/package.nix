{ pkgs, ... }:
let
  fetchPrebuiltBinary = import ../../../lib/fetch-prebuilt-binary.nix { inherit pkgs; };

  version = "0.142.5";

  codexUpstreamReleaseDescriptorBySystem = {
    "x86_64-linux" = {
      releaseTargetTriple = "x86_64-unknown-linux-musl";
      sha256 = "sha256-BklHXMFh6lyvV3VPzWdyW+r/lrmJpx9NpeebPmcw/oQ=";
      buildInputs = with pkgs; [
        openssl
        libcap
        zlib
      ];
    };
    "aarch64-darwin" = {
      releaseTargetTriple = "aarch64-apple-darwin";
      sha256 = "sha256-BgAvX/inhWizMzubS7pOdu8arIDDz7ThswwFMstI0Z0=";
      buildInputs = [ ];
    };
  };

  currentHostSystem = codexUpstreamReleaseDescriptorBySystem.${pkgs.stdenv.hostPlatform.system};

  codex-unwrapped = fetchPrebuiltBinary {
    pname = "codex";
    inherit version;
    url = "https://github.com/openai/codex/releases/download/rust-v${version}/codex-${currentHostSystem.releaseTargetTriple}.tar.gz";
    inherit (currentHostSystem) sha256 buildInputs;
    binaryName = "codex";
    archiveBinaryPath = "codex-${currentHostSystem.releaseTargetTriple}";
  };

  codex = pkgs.writeShellScriptBin "codex" ''
    export NPM_CONFIG_PREFIX="/nonexistent"
    exec ${codex-unwrapped}/bin/codex \
      --model "gpt-5.5" \
      --sandbox "danger-full-access" \
      --ask-for-approval "never" \
      --no-alt-screen \
      "$@"
  '';
in
{
  home.packages = [ codex ];
  home.file.".local/bin/codex".source = "${codex}/bin/codex";
}
