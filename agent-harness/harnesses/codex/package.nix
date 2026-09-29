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

  version = "0.158.0";

  codexUpstreamReleaseDescriptorBySystem = {
    "x86_64-linux" = {
      releaseTargetTriple = "x86_64-unknown-linux-musl";
      sha256 = "b33cd426c9acab9b34c5a93200ba4fe83c8e614c18ce5ef52b2bf36408b8e18c";
      buildInputs = with pkgs; [
        openssl
        libcap
        zlib
      ];
    };
    "aarch64-darwin" = {
      releaseTargetTriple = "aarch64-apple-darwin";
      sha256 = "09f2a9fde318fbcd384f15b4850c1b90930678f4805647b6bded196ccf32f590";
      buildInputs = [ ];
    };
  };

  currentHostSystem = codexUpstreamReleaseDescriptorBySystem.${pkgs.stdenv.hostPlatform.system};

  codexReleaseAssetUrl =
    assetName:
    "https://github.com/openai/codex/releases/download/rust-v${version}/${assetName}-${currentHostSystem.releaseTargetTriple}.tar.gz";

  codex-unwrapped = fetchPrebuiltBinary {
    pname = "codex";
    inherit version;
    url = codexReleaseAssetUrl "codex-package";
    inherit (currentHostSystem) sha256 buildInputs;
    archivePrefixToInstall = ".";
    preserveCodeSignature = pkgs.stdenv.hostPlatform.isDarwin;
    meta.mainProgram = "codex";
  };

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

  sharedServerPython = pkgs.python312.withPackages (packages: [ packages.websockets ]);
  sharedServerExecutable = pkgs.writeShellScript "codex-shared-client" ''
    exec ${sharedServerPython}/bin/python3 ${./scripts/shared_server}/codex_client_launch.py "$@"
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
      CODEX_LAUNCHER_SHARED_SERVER_EXECUTABLE = "${sharedServerExecutable}";
    };
    text = builtins.readFile ./scripts/codex;
  };
in
{
  options.codex.unwrappedPackage = lib.mkOption {
    type = lib.types.package;
    default = codex-unwrapped;
    readOnly = true;
    description = "The bare upstream codex binary, without the interactive wrapper that selects the human's instruction profile and injects sandbox mode and approval policy. An autonomous harness builds its own full argv and must launch this, because re-passing a flag the wrapper already injected makes codex exit 2.";
  };

  config.home = {
    packages = [ codex ];
    file = workspaceProfileActivation.profileFiles config.agentWorkspaceProfiles.profiles // {
      ".local/bin/codex".source = "${codex}/bin/codex";
      ".codex/packages/app-server-daemon/current".source = codex-unwrapped;
      ".codex/app-server-daemon/settings.json".text = builtins.toJSON {
        remoteControlEnabled = false;
        shutdownGraceSeconds = 60;
        updater.autoUpdateEnabled = false;
      };
    };
  };
}
