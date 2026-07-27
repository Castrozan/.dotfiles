{
  pkgs,
  lib,
}:
let
  helpers = import ../../../__tests__/nix-checks/helpers.nix {
    inherit pkgs lib;
    inputs = { };
    nixpkgs-version = "25.11";
    home-version = "25.11";
  };
  inherit (helpers) mkEvalCheck;

  composeText = builtins.readFile ../../../home/linux/arr-stack/docker-compose.yml;
  arrStackModuleText = builtins.readFile ../../../home/linux/arr-stack/default.nix;
  libraryDeclarationText = builtins.readFile ../../../home/linux/arr-stack/scripts/arr_users/jellyfin_library_declaration.py;
  friendPolicyText = builtins.readFile ../../../home/linux/arr-stack/scripts/arr_users/friend_account_policy.py;
  radarrRootFolderText = builtins.readFile ../../../nixos/modules/arr-config-provisioner/desired-state/radarr/rootfolder.json;
  sonarrRootFolderText = builtins.readFile ../../../nixos/modules/arr-config-provisioner/desired-state/sonarr/rootfolder.json;

  privateMediaSubdirectories = [
    "media/movies-private"
    "media/tv-private"
  ];
  everyPrivateDirectoryIsCreatedOnRebuild = builtins.all (
    subdirectory: lib.hasInfix ''"${subdirectory}"'' arrStackModuleText
  ) privateMediaSubdirectories;
  everyPrivateLibraryPathHasABackingDirectory = builtins.all (
    subdirectory: lib.hasInfix ''"/${subdirectory}"'' libraryDeclarationText
  ) privateMediaSubdirectories;
  privateRootFoldersDeclaredForArrApps =
    lib.hasInfix "/data/media/movies-private" radarrRootFolderText
    && lib.hasInfix "/data/media/tv-private" sonarrRootFolderText;
  friendPolicyNeverGrantsEveryFolder =
    !(lib.hasInfix ''"EnableAllFolders": True'' friendPolicyText)
    && lib.hasInfix ''visibility_policy["EnableAllFolders"] = False'' friendPolicyText;
  jellyfinMountsTheWholeMediaRootReadOnly = lib.hasInfix "\${ARR_DATA_ROOT}/media:/media:ro" composeText;
in
{
  chise-arr-private-media-directories-created-on-rebuild =
    mkEvalCheck "chise-arr-private-media-directories-created-on-rebuild"
      everyPrivateDirectoryIsCreatedOnRebuild
      "the module activation must create media/movies-private and media/tv-private, or the private Jellyfin libraries and the private *arr root folders would both point at paths that do not exist and a private grab would fail its import";

  chise-arr-private-library-paths-match-created-directories =
    mkEvalCheck "chise-arr-private-library-paths-match-created-directories"
      everyPrivateLibraryPathHasABackingDirectory
      "every private path in the Jellyfin library declaration must correspond to a directory the module creates under the media root; jellyfin mounts data/media at /media, so a declared /media/<x> with no data/media/<x> behind it would provision an empty library that silently never fills";

  chise-arr-private-root-folders-declared-for-arr-apps =
    mkEvalCheck "chise-arr-private-root-folders-declared-for-arr-apps"
      privateRootFoldersDeclaredForArrApps
      "radarr and sonarr must each carry the private root folder in the committed desired state, or a wiped config dir would come back with only the public root and there would be nowhere to send a private grab";

  chise-arr-friend-policy-never-grants-every-folder =
    mkEvalCheck "chise-arr-friend-policy-never-grants-every-folder" friendPolicyNeverGrantsEveryFolder
      "the friend policy must never set EnableAllFolders true and must pin it false when it writes library visibility; EnableAllFolders true overrides EnabledFolders entirely in Jellyfin, so reintroducing it would hand every friend the private libraries no matter what the enabled list says";

  chise-arr-jellyfin-mounts-media-root-read-only =
    mkEvalCheck "chise-arr-jellyfin-mounts-media-root-read-only" jellyfinMountsTheWholeMediaRootReadOnly
      "jellyfin must keep mounting the whole media root read-only at /media, so a newly declared private library needs no compose change to be served and no Jellyfin client can ever write into the library";
}
