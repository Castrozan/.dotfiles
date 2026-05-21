{ pkgs, lib, ... }:
let
  vscodeLinuxPinnedBuild = pkgs.vscode.overrideAttrs (previousAttributes: rec {
    version = "1.119.0";
    src = pkgs.fetchurl {
      name = "VSCode_${version}_linux-x64.tar.gz";
      url = "https://update.code.visualstudio.com/${version}/linux-x64/stable";
      sha256 = "sha256-HcZIRGB0y8U5huxXN9jNrhMD0Jjmn+QNUU60EHGduXo=";
    };
    buildInputs =
      previousAttributes.buildInputs
      ++ (with pkgs; [
        curl
        openssl
        libsoup_3
        webkitgtk_4_1
      ]);
  });

  chromeDevToolsProtocolPort = "9333";

  innerCodeBinaryWithChromeDevToolsProtocolFlagsName = "code-with-chrome-devtools-protocol-flags";

  electronUnknownOptionWarningPattern = "^Warning: '(remote-debugging-port|remote-allow-origins)' is not in the list of known options, but still passed to Electron/Chromium\\.$";

  codeFilteringElectronUnknownOptionWarnings = pkgs.writeShellScript "code-filtering-electron-unknown-option-warnings" ''
    exec "$(dirname "$0")/${innerCodeBinaryWithChromeDevToolsProtocolFlagsName}" "$@" 2> >(${pkgs.gnugrep}/bin/grep --line-buffered --invert-match --extended-regexp ${lib.escapeShellArg electronUnknownOptionWarningPattern} >&2)
  '';

  vscodePackageAlwaysExposingChromeDevToolsProtocol = pkgs.symlinkJoin {
    name = "vscode-with-chrome-devtools-protocol-${vscodeLinuxPinnedBuild.version}";
    paths = [ vscodeLinuxPinnedBuild ];
    nativeBuildInputs = [ pkgs.makeWrapper ];
    postBuild = ''
      wrapProgram $out/bin/code \
        --add-flags "--remote-debugging-port=${chromeDevToolsProtocolPort}" \
        --add-flags "--remote-allow-origins=*"

      mv $out/bin/code $out/bin/${innerCodeBinaryWithChromeDevToolsProtocolFlagsName}
      install -m 0755 ${codeFilteringElectronUnknownOptionWarnings} $out/bin/code
    '';
  };
in
{
  home.packages = [
    vscodePackageAlwaysExposingChromeDevToolsProtocol
  ];
}
