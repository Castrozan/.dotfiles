{ pkgs, lib, ... }:
let
  nodejs = pkgs.nodejs_22;
  npmPrefix = "$HOME/.local/share/openclaw-npm";
  openclawDistDir = "${npmPrefix}/lib/node_modules/openclaw/dist";

  patchSessionPathResolution = pkgs.writeShellScript "openclaw-patch-session-path" ''
    OPENCLAW_DIST_DIR="${openclawDistDir}"
    [ -d "$OPENCLAW_DIST_DIR" ] || exit 0

    PATCHED_COUNT=0
    for pathsFile in "$OPENCLAW_DIST_DIR"/paths-*.js; do
      [ -f "$pathsFile" ] || continue
      if ${pkgs.gnugrep}/bin/grep -q 'Session file path must be within sessions directory' "$pathsFile" && \
         ! ${pkgs.gnugrep}/bin/grep -q 'path.basename(trimmed)' "$pathsFile"; then
        ${pkgs.gnused}/bin/sed -i 's/if (relative.startsWith("..") || path.isAbsolute(relative)) throw new Error("Session file path must be within sessions directory");/if (relative.startsWith("..") || path.isAbsolute(relative)) { const basename = path.basename(trimmed); if (basename \&\& !basename.startsWith("..") \&\& !path.isAbsolute(basename)) return path.resolve(resolvedBase, basename); throw new Error("Session file path must be within sessions directory"); }/' "$pathsFile"
        PATCHED_COUNT=$((PATCHED_COUNT + 1))
      fi
    done

    if [ "$PATCHED_COUNT" -gt 0 ]; then
      echo "[openclaw-session-patch] Patched $PATCHED_COUNT files (openclaw/openclaw#15565)" >&2
    fi
  '';
in
{
  options.openclaw.sessionPathPatchScript = lib.mkOption {
    type = lib.types.path;
    default = patchSessionPathResolution;
    readOnly = true;
  };

  config.home.activation.openclawSessionPathPatch = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    run ${patchSessionPathResolution}
  '';
}
