{ pkgs, ... }:
let
  fetchPrebuiltBinary = import ../../../lib/fetch-prebuilt-binary.nix { inherit pkgs; };

  version = "2.1.81";

  bucket = "https://storage.googleapis.com/claude-code-dist-86c565f3-f756-42ad-8dfa-d59b1c096819/claude-code-releases";

  platformBinaryHashBySystem = {
    "x86_64-linux" = {
      platform = "linux-x64";
      sha256 = "sha256-BH4/VZHWI4sI3ZUYcprDNbDo3xyA/pheXX+9osGPwoE=";
    };
  };

  currentSystem = platformBinaryHashBySystem.${pkgs.stdenv.hostPlatform.system};

  claude-code-unwrapped = fetchPrebuiltBinary {
    pname = "claude-code-unwrapped";
    inherit version;
    url = "${bucket}/${version}/${currentSystem.platform}/claude";
    inherit (currentSystem) sha256;
    binaryName = "claude";
  };

  claude-code = pkgs.writeShellScriptBin "claude" ''
    export NPM_CONFIG_PREFIX="/nonexistent"
    export DISABLE_AUTOUPDATER=1
    export DISABLE_INSTALLATION_CHECKS=1
    rm -rf "$HOME/.local/share/claude/versions"
    exec ${claude-code-unwrapped}/bin/claude "$@"
  '';
in
{
  home = {
    packages = [ claude-code ];
    file.".local/bin/claude".source = "${claude-code}/bin/claude";
  };
}
