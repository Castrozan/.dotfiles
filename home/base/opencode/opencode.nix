{
  pkgs,
  lib,
  config,
  ...
}:
let
  fetchPrebuiltBinary = import ../../../lib/fetch-prebuilt-binary.nix { inherit pkgs; };
  opencodeGo = import ./go-provider.nix { homeDirectory = config.home.homeDirectory; };

  version = "1.18.11";

  opencodeUpstreamReleaseDescriptorBySystem = {
    "x86_64-linux" = {
      releaseAssetName = "opencode-linux-x64.tar.gz";
      sha256 = "sha256-pN/8wApakyVsa9BqoMmEMgUo9WTbUqH0vs1cfen7WaE=";
      buildInputs = [ ];
    };
    "aarch64-darwin" = {
      releaseAssetName = "opencode-darwin-arm64.zip";
      sha256 = "sha256-GI/2pxa81A4zrGLxf0rsm9dgFk+mos3mb3eaXbSrx84=";
      buildInputs = [ ];
    };
  };

  currentHostSystem = opencodeUpstreamReleaseDescriptorBySystem.${pkgs.stdenv.hostPlatform.system};

  opencode-unwrapped = fetchPrebuiltBinary {
    pname = "opencode";
    inherit version;
    url = "https://github.com/anomalyco/opencode/releases/download/v${version}/${currentHostSystem.releaseAssetName}";
    inherit (currentHostSystem) sha256 buildInputs;
    binaryName = "opencode";
    archiveBinaryPath = "opencode";
  };

  interactivePreferencesFile = pkgs.writeText "opencode-interactive-session-only-instructions.md" (
    builtins.readFile ../../../agents/core_rules/communication/interactive-preferences.md
    + "\n"
    + builtins.readFile ../../../agents/core_rules/communication/enforced-reply-rules.md
  );

  interactiveSessionConfigOverlay =
    pkgs.writeText "opencode-interactive-session-config-overlay.json"
      (
        builtins.toJSON {
          instructions = [ "${interactivePreferencesFile}" ];
        }
      );

  opencode-authenticated = pkgs.writeShellScriptBin "opencode" ''
    opencodeApiKeyFile="${opencodeGo.apiKeyFile}"
    if [ -r "$opencodeApiKeyFile" ]; then
      OPENCODE_API_KEY="$(cat "$opencodeApiKeyFile")"
      export OPENCODE_API_KEY
    fi
    exec ${opencode-unwrapped}/bin/opencode "$@"
  '';

  opencode = pkgs.writeShellScriptBin "opencode" ''
    case "''${1:-}" in
      acp | agent | attach | completion | db | debug | export | github | import | mcp | models | plugin | pr | providers | auth | run | serve | session | stats | uninstall | upgrade | web)
        ;;
      *)
        export OPENCODE_CONFIG="${interactiveSessionConfigOverlay}"
        ;;
    esac
    exec ${opencode-authenticated}/bin/opencode "$@"
  '';
in
{
  options.opencode.unwrappedPackage = lib.mkOption {
    type = lib.types.package;
    default = opencode-authenticated;
    readOnly = true;
    description = "opencode without the interactive wrapper that overlays the human's own reply-shape instructions through OPENCODE_CONFIG, but still exporting OPENCODE_API_KEY from the agenix secret. An autonomous harness sets its own per-agent OPENCODE_CONFIG and must launch this, because the wrapper's overlay would replace it, while a paid opencode-go model still needs the key the plain upstream binary would never read.";
  };

  config.home = {
    packages = [ opencode ];
    file.".local/bin/opencode".source = "${opencode}/bin/opencode";
  };
}
