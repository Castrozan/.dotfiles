#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
export DOT_ROOT="${DOT_ROOT:-$(pwd)/../.runtime}"
mkdir -p "$DOT_ROOT"
DOT_ROOT=$(cd "$DOT_ROOT" && pwd)
export DOT_ROOT
version=2.35.3
archive="nix-${version}-x86_64-linux.tar.xz"
sha256=6ce3ce3703fdc241b560cba401c5d338042122fe5b1a81e07bf1a623f259eba0
for tool in bwrap python3 curl tar sha256sum git; do command -v "$tool" >/dev/null; done
git -C ../../../.. rev-parse --show-toplevel >/dev/null
[[ $(uname -m) == x86_64 && $(uname -s) == Linux ]]
mkdir -p "$DOT_ROOT/downloads" "$DOT_ROOT/config/nix"
cat > "$DOT_ROOT/config/nix/nix.conf" <<'EOF'
experimental-features = nix-command flakes
sandbox = true
sandbox-fallback = false
build-users-group =
max-jobs = 1
cores = 2
EOF
if ! python3 run.py nix --version >/dev/null 2>&1; then
  curl --fail --location --retry 2 "https://releases.nixos.org/nix/nix-${version}/${archive}" -o "$DOT_ROOT/downloads/${archive}"
  (cd "$DOT_ROOT/downloads"; printf '%s  %s\n' "$sha256" "$archive" | sha256sum --check -; tar -xJf "$archive")
  python3 run.py /bin/sh "$DOT_ROOT/downloads/nix-${version}-x86_64-linux/install" --no-daemon --no-channel-add --no-modify-profile
fi
python3 run.py nix --version
python3 run.py nix eval --expr '1 + 2'
