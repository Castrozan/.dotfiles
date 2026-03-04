{ pkgs, ... }:
let
  fetchPrebuiltBinary = import ../../../lib/fetch-prebuilt-binary.nix { inherit pkgs; };

  version = "2.1.68";
  platform = "linux-x64";
  bucket = "https://storage.googleapis.com/claude-code-dist-86c565f3-f756-42ad-8dfa-d59b1c096819/claude-code-releases";

  claude-code-unwrapped = fetchPrebuiltBinary {
    pname = "claude-code-unwrapped";
    inherit version;
    url = "${bucket}/${version}/${platform}/claude";
    sha256 = "lpogzEqdluNEkJDtOU7+SEbpIM7F0Sy5zove9eGr5XU=";
    binaryName = "claude";
  };

  claude-code = pkgs.writeShellScriptBin "claude" ''
    export NPM_CONFIG_PREFIX="/nonexistent"
    export DISABLE_AUTOUPDATER=1
    exec ${claude-code-unwrapped}/bin/claude "$@"
  '';
in
{
  home = {
    packages = [ claude-code ];
    file.".local/bin/claude".source = "${claude-code}/bin/claude";
  };
}
