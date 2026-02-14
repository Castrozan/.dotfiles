{ pkgs, latest, ... }:
let
  nodejs = pkgs.nodejs_22;
  version = "0.10.0";
  prefix = "$HOME/.local/share/summarize-npm";

  summarize = pkgs.writeShellScriptBin "summarize" ''
    export PATH="${nodejs}/bin:${latest.yt-dlp}/bin:''${PATH:+:$PATH}"
    export NPM_CONFIG_PREFIX="${prefix}"

    BIN="${prefix}/bin/summarize"

    if [ ! -x "$BIN" ] || ! "$BIN" --version 2>/dev/null | grep -q "${version}"; then
      echo "[nix] Installing summarize ${version}..." >&2
      ${nodejs}/bin/npm install -g "@steipete/summarize@${version}" \
        --prefix "${prefix}" >&2
    fi

    exec "$BIN" "$@"
  '';
in
{
  home.packages = [ summarize ];
}
