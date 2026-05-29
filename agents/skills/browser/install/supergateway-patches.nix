{
  pkgs,
  supergatewayNpmPrefix,
}:
let
  patchSupergatewayUnhandledChildResponseRejection = pkgs.writeShellScript "patch-supergateway-unhandled-child-response-rejection" ''
    set -euo pipefail
    TARGET="${supergatewayNpmPrefix}/lib/node_modules/supergateway/dist/gateways/stdioToStatefulStreamableHttp.js"

    if [ ! -f "$TARGET" ]; then
      echo "supergateway file missing, skipping patch: $TARGET" >&2
      exit 0
    fi

    if grep -qF 'transport.send(jsonMsg).catch(' "$TARGET"; then
      exit 0
    fi

    if ! grep -qF 'transport.send(jsonMsg);' "$TARGET"; then
      echo "supergateway upstream layout changed at $TARGET; refusing to patch blindly" >&2
      exit 1
    fi

    ${pkgs.gnused}/bin/sed -i 's|transport\.send(jsonMsg);|transport.send(jsonMsg).catch((unhandledChildResponseError) => logger.error(`Failed to send to StreamableHttp`, unhandledChildResponseError));|' "$TARGET"
  '';

  patchSupergatewayChildKillSigkill = pkgs.writeShellScript "patch-supergateway-child-kill-sigkill" ''
    set -euo pipefail
    TARGET="${supergatewayNpmPrefix}/lib/node_modules/supergateway/dist/gateways/stdioToStatefulStreamableHttp.js"

    if [ ! -f "$TARGET" ]; then
      echo "supergateway file missing, skipping patch: $TARGET" >&2
      exit 0
    fi

    if grep -qF "child.kill('SIGKILL')" "$TARGET"; then
      exit 0
    fi

    if ! grep -qE 'child\.kill\(\);' "$TARGET"; then
      echo "supergateway upstream layout changed at $TARGET; refusing to patch blindly" >&2
      exit 1
    fi

    ${pkgs.gnused}/bin/sed -i "s|child\.kill();|child.kill('SIGKILL');|g" "$TARGET"

    if grep -qE 'child\.kill\(\);' "$TARGET"; then
      echo "supergateway SIGKILL patch failed to replace all child.kill() calls at $TARGET" >&2
      exit 1
    fi
  '';
in
{
  inherit
    patchSupergatewayUnhandledChildResponseRejection
    patchSupergatewayChildKillSigkill
    ;
}
