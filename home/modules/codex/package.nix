{ pkgs, ... }:
let
  fetchPrebuiltBinary = import ../../../lib/fetch-prebuilt-binary.nix { inherit pkgs; };

  version = "0.112.0";

  codex-unwrapped = fetchPrebuiltBinary {
    pname = "codex";
    inherit version;
    url = "https://github.com/openai/codex/releases/download/rust-v${version}/codex-x86_64-unknown-linux-gnu.tar.gz";
    sha256 = "sha256-kBa5ivxOHRA4El5bUDaw16fGC2vPE+2AqjYzXEDXm24=";
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
      --model "gpt-5.4" \
      --sandbox "danger-full-access" \
      --ask-for-approval "never" \
      "$@"
  '';
in
{
  home.packages = [ codex ];
  home.file.".local/bin/codex".source = "${codex}/bin/codex";
}
