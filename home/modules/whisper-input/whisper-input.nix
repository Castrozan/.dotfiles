{pkgs, ...}: let
  # Fetch whisper-input source directly
  whisper-input-src = pkgs.fetchFromGitHub {
    owner = "castrozan";
    repo = "whisper-input";
    rev = "e58fc51";
    hash = "sha256-PbYRzSbnv2tfCZh283V9XfcmmWFuV3vOSiRdRthm2Q8=";
  };

  # Process wrapper script with substitutions
  wrapperScript = pkgs.writeScript "whisper-input-wrapper.sh" (
    pkgs.lib.replaceStrings
    [
      "@alsaPlugins@"
      "@pulseaudio@"
      "@portaudio@"
      "@dbusLib@"
      "@ccLib@"
      "@ffmpeg@"
      "@libnotify@"
      "@wtype@"
      "@wlClipboard@"
      "@scriptDir@"
    ]
    [
      "${pkgs.alsa-plugins}"
      "${pkgs.pulseaudio}"
      "${pkgs.portaudio}"
      "${pkgs.dbus.lib}"
      "${pkgs.stdenv.cc.cc.lib}"
      "${pkgs.ffmpeg}"
      "${pkgs.libnotify}"
      "${pkgs.wtype}"
      "${pkgs.wl-clipboard}"
      "${whisper-input-src}/src"
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
      "@alsaLibDev@"
      "@alsaLib@"
    ]
    [
      "${pkgs.python311}/bin/python3"
      "${pkgs.portaudio}"
      "${pkgs.dbus.lib}"
      "${pkgs.stdenv.cc.cc.lib}"
      "${pkgs.alsa-lib.dev}"
      "${pkgs.alsa-lib}"
    ]
    (builtins.readFile ./activation.sh)
  );

  # Create the whisper-input package
  whisper-input = pkgs.stdenv.mkDerivation {
    name = "whisper-input";
    buildInputs = [];
    dontUnpack = true;
    dontBuild = true;
    installPhase = ''
      mkdir -p $out/bin
      cp ${wrapperScript} $out/bin/whisper-input
      chmod +x $out/bin/whisper-input
    '';
  };
in {
  home.packages = [
    whisper-input
    pkgs.xdotool
  ];

  # Set up whisper-input environment (similar to dooit.nix pattern)
  home.activation.installWhisperInput = {
    after = [
      "writeBoundary"
      "installPackages"
    ];
    before = [];
    data = builtins.readFile activationScript;
  };
}
