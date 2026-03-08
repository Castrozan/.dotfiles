#!/usr/bin/env bash

set -Eeuo pipefail

readonly REPOSITORY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

main() {
  echo "=== Nix Module Coverage ==="
  echo ""

  local allNixFiles
  allNixFiles=$(_find_all_nix_files)
  local totalFileCount
  totalFileCount=$(echo "$allNixFiles" | wc -l)

  _print_files_by_directory "$allNixFiles"
  _print_summary "$totalFileCount"
  _find_and_print_orphaned_files "$allNixFiles"

  echo ""
  echo "Note: Nix is declarative - 'coverage' means module usage, not line execution."
  echo "For function-level testing, consider nix-unit."
}

_find_all_nix_files() {
  find "$REPOSITORY_DIR" -name "*.nix" -not -path "*/result/*" -not -path "*/.git/*" | sort
}

_try_resolve_imported_files_via_nix_derivation() {
  echo "Building dependency graph (this may take a moment)..."
  nix path-info --derivation "$REPOSITORY_DIR#homeConfigurations.lucas.zanoni@x86_64-linux.activationPackage" 2>/dev/null |
    xargs nix derivation show 2>/dev/null |
    grep -oP '"'"$REPOSITORY_DIR"'/[^"]+\.nix"' |
    tr -d '"' |
    sort -u
}

_resolve_imported_files_via_grep_heuristic() {
  echo "Using import analysis instead..."
  grep -rh "import \./\|imports = \[" "$REPOSITORY_DIR" --include="*.nix" 2>/dev/null |
    grep -oP '\./[a-zA-Z0-9_/-]+\.nix|\./[a-zA-Z0-9_/-]+(?=/default\.nix)' |
    sort -u
}

_print_files_by_directory() {
  local allNixFiles="$1"
  echo "=== Files by Directory ==="
  echo "$allNixFiles" | while read -r nixFile; do
    dirname "$nixFile" | sed "s|$REPOSITORY_DIR/||"
  done | sort | uniq -c | sort -rn | head -20
}

_print_summary() {
  local totalFileCount="$1"
  echo ""
  echo "=== Summary ==="
  echo "Total .nix files: $totalFileCount"
}

_find_and_print_orphaned_files() {
  local allNixFiles="$1"
  local orphanedFiles=()

  echo ""
  echo "=== Potential Issues ==="

  for nixFile in $allNixFiles; do
    local fileName directoryName
    fileName=$(basename "$nixFile")
    directoryName=$(dirname "$nixFile")

    [[ "$fileName" == "flake.nix" ]] && continue
    [[ "$nixFile" == "$REPOSITORY_DIR/default.nix" ]] && continue

    if [[ "$fileName" == "default.nix" ]]; then
      local parentDirectoryName
      parentDirectoryName=$(basename "$directoryName")
      if ! grep -rq "$parentDirectoryName\|$parentDirectoryName/" "$REPOSITORY_DIR" --include="*.nix" 2>/dev/null; then
        orphanedFiles+=("$nixFile")
      fi
    elif ! grep -rq "$fileName" "$REPOSITORY_DIR" --include="*.nix" 2>/dev/null; then
      orphanedFiles+=("$nixFile")
    fi
  done

  if [[ ${#orphanedFiles[@]} -gt 0 ]]; then
    echo "Potentially unused files (not found in imports):"
    for orphanedFile in "${orphanedFiles[@]}"; do
      echo "  - ${orphanedFile#"$REPOSITORY_DIR/"}"
    done
  else
    echo "All .nix files appear to be imported."
  fi
}

main "$@"
