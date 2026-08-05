{ pkgs, lib }:
let
  fetchPrebuiltBinary = import ../../../../repository/nix-library/fetch-prebuilt-binary.nix {
    inherit pkgs;
  };

  cliProxyApiVersion = "7.2.96";
  cliProxyApiArtifacts = {
    aarch64-darwin = {
      releaseSystem = "darwin_aarch64";
      sha256 = "sha256-iG7HLFMqhjF3/+C6Fxam39ZNbXp9KwaWXjf9rhRedII=";
    };
    x86_64-linux = {
      releaseSystem = "linux_amd64";
      sha256 = "sha256-sOOK4ufSp6STWywMQ6B5tlM4eqGrzuIwM6GVRJJKLp0=";
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
