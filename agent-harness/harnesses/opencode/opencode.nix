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
  opencodeGo = import ./go-provider.nix { inherit (config.home) homeDirectory; };

  version = "1.18.16";

  opencodeUpstreamReleaseDescriptorBySystem = {
    "x86_64-linux" = {
      releaseAssetName = "opencode-linux-x64.tar.gz";
      sha256 = "sha256-KG4HNV3wZzjBkFlVvhW3+8EKexLZMd6TlKb3WXJGdQs=";
      buildInputs = [ ];
    };
    "aarch64-darwin" = {
      releaseAssetName = "opencode-darwin-arm64.zip";
      sha256 = "sha256-HmcMlDQaN0gk3GcAtvOLLLZjS688og5kUITDPOZjkyA=";
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
    lib.concatStringsSep "\n" [
      (builtins.readFile ../../../agent-harness/agent-instructions/skills/humanize/SKILL.md)
      (builtins.readFile ../../../agent-harness/agent-instructions/skills/humanize/community-language.md)
      (builtins.readFile ../../../agent-harness/agent-instructions/skills/humanize/interactive-communication.md)
    ]
  );

  interactiveSessionConfigOverlay =
    pkgs.writeText "opencode-interactive-session-config-overlay.json"
      (
        builtins.toJSON {
          instructions = [ "${interactivePreferencesFile}" ];
        }
      );

  workspaceProfileActivation = import ./workspace-profile-activation.nix {
    inherit pkgs lib interactivePreferencesFile;
  };

  inherit (import ../../workspace-profiles/activation/harness-launch-dispatch.nix { inherit lib; })
    mkWorkspaceProfileLaunchDispatch
    ;

  workspaceProfileLaunchDispatch = mkWorkspaceProfileLaunchDispatch {
    inherit (config) agentWorkspaceProfiles;
    inherit (workspaceProfileActivation) activationShellStatementsForProfile;
  };

  opencode-authenticated = pkgs.writeShellScriptBin "opencode" ''
    opencodeApiKeyFile="${opencodeGo.apiKeyFile}"
    if [ -r "$opencodeApiKeyFile" ]; then
      OPENCODE_API_KEY="$(cat "$opencodeApiKeyFile")"
      export OPENCODE_API_KEY
    fi
    exec ${opencode-unwrapped}/bin/opencode "$@"
  '';

  opencode = pkgs.writeShellScriptBin "opencode" ''
    opencodeConfigOverlayFile="${interactiveSessionConfigOverlay}"

    applyInteractiveSessionOverlay() {
      ${workspaceProfileLaunchDispatch}
      export OPENCODE_CONFIG="$opencodeConfigOverlayFile"
      export AGENT_INTERACTIVE_PREFERENCES_PATH="${interactivePreferencesFile}"
    }

    case "''${1:-}" in
      acp | agent | attach | completion | db | debug | export | github | import | mcp | models | plugin | pr | providers | auth | serve | session | stats | uninstall | upgrade)
        ;;
      run)
        for argument in "$@"; do
          case "$argument" in
            --mini | --mini=*)
              applyInteractiveSessionOverlay
              break
              ;;
          esac
        done
        ;;
      *)
        applyInteractiveSessionOverlay
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
