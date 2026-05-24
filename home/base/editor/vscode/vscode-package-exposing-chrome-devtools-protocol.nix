{
  pkgs,
  lib,
  basePackage,
  chromeDevToolsProtocolPort,
}:
let
  innerCodeBinaryWithChromeDevToolsProtocolFlagsName = "code-with-chrome-devtools-protocol-flags";

  electronUnknownOptionWarningPattern = "^Warning: '(remote-debugging-port|remote-allow-origins)' is not in the list of known options, but still passed to Electron/Chromium\\.$";

  codeFilteringElectronUnknownOptionWarnings = pkgs.writeShellScript "code-filtering-electron-unknown-option-warnings" ''
    exec "$(dirname "$0")/${innerCodeBinaryWithChromeDevToolsProtocolFlagsName}" "$@" 2> >(${pkgs.gnugrep}/bin/grep --line-buffered --invert-match --extended-regexp ${lib.escapeShellArg electronUnknownOptionWarningPattern} >&2)
  '';
in
pkgs.symlinkJoin {
  name = "vscode-with-chrome-devtools-protocol-${basePackage.version}";
  paths = [ basePackage ];
  nativeBuildInputs = [ pkgs.makeWrapper ];
  postBuild = ''
    wrapProgram $out/bin/code \
      --add-flags "--remote-debugging-port=${chromeDevToolsProtocolPort}" \
      --add-flags "--remote-allow-origins=*"

    mv $out/bin/code $out/bin/${innerCodeBinaryWithChromeDevToolsProtocolFlagsName}
    install -m 0755 ${codeFilteringElectronUnknownOptionWarnings} $out/bin/code
  '';
}
