{ pkgs }:
let
  emudhraDistrustedVersion = "2026.10.4";

  officialGoToolchain =
    pkgs.callPackage "${pkgs.path}/pkgs/development/compilers/go/binary.nix" {
      version = "1.27.3";
      hashes = {
        darwin-amd64 = "b6f8e931e4ab497fcde6da8ae4499a58f9d258e55c8a80824a516eae5950a750";
        darwin-arm64 = "dd3908cf20959d798c1e06ebe5b72213f0505ce01373b40ce3110975a6cd99c2";
        linux-amd64 = "65efbc80fdc1fa2cd2631cad5b481777a68e8725f34e89f50fc6ac714e379b40";
        linux-arm64 = "a06e99309dbcbdca1a8ccd2282c3ee146e55930886e26b4f1193269587165f49";
      };
    }
    // {
      inherit (pkgs.go) GOOS GOARCH CGO_ENABLED;
    };

  buildGoModuleWithOfficialGoToolchain =
    pkgs.callPackage "${pkgs.path}/pkgs/build-support/go/module.nix"
      {
        go = officialGoToolchain;
      };
in
if pkgs.lib.versionAtLeast pkgs.cloudflared.version emudhraDistrustedVersion then
  pkgs.cloudflared
else
  (pkgs.cloudflared.override { buildGoModule = buildGoModuleWithOfficialGoToolchain; }).overrideAttrs
    (
      finalAttributes: previousAttributes: {
        version = emudhraDistrustedVersion;

        src = pkgs.fetchFromGitHub {
          owner = "cloudflare";
          repo = "cloudflared";
          tag = finalAttributes.version;
          hash = "sha256-HuKjytbGutwjUMepozeUmeeHczm4qI7vMvS+hgLsaZ0=";
        };

        vendorHash = "sha256-WtGk5HE6PxAWqwvj8mAAzobuoSw+y6BqBEEB0hRQafk=";

        preCheck =
          builtins.replaceStrings
            [
              ''
                substituteInPlace "edgediscovery/protocol_test.go" \
                  --replace-warn "TestProtocolPercentage" "SkipProtocolPercentage"
              ''
            ]
            [
              ''
                substituteInPlace "crypto/curves_test.go" \
                  --replace-fail "TestSupportedCurvesNegotiation" "SkipSupportedCurvesNegotiation"
              ''
            ]
            previousAttributes.preCheck;

        ldflags = map (
          flag:
          if pkgs.lib.hasPrefix "-X main.Version=" flag then
            "-X main.Version=${finalAttributes.version}"
          else
            flag
        ) previousAttributes.ldflags;
      }
    )
