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

  version = "0.155.1";

  codexUpstreamReleaseDescriptorBySystem = {
    "x86_64-linux" = {
      releaseTargetTriple = "x86_64-unknown-linux-musl";
      sha256 = "sha256-oO+LLevDv3R+B7GgOTVN4xMArA3MInZJi6KBRwtdkRU=";
      codeModeHostSha256 = "sha256-n9CDdDr1W+gYrOs1HTcftRNvW2qjk48WcIc3PScGey0=";
      buildInputs = with pkgs; [
        openssl
        libcap
        zlib
      ];
    };
    "aarch64-darwin" = {
      releaseTargetTriple = "aarch64-apple-darwin";
      sha256 = "sha256-XlpRRw3OJCP52WvRkdC7xMwOKEimgz31F46vR6B6N2g=";
      codeModeHostSha256 = "sha256-6JVxCO69cJY7CQaFfOt/eitHfRlypxRwQcYl1AcbUIo=";
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

  codex-unwrapped = codex-binary.overrideAttrs (previousAttributes: {
    meta = (previousAttributes.meta or { }) // {
      mainProgram = "codex";
    };
    postFixup = (previousAttributes.postFixup or "") + ''
      ln -s ${codex-code-mode-host}/bin/codex-code-mode-host "$out/bin/codex-code-mode-host"
    '';
  });

  interactivePreferencesFile = import ./interactive-instructions.nix {
    inherit pkgs;
    inherit (config.home) homeDirectory;
  };

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

  workspaceProfileLaunchDispatchFile = pkgs.writeText "codex-workspace-profile-launch-dispatch" workspaceProfileLaunchDispatch;

  hookTrustExecutable = pkgs.writeShellScript "codex-approve-discovered-hooks" ''
    exec ${pkgs.python312}/bin/python3 ${./scripts/hook_trust}/approve.py "$@"
  '';

  codex = pkgs.writeShellApplication {
    name = "codex";
    bashOptions = [ ];
    excludeShellChecks = [ "SC1090" ];
    runtimeEnv = {
      NPM_CONFIG_PREFIX = "/nonexistent";
      CODEX_LAUNCHER_DEVELOPER_INSTRUCTIONS_FILE = "${interactivePreferencesFile}";
      CODEX_LAUNCHER_WORKSPACE_PROFILE_DISPATCH_FILE = "${workspaceProfileLaunchDispatchFile}";
      CODEX_LAUNCHER_BINARY = "${codex-unwrapped}/bin/codex";
      CODEX_LAUNCHER_HOOK_TRUST_EXECUTABLE = "${hookTrustExecutable}";
    };
    text = builtins.readFile ./scripts/codex;
  };
in
{
  options.codex.unwrappedPackage = lib.mkOption {
    type = lib.types.package;
    default = codex-unwrapped;
    readOnly = true;
    description = "The bare upstream codex binary, without the interactive wrapper that injects sandbox mode, approval policy and the human's own developer_instructions. An autonomous harness builds its own full argv and must launch this, because re-passing a flag the wrapper already injected makes codex exit 2.";
  };

  config.home = {
    packages = [ codex ];
    file.".local/bin/codex".source = "${codex}/bin/codex";
  };
}
