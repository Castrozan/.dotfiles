{
  helpers,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  chiseHomeText = builtins.readFile ../../../../machines/chise/home.nix;
  sharedMediaHomeManagerText = builtins.readFile ../../../media-home-manager.nix;
  cloudflareOriginsText = builtins.readFile ../../chise/cloudflare-origins/default.nix;
  stackReadmeText = builtins.readFile ../../stack/README.md;
  suwayomiModulePath = ../../../manga-streaming/suwayomi-server-home-manager.nix;
  suwayomiModuleText = builtins.readFile suwayomiModulePath;
  repositorySecretPath = ../../../../../secrets/credentials/suwayomi-extension-repositories.age;

  suwayomiDeploymentImportsAreRemoved =
    !(lib.hasInfix "../../media/manga-streaming/suwayomi-server-home-manager.nix" chiseHomeText)
    && !(lib.hasInfix "./manga-streaming/suwayomi-server-home-manager.nix" sharedMediaHomeManagerText);
  suwayomiRollbackArtifactsRemain =
    builtins.pathExists suwayomiModulePath
    && builtins.pathExists repositorySecretPath
    && lib.hasInfix "TACHIDESK_DATA_DIR=\${homeDir}/.local/share/Tachidesk" suwayomiModuleText
    && lib.hasInfix "downloadsPath = mangaDownloadRoot;" suwayomiModuleText;
  noPublicMiwayomiOrSuwayomiOrigin =
    !(lib.hasInfix "suwayomi.lucaszanoni.com" cloudflareOriginsText)
    && !(lib.hasInfix "miwayomi.lucaszanoni.com" cloudflareOriginsText)
    && !(lib.hasInfix ":4567" cloudflareOriginsText)
    && !(lib.hasInfix ":4568" cloudflareOriginsText);
  replacementBoundaryIsDocumented =
    lib.hasInfix "Miwayomi handles live web manga reading and anime playback." stackReadmeText
    && lib.hasInfix "Kavita keeps serving the existing CBZ library read-only." stackReadmeText
    && lib.hasInfix "Miwayomi does not write" stackReadmeText
    && lib.hasInfix "Kavita-compatible CBZ files." stackReadmeText;
in
{
  chise-miwayomi-replaces-suwayomi-deployment =
    mkEvalCheck "chise-miwayomi-replaces-suwayomi-deployment"
      (suwayomiDeploymentImportsAreRemoved && suwayomiRollbackArtifactsRemain)
      "chise must stop deploying Suwayomi while retaining its module, data declaration, encrypted repository list, and rollback path";

  chise-miwayomi-has-no-public-cloudflare-origin =
    mkEvalCheck "chise-miwayomi-has-no-public-cloudflare-origin" noPublicMiwayomiOrSuwayomiOrigin
      "the unauthenticated Miwayomi replacement and retired Suwayomi service must have no public Cloudflare origin";

  chise-miwayomi-replacement-boundary-is-documented =
    mkEvalCheck "chise-miwayomi-replacement-boundary-is-documented" replacementBoundaryIsDocumented
      "the stack must document Miwayomi as the live browser reader and player, Kavita as the existing CBZ reader, and the absence of a Miwayomi-to-Kavita acquisition path";
}
