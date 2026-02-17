{ pkgs, ... }:
let
  inherit (pkgs) bun;
  nodejs = pkgs.nodejs_22;
  sqliteVecPlatformPackageName = "sqlite-vec-linux-x64";
  qmdInstallDirectory = "$HOME/.local/share/qmd";

  qmd = pkgs.writeShellScriptBin "qmd" ''
    export PATH="${nodejs}/bin:${bun}/bin:${pkgs.sqlite.out}/bin:''${PATH:+:$PATH}"
    export LD_LIBRARY_PATH="${pkgs.sqlite.out}/lib:''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
    readonly QMD_INSTALL_DIR="${qmdInstallDirectory}"
    readonly QMD_ENTRYPOINT="$QMD_INSTALL_DIR/node_modules/.bin/qmd"

    if [ ! -x "$QMD_ENTRYPOINT" ]; then
      echo "[nix] Installing QMD..." >&2
      mkdir -p "$QMD_INSTALL_DIR"
      cd "$QMD_INSTALL_DIR"
      ${bun}/bin/bun init -y >/dev/null 2>&1 || true
      ${bun}/bin/bun add qmd@github:tobi/qmd >&2
    fi

    _ensure_sqlite_vec_symlink_exists() {
      local sqlite_vec_platform_package="$QMD_INSTALL_DIR/node_modules/${sqliteVecPlatformPackageName}"
      local sqlite_vec_symlink_in_qmd_package="$QMD_INSTALL_DIR/node_modules/qmd/${sqliteVecPlatformPackageName}"
      if [ -d "$sqlite_vec_platform_package" ] && [ ! -e "$sqlite_vec_symlink_in_qmd_package" ]; then
        ln -s "$sqlite_vec_platform_package" "$sqlite_vec_symlink_in_qmd_package"
      fi
    }
    _ensure_sqlite_vec_symlink_exists

    exec "$QMD_ENTRYPOINT" "$@"
  '';
in
{
  home.packages = [
    qmd
    bun
  ];
}
