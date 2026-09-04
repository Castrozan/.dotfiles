{
  pkgs,
  lib,
  config,
  latest,
  ...
}:
let
  fetchPrebuiltBinary = import ../../../repository/nix-library/fetch-prebuilt-binary.nix {
    inherit pkgs;
  };

  version = "0.153.2";

  codexUpstreamReleaseDescriptorBySystem = {
    "x86_64-linux" = {
      releaseTargetTriple = "x86_64-unknown-linux-musl";
      codeModeHostSha256 = "sha256-F3pFB7nMf5fxE6wDRpezn2pxqHaovVCP9tf1LzQuvko=";
      buildInputs = with pkgs; [
        openssl
        libcap
        zlib
      ];
    };
    "aarch64-darwin" = {
      releaseTargetTriple = "aarch64-apple-darwin";
      codeModeHostSha256 = "sha256-NHHlSmFB+8vpTOyH0UNwNTZn1A81DvFvqgBevBhUMAs=";
      buildInputs = [ ];
    };
  };

  currentHostSystem = codexUpstreamReleaseDescriptorBySystem.${pkgs.stdenv.hostPlatform.system};

  codexReleaseAssetUrl =
    assetName:
    "https://github.com/openai/codex/releases/download/rust-v${version}/${assetName}-${currentHostSystem.releaseTargetTriple}.tar.gz";

  codex-binary = latest.codex.overrideAttrs (
    finalAttributes: previousAttributes: {
      inherit version;
      src = pkgs.fetchFromGitHub {
        owner = "openai";
        repo = "codex";
        tag = "rust-v${version}";
        hash = "sha256-R97lEHS2XfMQNbAc9k8v7EbcQCnwxND7zhnK3EBsI3Y=";
      };
      cargoHash = "sha256-GG6kOXmCdq+bZLU2ul0DIVL8lDuweayvZvXn6+bcUZw=";
      cargoDeps = latest.rustPlatform.fetchCargoVendor {
        name = "codex-${version}-vendor";
        inherit (finalAttributes) src;
        sourceRoot = "${finalAttributes.src.name}/codex-rs";
        hash = finalAttributes.cargoHash;
      };
      postPatch = ''
        substituteInPlace Cargo.toml \
          --replace-fail 'lto = "thin"' "" \
          --replace-fail 'codegen-units = 4' ""
      '';
      postFixup = (previousAttributes.postFixup or "") + ''
        ln -s ${codex-code-mode-host}/bin/codex-code-mode-host "$out/bin/codex-code-mode-host"
      '';
    }
  );

  codex-code-mode-host = fetchPrebuiltBinary {
    pname = "codex-code-mode-host";
    inherit version;
    url = codexReleaseAssetUrl "codex-code-mode-host";
    sha256 = currentHostSystem.codeModeHostSha256;
    inherit (currentHostSystem) buildInputs;
    binaryName = "codex-code-mode-host";
    archiveBinaryPath = "codex-code-mode-host-${currentHostSystem.releaseTargetTriple}";
  };

  interactiveSessionDeveloperInstructionsText = lib.concatStringsSep "\n" [
    (builtins.readFile ../../../agent-harness/agent-instructions/skills/humanize/references/interactive-communication.md)
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

  workspaceProfileLaunchDispatchFile = pkgs.writeText "codex-workspace-profile-launch-dispatch" workspaceProfileLaunchDispatch;

  codex = pkgs.writeShellApplication {
    name = "codex";
    bashOptions = [ ];
    excludeShellChecks = [ "SC1090" ];
    runtimeEnv = {
      NPM_CONFIG_PREFIX = "/nonexistent";
      CODEX_LAUNCHER_DEVELOPER_INSTRUCTIONS_FILE = "${interactivePreferencesFile}";
      CODEX_LAUNCHER_WORKSPACE_PROFILE_DISPATCH_FILE = "${workspaceProfileLaunchDispatchFile}";
      CODEX_LAUNCHER_BINARY = "${codex-binary}/bin/codex";
    };
    text = builtins.readFile ./scripts/codex;
  };
in
{
  options.codex.unwrappedPackage = lib.mkOption {
    type = lib.types.package;
    default = codex-binary;
    readOnly = true;
    description = "The bare upstream codex binary, without the interactive wrapper that injects sandbox mode, approval policy and the human's own developer_instructions. An autonomous harness builds its own full argv and must launch this, because re-passing a flag the wrapper already injected makes codex exit 2.";
  };

  config.home = {
    packages = [ codex ];
    file.".local/bin/codex".source = "${codex}/bin/codex";
  };
}
