{ config, lib, ... }:

let
  homeDir = config.home.homeDirectory;

  directoriesToScan = [
    "${homeDir}/.config"
    "${homeDir}/.claude"
    "${homeDir}/.openclaw"
    "${homeDir}/.local"
    "${homeDir}/.codex"
  ];

  directoriesToScanAsShellArray = lib.concatStringsSep " " (
    map (dir: ''"${dir}"'') directoriesToScan
  );
in
{
  home.activation.removeStaleNixStoreSymlinks = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    for scanDirectory in ${directoriesToScanAsShellArray}; do
      if [ ! -d "$scanDirectory" ]; then
        continue
      fi

      staleSymlinksFound=$(find "$scanDirectory" -type l -lname '/nix/store/*' ! -exec test -e {} \; -print 2>/dev/null)

      if [ -n "$staleSymlinksFound" ]; then
        echo "$staleSymlinksFound" | while IFS= read -r staleSymlink; do
          echo "Removing stale nix store symlink: $staleSymlink" >&2
          rm -f "$staleSymlink"
        done
      fi
    done

    if [ -d "${homeDir}/.config" ]; then
      find "${homeDir}/.config" -maxdepth 1 -type d -name '*.backup-*' 2>/dev/null | while IFS= read -r backupDirectory; do
        remainingNonDanglingFiles=$(find "$backupDirectory" -not -type l -not -type d -print -quit 2>/dev/null)
        remainingValidSymlinks=$(find "$backupDirectory" -type l -exec test -e {} \; -print -quit 2>/dev/null)

        if [ -z "$remainingNonDanglingFiles" ] && [ -z "$remainingValidSymlinks" ]; then
          echo "Removing empty backup directory with only dangling symlinks: $backupDirectory" >&2
          rm -rf "$backupDirectory"
        fi
      done
    fi
  '';
}
