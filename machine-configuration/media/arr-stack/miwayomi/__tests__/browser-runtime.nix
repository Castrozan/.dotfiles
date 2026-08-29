{
  helpers,
  lib,
  pkgs,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  composeText = builtins.readFile ../../stack/docker-compose.yml;
  gatewayConfigurationPath = ../../stack/miwayomi-gateway.conf;
  gatewayConfigurationText =
    if builtins.pathExists gatewayConfigurationPath then
      builtins.readFile gatewayConfigurationPath
    else
      "";
  miwayomiDockerfilePath = ../../stack/miwayomi.Dockerfile;
  miwayomiDockerfileText =
    if builtins.pathExists miwayomiDockerfilePath then builtins.readFile miwayomiDockerfilePath else "";
  miwayomiPatchPath = ../../stack/miwayomi-manga-input-initialization.patch;
  miwayomiPatchText =
    if builtins.pathExists miwayomiPatchPath then builtins.readFile miwayomiPatchPath else "";
  watchProgressPatchPath = ../../stack/miwayomi-watch-progress.patch;
  watchProgressPatchText =
    if builtins.pathExists watchProgressPatchPath then builtins.readFile watchProgressPatchPath else "";
  interfaceArtworkPatchPath = ../../stack/miwayomi-interface-artwork.patch;
  interfaceArtworkPatchText =
    if builtins.pathExists interfaceArtworkPatchPath then
      builtins.readFile interfaceArtworkPatchPath
    else
      "";
  stackModuleText = builtins.readFile ../../stack/arr-stack-home-manager.nix;

  imagesAndBuildContextArePinned =
    lib.hasInfix "image: arr-miwayomi:0.2.9-watch-progress" composeText
    && lib.hasInfix "context: \${MIWAYOMI_BUILD_CONTEXT:?set in ~/arr-stack/.env}" composeText
    && lib.hasInfix "dockerfile: miwayomi.Dockerfile" composeText
    && lib.hasInfix "gradle:8.10.2-jdk21@sha256:963d59f7f22767da4efbcf46b661361b61af5fb88b0309da1071c4234c647eba" miwayomiDockerfileText
    && lib.hasInfix "ghcr.io/miwayomi/miwayomi:0.2.9@sha256:8e7094088565b97091319dfa92b80a8c22497a712e72af09e2470454f5942ec4" miwayomiDockerfileText
    && lib.hasInfix "bf18765a00cfc639ead84d97e071383c436ca7d7.tar.gz" miwayomiDockerfileText
    && lib.hasInfix "238a4b91d40f0c32d2096475c1a7bdf6500096272ea776ae6f0565c919b31b44" miwayomiDockerfileText
    && lib.hasInfix "ghcr.io/miwayomi/flaresolverr:0.2.9@sha256:41207a879aebc3e36101734377041a9d82e7375db274aebc0d15c87e51134189" composeText
    && lib.hasInfix "nginx:1.30.4-alpine@sha256:97d490c12ba55b4946b01546d1c3ed324e8d41ab1c9fcb2a616aa470620e5b46" composeText
    && lib.hasInfix ''pkgs.runCommand "miwayomi-build-context"'' stackModuleText
    && lib.hasInfix "cp \${./miwayomi.Dockerfile}" stackModuleText
    && lib.hasInfix "cp \${./miwayomi-manga-input-initialization.patch}" stackModuleText
    && lib.hasInfix "MIWAYOMI_BUILD_CONTEXT=\${miwayomiBuildContext}" stackModuleText;
  gatewayRepairsMiwayomiProxyOrigins =
    lib.hasInfix "hostname: miwayomi" composeText
    && lib.hasInfix "container_name: arr-miwayomi-gateway" composeText
    && lib.hasInfix "\${MIWAYOMI_GATEWAY_CONFIG_PATH:?set in ~/arr-stack/.env}:/etc/nginx/conf.d/default.conf:ro" composeText
    && lib.hasInfix "MIWAYOMI_GATEWAY_CONFIG_PATH=\${./miwayomi-gateway.conf}" stackModuleText
    && !(lib.hasInfix ''"arr-stack/miwayomi-gateway.conf".source'' stackModuleText)
    && lib.hasInfix "http://127.0.0.1:4568/api/v1/health" composeText
    && lib.hasInfix "proxy_pass http://miwayomi:4567" gatewayConfigurationText
    && lib.hasInfix "map $http_x_forwarded_proto $miwayomi_external_scheme" gatewayConfigurationText
    && lib.hasInfix ''~^https(?:\s*,|$) https;'' gatewayConfigurationText
    && lib.hasInfix "proxy_set_header X-Forwarded-Proto $miwayomi_external_scheme" gatewayConfigurationText
    && lib.hasInfix ''sub_filter "http://miwayomi:4567" "$miwayomi_external_scheme://$http_host"'' gatewayConfigurationText;
  mangaInputInitializationIsIsolated =
    lib.hasInfix ''it.title = ""'' miwayomiPatchText
    && lib.hasInfix ''it.name = ""'' miwayomiPatchText
    && !(lib.hasInfix "AnimeRoutes.kt" miwayomiPatchText);
  outboundServicesUseStableDns =
    lib.hasInfix "x-stable-public-dns: &stable-public-dns\n  - 1.1.1.1\n  - 8.8.8.8" composeText
    && lib.hasInfix "hostname: miwayomi\n    user: \"\${PUID}:\${PGID}\"\n    networks:\n      - arrnet\n    dns: *stable-public-dns" composeText
    && lib.hasInfix "container_name: arr-flaresolverr\n    restart: unless-stopped\n    networks:\n      - arrnet\n    dns: *stable-public-dns" composeText;
  watchProgressNormalizationIsIsolated =
    lib.hasInfix "COPY miwayomi-watch-progress.patch /tmp/miwayomi-watch-progress.patch" miwayomiDockerfileText
    && lib.hasInfix "RUN git apply /tmp/miwayomi-watch-progress.patch" miwayomiDockerfileText
    && lib.hasInfix "cp \${./miwayomi-watch-progress.patch}" stackModuleText
    && lib.hasInfix "const requestedAnimeUrl = safeDecode(animeUrl);" watchProgressPatchText
    && lib.hasInfix "d.url = requestedAnimeUrl;" watchProgressPatchText
    && !(lib.hasInfix "MangaRoutes.kt" watchProgressPatchText);
  interfaceArtworkIsPreserved =
    lib.hasInfix "COPY miwayomi-interface-artwork.patch /tmp/miwayomi-interface-artwork.patch" miwayomiDockerfileText
    && lib.hasInfix "RUN git apply /tmp/miwayomi-interface-artwork.patch" miwayomiDockerfileText
    && lib.hasInfix "cp \${./miwayomi-interface-artwork.patch}" stackModuleText
    && lib.hasInfix ''<link rel="icon" type="image/png" href="/logov1.png">'' interfaceArtworkPatchText
    && lib.hasInfix "async function loadHomeAnimeCatalog()" interfaceArtworkPatchText
    && lib.hasInfix "AbortSignal.timeout(4000)" interfaceArtworkPatchText
    && lib.hasInfix "renderGeneration !== homeRenderGeneration" interfaceArtworkPatchText
    && lib.hasInfix "function openCatalogEntry(sourceId, type, url, thumbnailUrl)" interfaceArtworkPatchText
    && lib.hasInfix "d.thumbnail_url = d.thumbnail_url || knownThumbnailUrl;" interfaceArtworkPatchText
    && !(lib.hasInfix "MangaRoutes.kt" interfaceArtworkPatchText);
  gatewaySchemeRuntimeCheck =
    pkgs.runCommand "chise-miwayomi-gateway-scheme-runtime"
      {
        nativeBuildInputs = [
          pkgs.bash
          pkgs.curl
          pkgs.nginx
        ];
      }
      ''
        bash ${./verify-gateway-scheme.sh} ${gatewayConfigurationPath}
        touch "$out"
      '';
in
{
  chise-miwayomi-images-are-pinned =
    mkEvalCheck "chise-miwayomi-images-are-pinned" imagesAndBuildContextArePinned
      "Miwayomi, FlareSolverr and the stream gateway must use immutable upstream image digests and a Nix-owned regular-file build context";

  chise-miwayomi-stream-gateway-repairs-container-origins =
    mkEvalCheck "chise-miwayomi-stream-gateway-repairs-container-origins"
      gatewayRepairsMiwayomiProxyOrigins
      "Miwayomi emits its Docker hostname into HLS and DASH manifests, so the tailnet gateway must replace that internal origin with the browser-visible request origin";

  chise-miwayomi-stream-gateway-preserves-public-scheme = gatewaySchemeRuntimeCheck;

  chise-miwayomi-initializes-required-manga-inputs =
    mkEvalCheck "chise-miwayomi-initializes-required-manga-inputs" mangaInputInitializationIsIsolated
      "Miwayomi must initialize required manga and chapter fields before third-party extensions read them, while keeping the temporary workaround isolated from the working anime path";

  chise-miwayomi-outbound-services-use-stable-dns =
    mkEvalCheck "chise-miwayomi-outbound-services-use-stable-dns" outboundServicesUseStableDns
      "Miwayomi and FlareSolverr must bypass Docker's unusable MagicDNS upstream while retaining Compose service discovery";

  chise-miwayomi-restores-watch-progress =
    mkEvalCheck "chise-miwayomi-restores-watch-progress" watchProgressNormalizationIsIsolated
      "the watch-history adapter must preserve the persisted anime URL when an extension duplicates its fragment during detail loading";

  chise-miwayomi-home-renders-media-artwork =
    mkEvalCheck "chise-miwayomi-home-renders-media-artwork" interfaceArtworkIsPreserved
      "Miwayomi Home must render a working anime catalog with persisted thumbnails and every HTML entry point must declare the existing logo as its favicon";
}
