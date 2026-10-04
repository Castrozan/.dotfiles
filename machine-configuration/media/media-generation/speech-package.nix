{ pkgs }:
let
  speechPython = pkgs.python312.withPackages (import ./speech-python-packages.nix);
  phonemizerEspeak = pkgs.espeak-ng.override { mbrolaSupport = false; };
  model = pkgs.fetchurl {
    url = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx";
    hash = "sha256-bnQhcNMJAW5YkamU4c4VWccCoszQB15n73FXl09kBss=";
  };
  voices = pkgs.fetchurl {
    url = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin";
    hash = "sha256-vKYQuDCOjZnzLm/kGX5+wBZ5Jk7+0MrJFA/pwp8fv30=";
  };
in
pkgs.writeShellScriptBin "media-speech" ''
  export MEDIA_KOKORO_MODEL=${model}
  export MEDIA_KOKORO_VOICES=${voices}
  export MEDIA_ESPEAK_LIBRARY=${phonemizerEspeak}/lib/libespeak-ng${pkgs.stdenv.hostPlatform.extensions.sharedLibrary}
  export MEDIA_ESPEAK_DATA=${phonemizerEspeak}/share/espeak-ng-data
  exec ${speechPython}/bin/python3 ${./scripts}/media_speech_cli.py "$@"
''
