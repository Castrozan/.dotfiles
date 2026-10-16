#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
export DOT_ROOT="${DOT_ROOT:-$(pwd)/../.runtime}"
mkdir -p "$DOT_ROOT"
DOT_ROOT=$(cd "$DOT_ROOT" && pwd)
export DOT_ROOT
./bootstrap.sh
python3 run.py nix build --impure --file build-home.nix --out-link "$DOT_ROOT/result"
# shellcheck disable=SC2016 # Expanded by the inner shell.
python3 run.py /bin/bash -c 'export HOME_MANAGER_BACKUP_EXT=dot-bootstrap-backup; exec "$DOT_ROOT/result/activate"'
