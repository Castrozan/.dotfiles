{ pkgs, ... }:
let
  version = "2.1.6";
  platform = "linux-x64";
  sha256 = "e86870ca13cd82d6d4570329a10a1fd68e11645747657afbdee925e26fc3952a";
  bucket = "https://storage.googleapis.com/claude-code-dist-86c565f3-f756-42ad-8dfa-d59b1c096819/claude-code-releases";

  claude-code-unwrapped = pkgs.stdenv.mkDerivation {
    pname = "claude-code-unwrapped";
    inherit version;

    src = pkgs.fetchurl {
      url = "${bucket}/${version}/${platform}/claude";
      sha256 = sha256;
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
