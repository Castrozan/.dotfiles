{ pkgs, lib, ... }:
let
  herdrVersion = "0.7.1";

  herdrReleaseAssetForSystem = {
    "x86_64-linux" = {
      asset = "herdr-linux-x86_64";
      hash = "sha256-uWWsr/wsIvVLbmxkr3z46Yo/SsJiJjCgWZxnpLnYplQ=";
    };
    "aarch64-darwin" = {
      asset = "herdr-macos-aarch64";
      hash = "sha256-FvRlPwSR6h59K0a1sCVC8Y4bguiNqvnikAVy5btjTfg=";
    };
    "x86_64-darwin" = {
      asset = "herdr-macos-x86_64";
      hash = "sha256-V4D6B9u5p4155S0guGphAT9sugJmfyC2z4lmMBUJCEY=";
    };
  };

  herdrReleaseAsset = herdrReleaseAssetForSystem.${pkgs.stdenv.hostPlatform.system};

  herdrStaticReleaseBinary = pkgs.stdenvNoCC.mkDerivation {
    pname = "herdr";
    version = herdrVersion;
    src = pkgs.fetchurl {
      url = "https://github.com/ogulcancelik/herdr/releases/download/v${herdrVersion}/${herdrReleaseAsset.asset}";
      hash = herdrReleaseAsset.hash;
    };
    dontUnpack = true;
    dontConfigure = true;
    dontBuild = true;
    dontStrip = true;
    dontPatchELF = true;
    installPhase = ''
      runHook preInstall
      install -Dm755 "$src" "$out/bin/herdr"
      runHook postInstall
    '';
    meta = {
      description = "Agent-native terminal multiplexer, tmux-compatible with native per-agent state and a socket API";
      homepage = "https://herdr.dev";
      license = lib.licenses.agpl3Plus;
      mainProgram = "herdr";
      platforms = builtins.attrNames herdrReleaseAssetForSystem;
    };
  };
in
{
  home.packages = [ herdrStaticReleaseBinary ];

  home.file.".config/herdr/config.toml".source = ../../../.config/herdr/config.toml;
}
