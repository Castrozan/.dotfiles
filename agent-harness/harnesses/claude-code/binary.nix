{
  pkgs,
  lib,
  ...
}:
let
  fetchPrebuiltBinary = import ../../../repository/nix-library/fetch-prebuilt-binary.nix {
    inherit pkgs;
  };

  version = "2.1.235";
  bucket = "https://storage.googleapis.com/claude-code-dist-86c565f3-f756-42ad-8dfa-d59b1c096819/claude-code-releases";

  platformBinaryHashBySystem = {
    "x86_64-linux" = {
      platform = "linux-x64";
      sha256 = "sha256-v88K4tv5SytqEGB0qr85OLmhCInDtnjky1oAwDJ01dU=";
    };
    "aarch64-darwin" = {
      platform = "darwin-arm64";
      sha256 = "sha256-g7j4Bvby7qMWz+JGYo5sIzdHEdho8f0ECdtVG4d7d0g=";
    };
  };

  currentSystem = platformBinaryHashBySystem.${pkgs.stdenv.hostPlatform.system};

  claude-code-unwrapped = fetchPrebuiltBinary {
    pname = "claude-code-unwrapped";
    binaryName = "claude";
    inherit version;
    inherit (currentSystem) sha256;
    url = "${bucket}/${version}/${currentSystem.platform}/claude";
  };

  claudeEnvironmentVariables = import ./settings/environment-variables.nix { inherit pkgs; };

  exportLinesForClaudeEnvironment = lib.concatStringsSep "\n" (
    lib.mapAttrsToList (name: value: ''export ${name}="${value}"'') claudeEnvironmentVariables
  );

  claude-code = pkgs.writeShellScriptBin "claude" ''
    ${exportLinesForClaudeEnvironment}
    ${pkgs.bash}/bin/bash ${./scripts/pre-approve-current-workspace-trust-dialog.sh} "${pkgs.jq}/bin/jq" || true
    exec ${claude-code-unwrapped}/bin/claude "$@"
  '';
in
{
  options.claude.unwrappedPackage = lib.mkOption {
    type = lib.types.package;
    default = claude-code;
    readOnly = true;
    description = "claude without the interactive wrapper that appends the human's own reply-shape system prompt and resolves a workspace profile, but still exporting the shared claude environment and pre-approving the workspace trust dialog. An autonomous harness must launch this, because the interactive reply rules apply only while the human drives the keyboard.";
  };
}
