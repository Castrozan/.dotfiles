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

  version = "0.147.0";

  codexUpstreamReleaseDescriptorBySystem = {
    "x86_64-linux" = {
      releaseTargetTriple = "x86_64-unknown-linux-musl";
      sha256 = "sha256-Akbi53ODTgfw+1JJ7W660S5FkeYI+Me7l91qlpBUTDY=";
      buildInputs = with pkgs; [
        openssl
        libcap
        zlib
      ];
    };
    "aarch64-darwin" = {
      releaseTargetTriple = "aarch64-apple-darwin";
      sha256 = "sha256-dZhLgfkqcbDA9LO1ytgOXFcXfk2Mi0seE9twOyDcQ1g=";
      buildInputs = [ ];
    };
  };

  currentHostSystem = codexUpstreamReleaseDescriptorBySystem.${pkgs.stdenv.hostPlatform.system};

  codex-unwrapped = fetchPrebuiltBinary {
    pname = "codex";
    inherit version;
    url = "https://github.com/openai/codex/releases/download/rust-v${version}/codex-${currentHostSystem.releaseTargetTriple}.tar.gz";
    inherit (currentHostSystem) sha256 buildInputs;
    binaryName = "codex";
    archiveBinaryPath = "codex-${currentHostSystem.releaseTargetTriple}";
  };

  interactiveSessionDeveloperInstructionsText = lib.concatStringsSep "\n" [
    (builtins.readFile ../../../agent-harness/agent-instructions/core-rules/communication/interactive-preferences.md)
    (builtins.readFile ../../../agent-harness/agent-instructions/core-rules/communication/enforced-reply-rules.md)
  ];

  interactivePreferencesFile = pkgs.writeText "codex-interactive-session-only-developer-instructions.md" interactiveSessionDeveloperInstructionsText;

  workspaceProfileActivation = import ./workspace-profile-activation.nix {
    inherit pkgs lib interactiveSessionDeveloperInstructionsText;
  };

  inherit (import ../../workspace-profiles/activation/harness-launch-dispatch.nix { inherit lib; })
    mkWorkspaceProfileLaunchDispatch
    ;

  workspaceProfileLaunchDispatch = mkWorkspaceProfileLaunchDispatch {
    inherit (config) agentWorkspaceProfiles;
    inherit (workspaceProfileActivation) activationShellStatementsForProfile;
  };

  codex = pkgs.writeShellScriptBin "codex" ''
    export NPM_CONFIG_PREFIX="/nonexistent"
    codexDeveloperInstructionsFile="${interactivePreferencesFile}"
    workspaceProfileArguments=()
    interactivePreferencesArguments=()
    case "''${1:-}" in
      "" | -* | resume | fork)
        ${workspaceProfileLaunchDispatch}
        interactivePreferencesArguments=(
          -c "developer_instructions=$(cat "$codexDeveloperInstructionsFile")"
        )
        ;;
    esac
    exec ${codex-unwrapped}/bin/codex \
      --model "gpt-5.6-sol" \
      --sandbox "danger-full-access" \
      --ask-for-approval "never" \
      --no-alt-screen \
      "''${interactivePreferencesArguments[@]}" \
      "''${workspaceProfileArguments[@]}" \
      "$@"
  '';
in
{
  options.codex.unwrappedPackage = lib.mkOption {
    type = lib.types.package;
    default = codex-unwrapped;
    readOnly = true;
    description = "The bare upstream codex binary, without the interactive wrapper that injects a model, sandbox mode, approval policy and the human's own developer_instructions. An autonomous harness builds its own full argv and must launch this, because re-passing a flag the wrapper already injected makes codex exit 2.";
  };

  config.home = {
    packages = [ codex ];
    file.".local/bin/codex".source = "${codex}/bin/codex";
  };
}
