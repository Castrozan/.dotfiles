{ pkgs, ... }:
let
  fetchPrebuiltBinary = import ../../../lib/fetch-prebuilt-binary.nix { inherit pkgs; };

  version = "20.0.14";

  inherit (pkgs.stdenv.hostPlatform) system isDarwin;

  npmPlatformPackageBySystem = {
    "aarch64-darwin" = {
      npmPackageName = "ccusage-darwin-arm64";
      sha256 = "0hmxpd00pb11761y8ib3am8ck1zlkaikmgpxagrsxv2z8q0fqjk5";
    };
    "x86_64-linux" = {
      npmPackageName = "ccusage-linux-x64";
      sha256 = "0i1x0jf11jdsx7xamnqzky8r2xdrckgna7nj8ljivln9mf6z8ckc";
    };
  };

  npmPlatformPackageForCurrentSystem =
    npmPlatformPackageBySystem.${system}
      or (throw "ccusage: no prebuilt native binary published for system ${system}");

  ccusage = fetchPrebuiltBinary {
    pname = "ccusage";
    binaryName = "ccusage";
    inherit version;
    url = "https://registry.npmjs.org/@ccusage/${npmPlatformPackageForCurrentSystem.npmPackageName}/-/${npmPlatformPackageForCurrentSystem.npmPackageName}-${version}.tgz";
    inherit (npmPlatformPackageForCurrentSystem) sha256;
    archiveBinaryPath = "package/bin/ccusage";
    preserveCodeSignature = isDarwin;
  };
in
{
  home.packages = [ ccusage ];
}
