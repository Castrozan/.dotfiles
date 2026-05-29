{
  pkgs,
  nodejs,
  chromeDevtoolsMcpNpmPrefix,
  supergatewayNpmPrefix,
}:
let
  chromeDevtoolsMcpVersion = "1.1.1";
  supergatewayVersion = "3.4.3";

  supergatewayPatches = import ./supergateway-patches.nix {
    inherit pkgs supergatewayNpmPrefix;
  };

  chromeDevtoolsMcpPatches = import ./chrome-devtools-mcp-patches.nix {
    inherit pkgs chromeDevtoolsMcpNpmPrefix;
  };

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

  installAndPatchSupergateway = pkgs.writeShellScript "install-and-patch-supergateway" ''
    set -euo pipefail
    ${installNpmPackageScript "supergateway" supergatewayVersion supergatewayNpmPrefix}
    ${supergatewayPatches.patchSupergatewayUnhandledChildResponseRejection}
    ${supergatewayPatches.patchSupergatewayChildKillSigkill}
  '';

  installAndPatchChromeDevtoolsMcp = pkgs.writeShellScript "install-and-patch-chrome-devtools-mcp" ''
    set -euo pipefail
    ${installNpmPackageScript "chrome-devtools-mcp" chromeDevtoolsMcpVersion chromeDevtoolsMcpNpmPrefix}
    ${chromeDevtoolsMcpPatches.patchChromeDevtoolsMcpSilenceUnknownIssueWarnings}
    ${chromeDevtoolsMcpPatches.patchChromeDevtoolsMcpBoundedProtocolTimeout}
    ${chromeDevtoolsMcpPatches.patchChromeDevtoolsMcpIgnoreNetworkEnableTimeout}
    ${chromeDevtoolsMcpPatches.patchChromeDevtoolsMcpIgnoreFrameManagerInitializeTimeout}
  '';
in
{
  installChromeDevtoolsMcpViaNpm = installAndPatchChromeDevtoolsMcp;
  installSupergatewayViaNpm = installAndPatchSupergateway;
}
