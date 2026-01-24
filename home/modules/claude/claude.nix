{ pkgs, ... }:
let
  version = "2.1.19";
  platform = "linux-x64";
  sha256 = "11a8bc2dece1cd7717a4c113883a573095511475545595d2b0e96f188d651e0f";
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
