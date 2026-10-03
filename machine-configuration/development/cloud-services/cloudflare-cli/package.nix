{ pkgs }:
let
  nodejs = pkgs.nodejs_22;
  nodeModules = pkgs.importNpmLock.buildNodeModules {
    npmRoot = ./runtime;
    inherit nodejs;
  };
in
pkgs.runCommand "cloudflare-cli-1.0.0-beta.12"
  {
    nativeBuildInputs = [ pkgs.makeWrapper ];
    meta = {
      description = "Official Cloudflare command-line interface";
      homepage = "https://github.com/cloudflare/cf";
      license = with pkgs.lib.licenses; [
        asl20
        mit
      ];
      mainProgram = "cf";
      platforms = pkgs.lib.platforms.unix;
    };
  }
  ''
    makeWrapper ${nodejs}/bin/node "$out/bin/cf" \
      --add-flags ${nodeModules}/node_modules/cf/bin/cf
    ln -s cf "$out/bin/cloudflare"
  ''
