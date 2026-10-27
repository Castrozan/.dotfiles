{ latest }:
let
  patchedVersion = "1.4.4";

  releaseArchiveHashes = {
    aarch64-darwin = {
      archive = "bun-darwin-aarch64";
      hash = "sha256-wkDX8My5DCY6hJ/NsJt+5iYw2SE0jtaq/ahrnVd7xRA=";
    };
    x86_64-linux = {
      archive = "bun-linux-x64-baseline";
      hash = "sha256-4ERutVmVdy65iUvrrppr42jZhai5Jx7hJEhvmUbu3XY=";
    };
  };
in
if latest.lib.versionAtLeast latest.bun.version patchedVersion then
  latest.bun
else
  latest.bun.overrideAttrs (
    finalAttributes: previousAttributes: {
      version = patchedVersion;
      passthru = previousAttributes.passthru // {
        sources = builtins.mapAttrs (
          _system: release:
          latest.fetchurl {
            url = "https://github.com/oven-sh/bun/releases/download/bun-v${finalAttributes.version}/${release.archive}.zip";
            inherit (release) hash;
          }
        ) releaseArchiveHashes;
      };
    }
  )
