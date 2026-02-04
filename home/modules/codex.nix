# codex - OpenAI's CLI coding agent
# https://github.com/openai/codex
{ pkgs, ... }:
let
  version = "0.94.0";
  sha256 = "1qnxwn2vpahp839d749vhcaq7m7bvp9ssa4insh0wilkq01mzw1a";

  codex = pkgs.stdenv.mkDerivation {
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
    ];

    dontStrip = true;

    unpackPhase = ''
      tar -xzf $src
    '';

    installPhase = ''
      install -Dm755 codex-x86_64-unknown-linux-gnu $out/bin/codex
    '';
  };
in
{
  home.packages = [ codex ];
}
