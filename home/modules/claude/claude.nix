{ pkgs, ... }:
let
  version = "2.1.20";
  platform = "linux-x64";
  sha256 = "Tiocc4cezzsTM3a1fe0DMzp6Y4fy0qOmJ5u5Cgf3qUQ=";
  bucket = "https://storage.googleapis.com/claude-code-dist-86c565f3-f756-42ad-8dfa-d59b1c096819/claude-code-releases";

  claude-code-unwrapped = pkgs.stdenv.mkDerivation {
    pname = "claude-code-unwrapped";
    inherit version;

    src = pkgs.fetchurl {
      url = "${bucket}/${version}/${platform}/claude";
      inherit sha256;
    };

    nativeBuildInputs = [ pkgs.autoPatchelfHook ];
    buildInputs = [ pkgs.stdenv.cc.cc.lib ];

    dontUnpack = true;
    dontStrip = true;

    installPhase = ''
      install -Dm755 $src $out/bin/claude
    '';
  };

  claude-code = pkgs.writeShellScriptBin "claude" ''
    export NPM_CONFIG_PREFIX="/nonexistent"
    export DISABLE_AUTOUPDATER=1
    exec ${claude-code-unwrapped}/bin/claude "$@"
  '';
in
{
  home.packages = [ claude-code ];
  home.file.".local/bin/claude".source = "${claude-code}/bin/claude";
}
