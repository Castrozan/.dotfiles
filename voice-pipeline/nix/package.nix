{ pkgs, ... }:
let
  python = pkgs.python312;
  prefix = "$HOME/.local/share/voice-pipeline-venv";

  voicePipeline = pkgs.writeShellScriptBin "voice-pipeline" ''
    export PATH="${python}/bin:${pkgs.portaudio}/lib:''${PATH:+:$PATH}"
    export LD_LIBRARY_PATH="${pkgs.portaudio}/lib:${
      pkgs.lib.makeLibraryPath [ pkgs.stdenv.cc.cc.lib ]
    }:''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
    VENV="${prefix}"

    if [ ! -d "$VENV" ]; then
      echo "[voice-pipeline] Creating virtualenv..." >&2
      ${python}/bin/python -m venv "$VENV" >&2
    fi

    if [ ! -f "$VENV/.installed" ] || [ "$VENV/.installed" -ot "${../pyproject.toml}" ]; then
      echo "[voice-pipeline] Installing dependencies..." >&2
      "$VENV/bin/pip" install --quiet --upgrade pip >&2
      "$VENV/bin/pip" install --quiet "${../.}" >&2
      touch "$VENV/.installed"
    fi

    exec "$VENV/bin/voice-pipeline" "$@"
  '';
in
{
  home.packages = [
    voicePipeline
    pkgs.portaudio
  ];
}
