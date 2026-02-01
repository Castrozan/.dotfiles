# --ignore-scripts skips node-llama-cpp cmake build (unused).
{
  pkgs,
  lib,
  config,
  ...
}:
let
  nodejs = pkgs.nodejs_22;
  version = "2026.1.30";
  prefix = "$HOME/.local/share/openclaw-npm";

  openclaw = pkgs.writeShellScriptBin "openclaw" ''
    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"
    export NPM_CONFIG_PREFIX="${prefix}"
    BIN="${prefix}/bin/openclaw"

    if [ ! -x "$BIN" ] || [ "$("$BIN" --version 2>/dev/null)" != "${version}" ]; then
      echo "[nix] Installing OpenClaw ${version}..." >&2
      ${nodejs}/bin/npm install -g "openclaw@${version}" \
        --prefix "${prefix}" --ignore-scripts >&2
    fi

    exec "$BIN" "$@"
  '';

  ws = config.openclaw.workspace;
  agentDir = ../../../agents/openclaw;

  mdFiles = builtins.filter (name: lib.hasSuffix ".md" name) (
    builtins.attrNames (builtins.readDir agentDir)
  );

  contextFiles = builtins.listToAttrs (
    map (filename: {
      name = "${ws}/${filename}";
      value.text = builtins.readFile (agentDir + "/${filename}");
    }) mdFiles
  );
in
{
  config = {
    home.packages = [
      openclaw
      nodejs
      pkgs.moreutils
    ];

    home.file = contextFiles;
  };
}
