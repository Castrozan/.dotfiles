{ pkgs, inputs, ... }:
let
  # Process wrapper script with substitutions
  wrapperScript = pkgs.writeScript "whisper-input-wrapper.sh" (
    pkgs.lib.replaceStrings
      [
        "@alsaPlugins@"
        "@pulseaudio@"
        "@portaudio@"
        "@dbusLib@"
        "@ccLib@"
        "@glibc@"
        "@scriptDir@"
      ]
      [
        "${pkgs.alsa-plugins}"
        "${pkgs.pulseaudio}"
        "${pkgs.portaudio}"
        "${pkgs.dbus.lib}"
        "${pkgs.stdenv.cc.cc.lib}"
        "${pkgs.glibc}"
        "${inputs.whisper-input}/src"
      ]
      (builtins.readFile ./wrapper.sh)
  );
  
  # Process activation script with substitutions
  activationScript = pkgs.writeText "whisper-input-activation.sh" (
    pkgs.lib.replaceStrings
      [
        "@pythonBin@"
        "@portaudio@"
        "@dbusLib@"
        "@ccLib@"
        "@glibc@"
        "@alsaLibDev@"
        "@alsaLib@"
      ]
      [
        "${pkgs.python311}/bin/python3"
        "${pkgs.portaudio}"
        "${pkgs.dbus.lib}"
        "${pkgs.stdenv.cc.cc.lib}"
        "${pkgs.glibc}"
        "${pkgs.alsa-lib.dev}"
        "${pkgs.alsa-lib}"
      ]
      (builtins.readFile ./activation.sh)
  );
  
  # Create the whisper-input package
  whisper-input = pkgs.stdenv.mkDerivation {
    name = "whisper-input";
    buildInputs = [ ];
    dontUnpack = true;
    dontBuild = true;
    installPhase = ''
      mkdir -p $out/bin
      cp ${wrapperScript} $out/bin/whisper-input
      chmod +x $out/bin/whisper-input
    '';
  };
in
{
  home.packages = [ whisper-input pkgs.xdotool ];

  # Set up whisper-input environment (similar to dooit.nix pattern)
  home.activation.installWhisperInput = {
    after = [ "writeBoundary" "installPackages" ];
    before = [ ];
    data = builtins.readFile activationScript;
  };
}
