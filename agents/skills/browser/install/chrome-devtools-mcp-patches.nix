{
  pkgs,
  chromeDevtoolsMcpNpmPrefix,
}:
let
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

    ${pkgs.gnused}/bin/sed -i '/handleDevToolsAsPage: true,/a\        protocolTimeout: 300000,' "$TARGET"

    if ! grep -qF 'protocolTimeout: 300000,' "$TARGET"; then
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

  patchChromeDevtoolsMcpIgnoreFrameManagerInitializeTimeout = pkgs.writeShellScript "patch-chrome-devtools-mcp-ignore-frame-manager-initialize-timeout" ''
    set -euo pipefail
    TARGET="${chromeDevtoolsMcpNpmPrefix}/lib/node_modules/chrome-devtools-mcp/build/src/third_party/index.js"

    if [ ! -f "$TARGET" ]; then
      echo "chrome-devtools-mcp bundle missing, skipping patch: $TARGET" >&2
      exit 0
    fi

    PATCHED_LINE='if (isErrorLike$2(error) && (isTargetClosedError(error) || error.message.includes("timed out"))) {'
    UNPATCHED_LINE='if (isErrorLike$2(error) && isTargetClosedError(error)) {'

    if grep -qF "$PATCHED_LINE" "$TARGET"; then
      exit 0
    fi

    if ! grep -qF "$UNPATCHED_LINE" "$TARGET"; then
      echo "chrome-devtools-mcp FrameManager initialize layout changed at $TARGET; refusing to patch blindly" >&2
      exit 1
    fi

    ${pkgs.gnused}/bin/sed -i 's#if (isErrorLike\$2(error) && isTargetClosedError(error)) {#if (isErrorLike\$2(error) \&\& (isTargetClosedError(error) || error.message.includes("timed out"))) {#' "$TARGET"

    if ! grep -qF "$PATCHED_LINE" "$TARGET"; then
      echo "chrome-devtools-mcp ignore-frame-manager-initialize-timeout patch failed at $TARGET" >&2
      exit 1
    fi
  '';
in
{
  inherit
    patchChromeDevtoolsMcpSilenceUnknownIssueWarnings
    patchChromeDevtoolsMcpBoundedProtocolTimeout
    patchChromeDevtoolsMcpIgnoreNetworkEnableTimeout
    patchChromeDevtoolsMcpIgnoreFrameManagerInitializeTimeout
    ;
}
