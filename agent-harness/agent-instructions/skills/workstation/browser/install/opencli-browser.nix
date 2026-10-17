{ pkgs }:
if pkgs.stdenv.isLinux then
  pkgs.chromium
else
  let
    release =
      {
        aarch64-darwin = {
          platform = "mac-arm64";
          hash = "sha256-E7npjOVvXOGOEAoAn0VckoXzmefJ3Ip2/fLzqXVbtfI=";
        };
        x86_64-darwin = {
          platform = "mac-x64";
          hash = "sha256-2AWhcxGNql9vXPRkUAeJ4eAAIqmmrtir/sghq4KPqGI=";
        };
      }
      .${pkgs.stdenv.hostPlatform.system};
  in
  pkgs.stdenvNoCC.mkDerivation {
    pname = "opencli-chromium";
    version = "155.0.8059.84";
    src = pkgs.fetchurl {
      url = "https://storage.googleapis.com/chrome-for-testing-public/155.0.8059.84/${release.platform}/chrome-${release.platform}.zip";
      inherit (release) hash;
    };
    nativeBuildInputs = [
      pkgs.unzip
      pkgs.makeWrapper
    ];
    dontConfigure = true;
    dontBuild = true;
    dontFixup = true;
    installPhase = ''
      mkdir -p "$out/lib"
      cp -R "Google Chrome for Testing.app" "$out/lib/"
      makeWrapper "$out/lib/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing" "$out/bin/chromium"
    '';
    meta = {
      description = "Chromium browser for isolated OpenCLI jobs";
      homepage = "https://googlechromelabs.github.io/chrome-for-testing/";
      platforms = pkgs.lib.platforms.darwin;
      mainProgram = "chromium";
    };
  }
