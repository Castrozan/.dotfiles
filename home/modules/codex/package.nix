# codex - OpenAI's CLI coding agent
# https://github.com/openai/codex
{ pkgs, ... }:
let
  version = "0.98.0";
  sha256 = "smZ5dxFkFVdRZRs6Z/v7SLZove/TUsGhVssDU4NJDUA=";

  codex-unwrapped = pkgs.stdenv.mkDerivation {
    pname = "codex";
    inherit version;

    src = pkgs.fetchurl {
      url = "https://github.com/openai/codex/releases/download/rust-v${version}/codex-x86_64-unknown-linux-gnu.tar.gz";
      inherit sha256;
    };

    nativeBuildInputs = [
      pkgs.autoPatchelfHook
      pkgs.gnutar
    ];
    buildInputs = [
      pkgs.stdenv.cc.cc.lib
      pkgs.openssl
      pkgs.libcap
    ];

    dontStrip = true;

    unpackPhase = ''
      tar -xzf $src
    '';

    installPhase = ''
      install -Dm755 codex-x86_64-unknown-linux-gnu $out/bin/codex
    '';
  };

  # Wrapper: pins sane defaults without fighting Codex's app-managed config.toml.
  # Users can override any value via normal CLI flags.
  codex = pkgs.writeShellScriptBin "codex" ''
    export NPM_CONFIG_PREFIX="/nonexistent"
    exec ${codex-unwrapped}/bin/codex \
      --model "gpt-5.3-codex" \
      --sandbox "workspace-write" \
      --ask-for-approval "on-failure" \
      "$@"
  '';
in
{
  home.packages = [ codex ];
  home.file.".local/bin/codex".source = "${codex}/bin/codex";
}

