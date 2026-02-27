{ pkgs, ... }:
let
  fetchPrebuiltBinary = import ../../../lib/fetch-prebuilt-binary.nix { inherit pkgs; };

  version = "0.104.0";

  codex-unwrapped = fetchPrebuiltBinary {
    pname = "codex";
    inherit version;
    url = "https://github.com/openai/codex/releases/download/rust-v${version}/codex-x86_64-unknown-linux-gnu.tar.gz";
    sha256 = "UvbMt86+HWYg+GdgdqzEzeEFQ6btDszqYlSY3nrhf4g=";
    binaryName = "codex";
    archiveBinaryPath = "codex-x86_64-unknown-linux-gnu";
    buildInputs = with pkgs; [
      openssl
      libcap
      zlib
    ];
  };

  codex = pkgs.writeShellScriptBin "codex" ''
    export NPM_CONFIG_PREFIX="/nonexistent"
    exec ${codex-unwrapped}/bin/codex \
      --model "gpt-5.3-codex" \
      --sandbox "workspace-write" \
      --ask-for-approval "never" \
      "$@"
  '';
in
{
  home.packages = [ codex ];
  home.file.".local/bin/codex".source = "${codex}/bin/codex";
}
