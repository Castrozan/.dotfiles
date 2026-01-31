# QMD — Quick Markdown Search (on-device search for markdown/notes)
# https://github.com/tobi/qmd
#
# Installs from GitHub into a dedicated prefix on first run.
# Bun is required (provided by Nix).
{ pkgs, ... }:
let
  inherit (pkgs) bun;
  prefix = "$HOME/.local/share/qmd";

  qmd = pkgs.writeShellScriptBin "qmd" ''
    export PATH="${bun}/bin:${pkgs.sqlite.out}/bin:''${PATH:+:$PATH}"
    export LD_LIBRARY_PATH="${pkgs.sqlite.out}/lib:''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
    QMD_DIR="${prefix}"
    QMD_BIN="$QMD_DIR/node_modules/.bin/qmd"

    if [ ! -x "$QMD_BIN" ]; then
      echo "[nix] Installing QMD..." >&2
      mkdir -p "$QMD_DIR"
      cd "$QMD_DIR"
      ${bun}/bin/bun init -y >/dev/null 2>&1 || true
      ${bun}/bin/bun add qmd@github:tobi/qmd >&2
    fi

    exec "$QMD_BIN" "$@"
  '';
in
{
  home.packages = [
    qmd
    bun
  ];
}
