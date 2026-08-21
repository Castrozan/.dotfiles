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

  version = "0.148.0";

  codexUpstreamReleaseDescriptorBySystem = {
    "x86_64-linux" = {
      releaseTargetTriple = "x86_64-unknown-linux-musl";
      sha256 = "sha256-Gjb3YvazvvUzu4Y0WtlRdmHC2E1TmWolDPLKidLP7lo=";
      codeModeHostSha256 = "sha256-jm5VmyKPphsY+ywowx7AIGh1ECW8zj8Az2PHlJnVmCk=";
      buildInputs = with pkgs; [
        openssl
        libcap
        zlib
      ];
    };
    "aarch64-darwin" = {
      releaseTargetTriple = "aarch64-apple-darwin";
      sha256 = "sha256-dYkWqjjvp60HagUIMPy+8aftb0Hvrpwczq7vY+Qo/Cs=";
      codeModeHostSha256 = "sha256-EOr1Yuzv7hufF/tgnNjzK28Bh2Z0VVq9LduBli87XjQ=";
      buildInputs = [ ];
    };
  };

  currentHostSystem = codexUpstreamReleaseDescriptorBySystem.${pkgs.stdenv.hostPlatform.system};

  codexReleaseAssetUrl =
    assetName:
    "https://github.com/openai/codex/releases/download/rust-v${version}/${assetName}-${currentHostSystem.releaseTargetTriple}.tar.gz";

  codex-binary = fetchPrebuiltBinary {
    pname = "codex";
    inherit version;
    url = codexReleaseAssetUrl "codex";
    inherit (currentHostSystem) sha256 buildInputs;
    binaryName = "codex";
    archiveBinaryPath = "codex-${currentHostSystem.releaseTargetTriple}";
  };

  codex-code-mode-host = fetchPrebuiltBinary {
    pname = "codex-code-mode-host";
    inherit version;
    url = codexReleaseAssetUrl "codex-code-mode-host";
    sha256 = currentHostSystem.codeModeHostSha256;
    inherit (currentHostSystem) buildInputs;
    binaryName = "codex-code-mode-host";
    archiveBinaryPath = "codex-code-mode-host-${currentHostSystem.releaseTargetTriple}";
  };

  codex-unwrapped = pkgs.runCommand "codex-with-code-mode-host-${version}" { } ''
    mkdir -p $out/bin
    cp ${codex-binary}/bin/codex $out/bin/codex
    cp ${codex-code-mode-host}/bin/codex-code-mode-host $out/bin/codex-code-mode-host
    chmod +x $out/bin/codex $out/bin/codex-code-mode-host
  '';

  interactiveSessionDeveloperInstructionsText = lib.concatStringsSep "\n" [
    (builtins.readFile ../../../agent-harness/agent-instructions/skills/humanize/interactive-communication.md)
    (builtins.readFile ../../../agent-harness/agent-instructions/core-rules/servant-identity.md)
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
        export AGENT_INTERACTIVE_PREFERENCES_PATH="$codexDeveloperInstructionsFile"
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
