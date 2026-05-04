{
  pkgs,
  nodejs,
  chromeDevtoolsMcpNpmPrefix,
  supergatewayNpmPrefix,
}:
let
  chromeDevtoolsMcpVersion = "0.20.3";
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

  installAndPatchSupergateway = pkgs.writeShellScript "install-and-patch-supergateway" ''
    set -euo pipefail
    ${installNpmPackageScript "supergateway" supergatewayVersion supergatewayNpmPrefix}
    ${patchSupergatewayUnhandledChildResponseRejection}
  '';
in
{
  installChromeDevtoolsMcpViaNpm =
    installNpmPackageScript "chrome-devtools-mcp" chromeDevtoolsMcpVersion
      chromeDevtoolsMcpNpmPrefix;
  installSupergatewayViaNpm = installAndPatchSupergateway;
}
