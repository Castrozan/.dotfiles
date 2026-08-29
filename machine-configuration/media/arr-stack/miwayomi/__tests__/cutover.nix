{
  helpers,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  chiseHomeText = builtins.readFile ../../../../machines/chise/home.nix;
  cloudflareOriginsText = builtins.readFile ../../chise/cloudflare-origins/default.nix;
  stackReadmeText = builtins.readFile ../../stack/README.md;
  suwayomiModulePath = ../../../manga-streaming/suwayomi-server-home-manager.nix;
  suwayomiModuleText = builtins.readFile suwayomiModulePath;
  repositorySecretPath = ../../../../../secrets/credentials/suwayomi-extension-repositories.age;
  animeStreamingDirectory = ../../../anime-streaming;

  suwayomiIsDeployed = lib.hasInfix "../../media/manga-streaming/suwayomi-server-home-manager.nix" chiseHomeText;
  mangaReaderArtifactsRemain =
    builtins.pathExists suwayomiModulePath
    && builtins.pathExists repositorySecretPath
    && lib.hasInfix "TACHIDESK_DATA_DIR=\${homeDir}/.local/share/Tachidesk" suwayomiModuleText
    && lib.hasInfix "downloadsPath = mangaDownloadRoot;" suwayomiModuleText;
  mangaAndAnimeOriginsAreDeclared =
    lib.hasInfix "anime.lucaszanoni.com" cloudflareOriginsText
    && lib.hasInfix "suwayomi.lucaszanoni.com" cloudflareOriginsText
    && lib.hasInfix ":4567" cloudflareOriginsText
    && lib.hasInfix ":4568" cloudflareOriginsText;
  serviceBoundaryIsDocumented =
    lib.hasInfix "Suwayomi handles manga discovery, browser reading" stackReadmeText
    && lib.hasInfix "Kavita-compatible CBZ files." stackReadmeText
    && lib.hasInfix "Kavita serves the persisted CBZ library" stackReadmeText
    && lib.hasInfix "read-only." stackReadmeText
    && lib.hasInfix "Miwayomi handles instant anime playback." stackReadmeText;
  seanimeIsRemoved =
    !(lib.hasInfix "../../media/anime-streaming/seanime-home-manager.nix" chiseHomeText)
    && !(lib.hasInfix "seanime.lucaszanoni.com" cloudflareOriginsText)
    && !(lib.hasInfix ":43211" cloudflareOriginsText)
    && !(builtins.pathExists "${animeStreamingDirectory}/seanime-home-manager.nix")
    && !(builtins.pathExists "${animeStreamingDirectory}/seanime-package.nix")
    && !(builtins.pathExists "${animeStreamingDirectory}/prowlarr-anime-torrent-provider.js")
    && !(builtins.pathExists "${animeStreamingDirectory}/scripts/seanime_provisioner");
in
{
  chise-suwayomi-and-miwayomi-serve-separate-media =
    mkEvalCheck "chise-suwayomi-and-miwayomi-serve-separate-media"
      (suwayomiIsDeployed && mangaReaderArtifactsRemain)
      "chise must deploy Suwayomi for manga while retaining Miwayomi for anime";

  chise-manga-and-anime-have-owner-gated-cloudflare-origins =
    mkEvalCheck "chise-manga-and-anime-have-owner-gated-cloudflare-origins"
      mangaAndAnimeOriginsAreDeclared
      "Miwayomi and Suwayomi must route through their dedicated Cloudflare origins";

  chise-manga-and-anime-service-boundary-is-documented =
    mkEvalCheck "chise-manga-and-anime-service-boundary-is-documented" serviceBoundaryIsDocumented
      "the stack must document Suwayomi for manga, Kavita for persisted CBZ files, and Miwayomi for instant anime";

  chise-seanime-is-removed =
    mkEvalCheck "chise-seanime-is-removed" seanimeIsRemoved
      "Seanime must have no chise import, Cloudflare origin, package, provider, or provisioner";
}
