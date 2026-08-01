{ pkgs, lib, ... }:
let
  fetchPrebuiltBinary = import ../../../lib/fetch-prebuilt-binary.nix { inherit pkgs; };

  version = "1.18.9";

  opencodeUpstreamReleaseDescriptorBySystem = {
    "x86_64-linux" = {
      releaseAssetName = "opencode-linux-x64.tar.gz";
      sha256 = "sha256-oPpLe4vay9AT55pfadQiDTa1Rc0+opa6dl8wFvpQG1s=";
      buildInputs = [ ];
    };
    "aarch64-darwin" = {
      releaseAssetName = "opencode-darwin-arm64.zip";
      sha256 = "sha256-b5mLfau5QluzSP0NiK/rkqFEIncSMc7JsPQ3S5Rzl+Y=";
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

  opencode = pkgs.writeShellScriptBin "opencode" ''
    opencodeApiKeyFile="$HOME/.secrets/opencode-api-key"
    if [ -r "$opencodeApiKeyFile" ]; then
      OPENCODE_API_KEY="$(cat "$opencodeApiKeyFile")"
      export OPENCODE_API_KEY
    fi
    case "''${1:-}" in
      acp | agent | attach | completion | db | debug | export | github | import | mcp | models | plugin | pr | providers | auth | run | serve | session | stats | uninstall | upgrade | web)
        ;;
      *)
        export OPENCODE_CONFIG="${interactiveSessionConfigOverlay}"
        ;;
    esac
    exec ${opencode-unwrapped}/bin/opencode "$@"
  '';
in
{
  options.opencode.unwrappedPackage = lib.mkOption {
    type = lib.types.package;
    default = opencode-unwrapped;
    readOnly = true;
    description = "The bare upstream opencode binary, without the interactive wrapper that overlays the human's own reply-shape instructions through OPENCODE_CONFIG. An autonomous harness sets its own per-agent OPENCODE_CONFIG and must launch this, because the wrapper's overlay would replace it.";
  };

  config.home = {
    packages = [ opencode ];
    file.".local/bin/opencode".source = "${opencode}/bin/opencode";
  };
}
