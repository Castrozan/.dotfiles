{ pkgs, lib }:
let
  fetchPrebuiltBinary = import ../../../../../repository/nix-library/fetch-prebuilt-binary.nix {
    inherit pkgs;
  };

  cliProxyApiVersion = "8.0.44";
  cliProxyApiArtifacts = {
    aarch64-darwin = {
      releaseSystem = "darwin_aarch64";
      sha256 = "sha256-ULdeC87IV2uTVh8qspQf8Iryb8knPPaG6cKzN3FrvEY=";
    };
    x86_64-linux = {
      releaseSystem = "linux_amd64";
      sha256 = "sha256-OVfDT+SpWjf1mXq2PXjcpDH6FSGZfXwqs73+FprYkwc=";
    };
  };
  cliProxyApiArtifact =
    cliProxyApiArtifacts.${pkgs.stdenv.hostPlatform.system}
      or (throw "cli-proxy-api is unsupported on ${pkgs.stdenv.hostPlatform.system}");
in
fetchPrebuiltBinary {
  pname = "cli-proxy-api";
  version = cliProxyApiVersion;
  url = "https://github.com/router-for-me/CLIProxyAPI/releases/download/v${cliProxyApiVersion}/CLIProxyAPI_${cliProxyApiVersion}_${cliProxyApiArtifact.releaseSystem}.tar.gz";
  inherit (cliProxyApiArtifact) sha256;
  binaryName = "cli-proxy-api";
  meta = {
    description = "Local proxy translating the Anthropic Messages API onto OpenAI-compatible and subscription upstreams";
    homepage = "https://github.com/router-for-me/CLIProxyAPI";
    license = lib.licenses.mit;
    platforms = builtins.attrNames cliProxyApiArtifacts;
    mainProgram = "cli-proxy-api";
  };
}
