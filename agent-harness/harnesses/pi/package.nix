{
  pkgs,
  lib,
  config,
  ...
}:
let
  fetchPrebuiltBinary = import ../../../repository/nix-library/fetch-prebuilt-binary.nix {
    inherit pkgs;
  };

  version = "1.1.0";

  piUpstreamReleaseDescriptorBySystem = {
    "x86_64-linux" = {
      releaseAssetName = "pi-linux-x64.tar.gz";
      sha256 = "sha256-P6qUZmzThJ03rzIP90lAfQJxsHqblPQgyH4whm4Q4ok=";
      buildInputs = [ pkgs.xorg.libxcb ];
    };
    "aarch64-darwin" = {
      releaseAssetName = "pi-darwin-arm64.tar.gz";
      sha256 = "sha256-NFWxPeNcFaWJPN68kiZ4GZ6Qp86ZsGy8I/N4YOkNY8c=";
      buildInputs = [ ];
    };
  };

  currentHostSystem = piUpstreamReleaseDescriptorBySystem.${pkgs.stdenv.hostPlatform.system};

  pi-unwrapped = fetchPrebuiltBinary {
    pname = "pi-coding-agent";
    inherit version;
    url = "https://github.com/earendil-works/pi/releases/download/v${version}/${currentHostSystem.releaseAssetName}";
    inherit (currentHostSystem) sha256 buildInputs;
    binaryName = "pi";
    archivePrefixToInstall = "pi";
  };

  searchToolsThePiFileToolsShellOutTo = lib.makeBinPath [
    pkgs.ripgrep
    pkgs.fd
  ];

  interactivePreferencesFile = import ./interactive-instructions.nix {
    inherit pkgs;
    inherit (config.home) homeDirectory;
  };

  pi = pkgs.writeShellScriptBin "pi" ''
    export PATH="${searchToolsThePiFileToolsShellOutTo}:$PATH"
    export PI_SKIP_VERSION_CHECK="''${PI_SKIP_VERSION_CHECK:-1}"
    export PI_TELEMETRY="''${PI_TELEMETRY:-0}"
    export PI_UNWRAPPED_BINARY="${pi-unwrapped}/pi"
    export PI_INTERACTIVE_REPLY_RULES_FILE="${interactivePreferencesFile}"
    export PI_HUMAN_REPLY_GUARD_EXTENSION="${config.agentPlugins.bundle}/plugin/native/pi/human-facing-reply-guard.js"
    exec ${pkgs.bash}/bin/bash ${./scripts/launch-pi-with-the-interactive-reply-rules.sh} "$@"
  '';
in
{
  options.pi.package = lib.mkOption {
    type = lib.types.package;
    default = pi;
    readOnly = true;
    description = "The pi coding agent package used across all pi modules. Its upstream release is a directory of sidecar assets around a Bun single-file executable rather than one relocatable binary, so the store path holds the unpacked release and this wrapper is what puts a `pi` on PATH.";
  };

  config.home = {
    packages = [ pi ];
    file.".local/bin/pi".source = "${pi}/bin/pi";
  };
}
