{ pkgs, ... }:
let
  lib = pkgs.lib;
  version = "0.15.2";

  ollama = pkgs.stdenv.mkDerivation {
    pname = "ollama";
    inherit version;

    # Download the release binary directly
    src = pkgs.fetchurl {
      url = "https://github.com/ollama/ollama/releases/download/v${version}/ollama-linux-amd64.tar.zst";
      hash = "sha256-RF+u48o7l8FY5CyZ5arrtgss7aGBMDl8F/qisk4Vbis=";
    };

    nativeBuildInputs = [
      pkgs.zstd
      pkgs.gnutar
    ];

    dontUnpack = true;
    dontStrip = true;

    installPhase = ''
      runHook preInstall

      # Extract the binary
      mkdir -p $out/bin
      ${pkgs.zstd}/bin/zstd -d $src | ${pkgs.gnutar}/bin/tar -xzf - -C $out/bin --strip-components=1 bin/ollama

      # Make executable
      chmod +x $out/bin/ollama

      runHook postInstall
    '';

    meta = with lib; {
      description = "Get up and running with large language models locally";
      homepage = "https://github.com/ollama/ollama";
      changelog = "https://github.com/ollama/ollama/releases/tag/v${version}";
      license = lib.licenses.mit;
      platforms = lib.platforms.linux;
      mainProgram = "ollama";
    };
  };
in
{
  home.packages = [ ollama ];
  home.file.".local/bin/ollama".source = "${ollama}/bin/ollama";

  # Enable systemd user service
  systemd.user.services.ollama = {
    Unit = {
      Description = "Ollama Service";
      After = [ "network-online.target" ];
    };

    Service = {
      ExecStart = "${ollama}/bin/ollama serve";
      Restart = "always";
      RestartSec = 3;
    };

    Install = {
      WantedBy = [ "default.target" ];
    };
  };
}
