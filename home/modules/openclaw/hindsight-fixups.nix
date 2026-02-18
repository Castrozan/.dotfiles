{
  pkgs,
  config,
  lib,
  ...
}:
let
  homeDir = config.home.homeDirectory;
  nixGlibc = pkgs.glibc;
  nixOpenssl = pkgs.openssl.out;

  patchedClientJsContent = builtins.readFile ./hindsight-client-retain-patch.js;

  hindsightFixupsScript = pkgs.writeShellScript "hindsight-fixups" ''
    set -euo pipefail

    _patch_pgvector_if_needed() {
      local pgInstallDir
      pgInstallDir=$(find "${homeDir}/.pg0/installation" -maxdepth 1 -mindepth 1 -type d 2>/dev/null | head -1)
      if [ -z "$pgInstallDir" ]; then
        echo "[hindsight-fixups] No pg0 installation found, skipping pgvector patch"
        return 0
      fi

      local vectorSo="$pgInstallDir/lib/vector.so"
      if [ ! -f "$vectorSo" ]; then
        echo "[hindsight-fixups] No vector.so found, skipping pgvector patch"
        return 0
      fi

      if ! ${pkgs.binutils}/bin/strings "$vectorSo" | ${pkgs.gnugrep}/bin/grep -qE "GLIBC_2\.(3[89]|[4-9][0-9])"; then
        echo "[hindsight-fixups] pgvector already compatible, skipping"
        return 0
      fi

      local pgConfig="$pgInstallDir/bin/pg_config"
      if [ ! -x "$pgConfig" ]; then
        echo "[hindsight-fixups] No pg_config found, cannot rebuild pgvector" >&2
        return 0
      fi

      echo "[hindsight-fixups] Rebuilding pgvector from source..."
      local buildDir
      buildDir=$(mktemp -d)
      ${pkgs.git}/bin/git clone --depth 1 --branch v0.8.1 \
        https://github.com/pgvector/pgvector.git "$buildDir/pgvector" 2>&1 | tail -1
      cd "$buildDir/pgvector"
      ${pkgs.gnumake}/bin/make PG_CONFIG="$pgConfig" 2>&1 | tail -1
      ${pkgs.gnumake}/bin/make install PG_CONFIG="$pgConfig" 2>&1 | tail -1
      rm -rf "$buildDir"
      echo "[hindsight-fixups] pgvector rebuilt successfully"
    }

    _patch_hindsight_binary_if_needed() {
      local hindsightBin="${homeDir}/.local/bin/hindsight"
      if [ ! -f "$hindsightBin" ]; then
        echo "[hindsight-fixups] No hindsight binary found, skipping patchelf"
        return 0
      fi

      if "$hindsightBin" --version >/dev/null 2>&1; then
        echo "[hindsight-fixups] hindsight binary already works, skipping"
        return 0
      fi

      echo "[hindsight-fixups] Patching hindsight binary with patchelf..."
      ${pkgs.patchelf}/bin/patchelf \
        --set-interpreter "${nixGlibc}/lib/ld-linux-x86-64.so.2" \
        --set-rpath "${nixGlibc}/lib:${nixOpenssl}/lib" \
        "$hindsightBin"
      echo "[hindsight-fixups] hindsight binary patched"
    }

    _patch_client_js_retain_if_needed() {
      local clientJs="${homeDir}/.openclaw/extensions/hindsight-openclaw/dist/client.js"
      if [ ! -f "$clientJs" ]; then
        echo "[hindsight-fixups] No hindsight client.js found, skipping retain patch"
        return 0
      fi

      if ${pkgs.gnugrep}/bin/grep -q "HINDSIGHT_DAEMON_BASE_URL" "$clientJs"; then
        echo "[hindsight-fixups] client.js already patched, skipping"
        return 0
      fi

      echo "[hindsight-fixups] Patching client.js retain to use HTTP API..."
      cp "${homeDir}/.openclaw/extensions/hindsight-openclaw/dist/client.js" \
         "${homeDir}/.openclaw/extensions/hindsight-openclaw/dist/client.js.bak"
      cat ${pkgs.writeText "hindsight-client-patch" patchedClientJsContent} > "$clientJs"
      echo "[hindsight-fixups] client.js patched"
    }

    _patch_pgvector_if_needed
    _patch_hindsight_binary_if_needed
    _patch_client_js_retain_if_needed
  '';
in
{
  config = {
    home.activation.hindsightFixups =
      lib.hm.dag.entryAfter
        [
          "writeBoundary"
          "installOpenclawViaNpm"
        ]
        ''
          run ${hindsightFixupsScript}
        '';
  };
}
