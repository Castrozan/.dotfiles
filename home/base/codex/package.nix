{ pkgs, ... }:
let
  fetchPrebuiltBinary = import ../../../lib/fetch-prebuilt-binary.nix { inherit pkgs; };

  version = "0.145.0";

  codexUpstreamReleaseDescriptorBySystem = {
    "x86_64-linux" = {
      releaseTargetTriple = "x86_64-unknown-linux-musl";
      sha256 = "sha256-v68Tybo08q12TkqRbEnPcXeuujKc8PcZ4iJ1ZvyNZio=";
      buildInputs = with pkgs; [
        openssl
        libcap
        zlib
      ];
    };
    "aarch64-darwin" = {
      releaseTargetTriple = "aarch64-apple-darwin";
      sha256 = "sha256-Byowpl8FZmc1iJ7w9gtW2xhq293p1cXMGmS+C1mFMP4=";
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
      --dangerously-bypass-hook-trust \
      --no-alt-screen \
      "''${interactivePreferencesArguments[@]}" \
      "$@"
  '';
in
{
  home.packages = [ codex ];
  home.file.".local/bin/codex".source = "${codex}/bin/codex";
}
