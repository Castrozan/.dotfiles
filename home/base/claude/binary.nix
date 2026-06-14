{
  pkgs,
  lib,
  ...
}:
let
  fetchPrebuiltBinary = import ../../../lib/fetch-prebuilt-binary.nix { inherit pkgs; };

  version = "2.1.177";
  bucket = "https://storage.googleapis.com/claude-code-dist-86c565f3-f756-42ad-8dfa-d59b1c096819/claude-code-releases";

  platformBinaryHashBySystem = {
    "x86_64-linux" = {
      platform = "linux-x64";
      sha256 = "sha256-/0F1NjSyDIae9qMqIIY1IbM9QYasDWpJN5q0ikg5Xuc=";
    };
    "aarch64-darwin" = {
      platform = "darwin-arm64";
      sha256 = "sha256-6wcwNRvi8CtIKxhVhw9Yd0iQharIawxMHbTkWNnkDtk=";
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
    rm -rf "$HOME/.local/share/claude/versions"
    ${pkgs.python312}/bin/python3 ${./scripts/pre-approve-current-workspace-trust-dialog} || true
    exec ${claude-code-unwrapped}/bin/claude "$@"
  '';
in
{
  options.claude.package = lib.mkOption {
    type = lib.types.package;
    default = claude-code;
    readOnly = true;
    description = "The claude-code package used across all claude modules";
  };

  config.home = {
    packages = [ claude-code ];
    file.".local/bin/claude" = {
      source = "${claude-code}/bin/claude";
      force = true;
    };
  };
}
