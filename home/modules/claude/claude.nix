{ pkgs, config, ... }:
let
  version = "2.1.47";
  platform = "linux-x64";
  sha256 = "nEi95nvaJ01lw9ZdpPeOIaRYznIqiVXtzCctMsmMdKM=";
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
  home = {
    packages = [ claude-code ];
    file = {
      ".local/bin/claude".source = "${claude-code}/bin/claude";
      ".claude/skills/aplicacoes-atendimento-triage".source =
        config.lib.file.mkOutOfStoreSymlink "${config.home.homeDirectory}/repo/aplicacoes-atendimento-triage";
      ".claude/skills/sourcebot" = {
        source = ../sourcebot/skill;
        recursive = true;
      };
    };
  };
}
