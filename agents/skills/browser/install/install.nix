{
  pkgs,
  nodejs,
  chromeDevtoolsMcpNpmPrefix,
  supergatewayNpmPrefix,
}:
let
  chromeDevtoolsMcpVersion = "1.1.1";
  supergatewayVersion = "3.4.3";

  installNpmPackageScript =
    name: version: prefix:
    pkgs.writeShellScript "install-${name}" ''
      set -euo pipefail
      export PATH="${nodejs}/bin:''${PATH:+:$PATH}"
      export NPM_CONFIG_PREFIX="${prefix}"

      PACKAGE_JSON="${prefix}/lib/node_modules/${name}/package.json"

      if [ -f "$PACKAGE_JSON" ] && grep -q '"version": "${version}"' "$PACKAGE_JSON"; then
        exit 0
      fi

      install_npm_package() {
        ${nodejs}/bin/npm install -g "${name}@${version}" \
          --prefix "${prefix}" \
          --registry "https://registry.npmjs.org/" \
          --prefer-offline \
          --no-audit \
          --no-fund \
          2>&1
      }

      if ! OUTPUT=$(install_npm_package); then
        echo "npm install ${name}@${version} failed (attempt 1), retrying..." >&2
        sleep 2
        if ! OUTPUT=$(install_npm_package); then
          echo "npm install ${name}@${version} failed after retry: $OUTPUT" >&2
          exit 1
        fi
      fi
    '';

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

  installAndPatchSupergateway = pkgs.writeShellScript "install-and-patch-supergateway" ''
    set -euo pipefail
    ${installNpmPackageScript "supergateway" supergatewayVersion supergatewayNpmPrefix}
    ${patchSupergatewayUnhandledChildResponseRejection}
    ${patchSupergatewayChildKillSigkill}
  '';

  patchChromeDevtoolsMcpSilenceUnknownIssueWarnings = pkgs.writeShellScript "patch-chrome-devtools-mcp-silence-unknown-issue-warnings" ''
    set -euo pipefail
    TARGET="${chromeDevtoolsMcpNpmPrefix}/lib/node_modules/chrome-devtools-mcp/build/src/third_party/index.js"

    if [ ! -f "$TARGET" ]; then
      echo "chrome-devtools-mcp bundle missing, skipping patch: $TARGET" >&2
      exit 0
    fi

    UNPATCHED_LINE='console.warn(`No handler registered for issue code ''${inspectorIssue.code}`);'

    if ! grep -qF "$UNPATCHED_LINE" "$TARGET"; then
      exit 0
    fi

    ${pkgs.gnused}/bin/sed -i 's|console\.warn(`No handler registered for issue code ''${inspectorIssue\.code}`);||' "$TARGET"

    if grep -qF "$UNPATCHED_LINE" "$TARGET"; then
      echo "chrome-devtools-mcp patch failed to remove unknown-issue warn at $TARGET" >&2
      exit 1
    fi
  '';

  patchChromeDevtoolsMcpBoundedProtocolTimeout = pkgs.writeShellScript "patch-chrome-devtools-mcp-bounded-protocol-timeout" ''
    set -euo pipefail
    TARGET="${chromeDevtoolsMcpNpmPrefix}/lib/node_modules/chrome-devtools-mcp/build/src/browser.js"

    if [ ! -f "$TARGET" ]; then
      echo "chrome-devtools-mcp browser.js missing, skipping patch: $TARGET" >&2
      exit 0
    fi

    if grep -qF 'protocolTimeout:' "$TARGET"; then
      exit 0
    fi

    if ! grep -qF 'handleDevToolsAsPage: true,' "$TARGET"; then
      echo "chrome-devtools-mcp browser.js layout changed at $TARGET; refusing to patch blindly" >&2
      exit 1
    fi

    ${pkgs.gnused}/bin/sed -i '/handleDevToolsAsPage: true,/a\        protocolTimeout: 30000,' "$TARGET"

    if ! grep -qF 'protocolTimeout: 30000,' "$TARGET"; then
      echo "chrome-devtools-mcp bounded-protocol-timeout patch failed at $TARGET" >&2
      exit 1
    fi
  '';

  patchChromeDevtoolsMcpIgnoreNetworkEnableTimeout = pkgs.writeShellScript "patch-chrome-devtools-mcp-ignore-network-enable-timeout" ''
    set -euo pipefail
    TARGET="${chromeDevtoolsMcpNpmPrefix}/lib/node_modules/chrome-devtools-mcp/build/src/third_party/index.js"

    if [ ! -f "$TARGET" ]; then
      echo "chrome-devtools-mcp bundle missing, skipping patch: $TARGET" >&2
      exit 0
    fi

    if grep -qF 'error.message.includes("timed out")' "$TARGET"; then
      exit 0
    fi

    if ! grep -qF 'error.message.includes("wasn'\'''t found")' "$TARGET"; then
      echo "chrome-devtools-mcp bundle layout changed at $TARGET; refusing to patch blindly" >&2
      exit 1
    fi

    ${pkgs.gnused}/bin/sed -i 's#includes("wasn\x27t found")#includes("wasn\x27t found") || error.message.includes("timed out")#' "$TARGET"

    if ! grep -qF 'error.message.includes("timed out")' "$TARGET"; then
      echo "chrome-devtools-mcp ignore-network-enable-timeout patch failed at $TARGET" >&2
      exit 1
    fi
  '';

  installAndPatchChromeDevtoolsMcp = pkgs.writeShellScript "install-and-patch-chrome-devtools-mcp" ''
    set -euo pipefail
    ${installNpmPackageScript "chrome-devtools-mcp" chromeDevtoolsMcpVersion chromeDevtoolsMcpNpmPrefix}
    ${patchChromeDevtoolsMcpSilenceUnknownIssueWarnings}
    ${patchChromeDevtoolsMcpBoundedProtocolTimeout}
    ${patchChromeDevtoolsMcpIgnoreNetworkEnableTimeout}
  '';
in
{
  installChromeDevtoolsMcpViaNpm = installAndPatchChromeDevtoolsMcp;
  installSupergatewayViaNpm = installAndPatchSupergateway;
}
