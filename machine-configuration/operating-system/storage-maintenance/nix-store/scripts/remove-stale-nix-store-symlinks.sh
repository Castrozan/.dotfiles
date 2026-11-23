# shellcheck shell=bash
scan_seconds_per_directory="$1"
configuration_directory="$2"
shift 2

for scan_directory in "$@"; do
  [[ -d $scan_directory ]] || continue
  timeout "$scan_seconds_per_directory" \
    find "$scan_directory" -type l -lname '/nix/store/*' -xtype l -print -delete 2>/dev/null |
    sed 's/^/Removing stale nix store symlink: /' >&2 || true
done

[[ -d $configuration_directory ]] || exit 0
find "$configuration_directory" -maxdepth 1 -type d -name '*.backup-*' 2>/dev/null |
  while IFS= read -r backup_directory; do
    surviving_entry="$(find "$backup_directory" -not -type d \( -not -type l -o -not -xtype l \) -print -quit 2>/dev/null || true)"
    [[ -z $surviving_entry ]] || continue
    echo "Removing empty backup directory with only dangling symlinks: $backup_directory" >&2
    rm -rf "$backup_directory"
  done
