{ pkgs, lib }:
let
  release = {
    version = "0.14.0";
    tag = "v0.14.0";
    commit = "8def159a6b2c23e832a5283b4131cfffd9af9344";
    publishedEpoch = 1794041828;
  };

  platformReleases = {
    x86_64-linux = {
      assetSuffix = "linux-x64";
      hashes = {
        archon = "sha256-mW2ZiZM71yFGRYQHI8SKgD54ElZDWg8NIutP5kWYW6s=";
        claude = "sha256-RZldM/hLwFMuihyAqMANahxaS7DMKuebrlOXnNXPuMc=";
        codex = "sha256-QIE8a6fYlg+d2eil0LOEZ6/3iUl/QJAHGBepT0tmGts=";
        pi = "sha256-l1yhvrIzx8YdiVmoLpov9Xwq+i5aLD0NiMp06zSvapI=";
      };
    };
    aarch64-darwin = {
      assetSuffix = "darwin-arm64";
      hashes = {
        archon = "sha256-eEzA/AcO2wRvQQ0dXeazCpJftA7PH3Ci3iNzEEjG06Q=";
        claude = "sha256-y6vDvdpKM7OEK5HMhg1BzN+nq1QgKcpwNwiX4+0MiZk=";
        codex = "sha256-MGC3WODmYnf0zzVOU1UVeMlhECYN5UB3ygXEONtSv4U=";
        pi = "sha256-MniPdetofIKDD0zeEPVPZSEbuNxwSnJqfdF/vvIM25E=";
      };
    };
  };

  platformRelease = platformReleases.${pkgs.stdenv.hostPlatform.system};

  fetchReleaseAsset =
    assetName: hash:
    pkgs.fetchurl {
      url = "https://github.com/coleam00/Archon/releases/download/${release.tag}/${assetName}-${platformRelease.assetSuffix}";
      inherit hash;
    };

  maintainedProviders = [
    {
      identifier = "claude";
      displayName = "Claude";
    }
    {
      identifier = "codex";
      displayName = "Codex";
    }
    {
      identifier = "pi";
      displayName = "Pi";
    }
  ];

  installReleaseBinary =
    source: destination:
    ''
      install -Dm755 ${source} ${destination}
    ''
    + lib.optionalString pkgs.stdenv.hostPlatform.isLinux ''
      patchelf --set-interpreter "$(cat $NIX_CC/nix-support/dynamic-linker)" ${destination}
    '';

  installProvider =
    { identifier, displayName }:
    let
      pluginBinary = "$out/share/archon/plugins/archon-provider-${identifier}";
    in
    installReleaseBinary (fetchReleaseAsset "archon-provider-${identifier}"
      platformRelease.hashes.${identifier}
    ) pluginBinary
    + ''
      python3 ${./scripts/archon_provider_receipt.py} \
        --provider-binary ${pluginBinary} \
        --provider-identifier ${identifier} \
        --display-name ${displayName} \
        --release-tag ${release.tag} \
        --release-commit ${release.commit} \
        --installed-at-epoch ${toString release.publishedEpoch} \
        --output "$out/share/archon/plugins/installed/coleam00/Archon/plugins/provider-${identifier}/receipt.json"
    '';
in
pkgs.stdenv.mkDerivation {
  pname = "archon";
  inherit (release) version;
  dontUnpack = true;
  dontConfigure = true;
  dontBuild = true;
  dontFixup = true;
  nativeBuildInputs = [
    pkgs.makeWrapper
    pkgs.python312
  ]
  ++ lib.optional pkgs.stdenv.hostPlatform.isLinux pkgs.patchelf;
  installPhase = ''
    runHook preInstall
    export HOME="$TMPDIR"
    ${installReleaseBinary (fetchReleaseAsset "archon" platformRelease.hashes.archon) "$out/libexec/archon/archon"}
    ${lib.concatMapStrings installProvider maintainedProviders}
    makeWrapper $out/libexec/archon/archon $out/bin/archon \
      --set ARCHON_TELEMETRY_DISABLED 1 \
      --set DO_NOT_TRACK 1
    runHook postInstall
  '';
  meta = {
    description = "Archon workflow engine with its maintained provider plugins";
    homepage = "https://github.com/coleam00/Archon";
    license = lib.licenses.mit;
    platforms = builtins.attrNames platformReleases;
    mainProgram = "archon";
  };
}
