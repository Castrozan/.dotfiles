{ pkgs, ... }:
let
  version = "0.15.2";
  sha256 = "sha256-0000000000000000000000000000000000000000000000000000";

  ollama-unwrapped = pkgs.stdenv.mkDerivation {
    pname = "ollama-unwrapped";
    inherit version;

    src = pkgs.fetchurl {
      url = "https://ollama.com/download/ollama-linux-amd64-${version}.tgz";
      inherit sha256;
    };

    dontUnpack = true;
    dontStrip = true;

    installPhase = ''
      mkdir -p $out/bin
      zstd -d $src -o ollama-linux-amd64.tar
      tar -xf ollama-linux-amd64.tar -C $out/bin --strip-components=1 bin/ollama
      chmod +x $out/bin/ollama
    '';
  };

  ollama = pkgs.writeShellScriptBin "ollama" ''
    exec ${ollama-unwrapped}/bin/ollama "$@"
  '';
in
{
  home.packages = [ ollama ];
  home.file.".local/bin/ollama".source = "${ollama}/bin/ollama";

  # Optional: systemd user service
  # systemd.user.services.ollama = {
  #   Unit = {
  #     Description = "Ollama Service";
  #     After = [ "network-online.target" ];
  #   };

  #   Service = {
  #     ExecStart = "${ollama-unwrapped}/bin/ollama serve";
  #     Restart = "always";
  #     RestartSec = 3;
  #   };

  #   Install = {
  #     WantedBy = [ "default.target" ];
  #   };
  # };
}
