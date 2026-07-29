{ pkgs, lib, ... }:
let
  fetchPrebuiltBinary = import ../../../lib/fetch-prebuilt-binary.nix { inherit pkgs; };

  version = "0.146.0";

  codexUpstreamReleaseDescriptorBySystem = {
    "x86_64-linux" = {
      releaseTargetTriple = "x86_64-unknown-linux-musl";
      sha256 = "sha256-W6O5QFVDlTCB9mHQhU0mb3biq75R1BNJNVo23nZzd2o=";
      buildInputs = with pkgs; [
        openssl
        libcap
        zlib
      ];
    };
    "aarch64-darwin" = {
      releaseTargetTriple = "aarch64-apple-darwin";
      sha256 = "sha256-J1ATLTAOZPHb/7lePZE/2cnceBK8jhvOXGE1cki3kp4=";
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

  interactivePreferencesFile = ../../../agents/core_rules/communication/interactive-preferences.md;

  codex = pkgs.writeShellScriptBin "codex" ''
    export NPM_CONFIG_PREFIX="/nonexistent"
    interactivePreferencesArguments=()
    case "''${1:-}" in
      "" | -* | resume | fork)
        interactivePreferencesArguments=(
          -c "developer_instructions=$(cat ${interactivePreferencesFile})"
        )
        ;;
    esac
    exec ${codex-unwrapped}/bin/codex \
      --model "gpt-5.6-sol" \
      --sandbox "danger-full-access" \
      --ask-for-approval "never" \
      --no-alt-screen \
      "''${interactivePreferencesArguments[@]}" \
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
