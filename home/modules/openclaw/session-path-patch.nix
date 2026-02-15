# Workaround for openclaw/openclaw#15565 (v2026.2.12)
#
# resolvePathWithinSessionsDir rejects absolute sessionFile paths when the
# agentId used to resolve the sessions directory differs from the owning agent.
# This breaks multi-agent Telegram setups, renamed agents, and any case where
# session entries cross agent boundaries.
#
# The patch adds a basename fallback: when an absolute path fails containment,
# extract just the filename (uuid.jsonl) and resolve it within the current
# agent's sessions dir. The original error is preserved as final fallback.
#
# Remove this module once upstream ships a fix.
{ pkgs, lib, ... }:
let
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
