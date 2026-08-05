{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  composeText = builtins.readFile ../../stack/docker-compose.yml;
  arrStackModuleText = builtins.readFile ../../stack/arr-stack-home-manager.nix;
  libraryDeclarationText = builtins.readFile ../scripts/arr_users/jellyfin_library_declaration.py;
  friendPolicyText = builtins.readFile ../scripts/arr_users/friend_account_policy.py;
  radarrRootFolderText = builtins.readFile ../../configuration/desired-state/radarr/rootfolder.json;
  sonarrRootFolderText = builtins.readFile ../../configuration/desired-state/sonarr/rootfolder.json;

  requestRoutingText = builtins.readFile ../scripts/arr_users/private_request_routing.py;
  visibilityReconcileText = builtins.readFile ../scripts/arr_users/library_access_synchronization.py;
  accountPermissionsText = builtins.readFile ../scripts/arr_users/jellyseerr_account_permissions.py;
  permissionReconcileText = builtins.readFile ../scripts/arr_users/account_permission_synchronization.py;

  everyAccountHoldsTheSamePermissionsAsAFriend =
    lib.hasInfix "friend_account_policy.FRIEND_JELLYSEERR_PERMISSIONS_BITMASK" accountPermissionsText
    && lib.hasInfix "SELF_APPROVING_REQUESTER_PERMISSIONS" accountPermissionsText;
  jellyseerrKeepsADeclaredAdministrator =
    lib.hasInfix "administrator_accounts" permissionReconcileText
    && lib.hasInfix "raise ValueError" permissionReconcileText;

  privateAccessIsAnExplicitAllowlist =
    lib.hasInfix "PRIVATE_LIBRARY_ACCOUNT_USERNAMES" libraryDeclarationText
    && lib.hasInfix "def resolve_visible_library_ids" libraryDeclarationText;
  privateAccessNamesTheAdministratorByReference =
    lib.hasInfix "jellyseerr_account_permissions.JELLYSEERR_ADMINISTRATOR_ACCOUNT_USERNAMES" libraryDeclarationText
    && !(lib.hasInfix ''"jellyseerr"'' libraryDeclarationText);
  reconcileNeverExemptsAnAdministrator = !(lib.hasInfix "is_administrator" visibilityReconcileText);

  privateMediaSubdirectories = [
    "media/movies-private"
    "media/tv-private"
  ];
  routedRootFoldersExistInArrApps =
    lib.hasInfix ''PRIVATE_MOVIE_ROOT_FOLDER = "/data/media/movies-private"'' requestRoutingText
    && lib.hasInfix ''PRIVATE_SERIES_ROOT_FOLDER = "/data/media/tv-private"'' requestRoutingText;
  animeSeriesGetTheirOwnRoutingRule = lib.hasInfix "TMDB_ANIME_KEYWORD_ID" requestRoutingText;
  routedAccountLosesOverridesWhenPrivileged =
    lib.hasInfix "JELLYSEERR_PERMISSION_ADMIN" requestRoutingText
    && lib.hasInfix "JELLYSEERR_PERMISSION_MANAGE_REQUESTS" requestRoutingText;
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

  chise-arr-routed-root-folders-match-the-arr-desired-state =
    mkEvalCheck "chise-arr-routed-root-folders-match-the-arr-desired-state"
      routedRootFoldersExistInArrApps
      "the root folders the Jellyseerr override rules send private requests to must be spelled exactly as radarr and sonarr declare them; Jellyseerr saves a rule naming an unknown root folder without complaint and the mismatch only surfaces later, when the grab fails to import";

  chise-arr-anime-series-get-their-own-routing-rule =
    mkEvalCheck "chise-arr-anime-series-get-their-own-routing-rule" animeSeriesGetTheirOwnRoutingRule
      "a second series rule carrying the anime keyword is mandatory, because Jellyseerr drops every override rule for an anime show unless the rule names that keyword itself, so without it a privately requested anime would land in the public library";

  chise-arr-routed-account-privilege-is-checked =
    mkEvalCheck "chise-arr-routed-account-privilege-is-checked"
      routedAccountLosesOverridesWhenPrivileged
      "the reconciler must keep refusing a routing account that holds Jellyseerr admin or manage-requests, because Jellyseerr skips override rules entirely for those accounts and the private route would read as configured while every request landed in public view";

  chise-arr-private-access-is-an-explicit-allowlist =
    mkEvalCheck "chise-arr-private-access-is-an-explicit-allowlist" privateAccessIsAnExplicitAllowlist
      "which accounts see the private libraries must stay a named allowlist resolved per account, not a role test; the owner's own admin account is deliberately outside it, so collapsing this back to administrator-sees-everything would silently put private media back in the daily-driver account";

  chise-arr-private-access-names-the-administrator-by-reference =
    mkEvalCheck "chise-arr-private-access-names-the-administrator-by-reference"
      privateAccessNamesTheAdministratorByReference
      "the library allowlist must take the break-glass account's name from the Jellyseerr permission declaration instead of spelling it a second time; the two literals would drift on a rename and the sole remaining Jellyseerr administrator would quietly lose the private libraries it is the only account allowed to watch";

  chise-arr-visibility-reconcile-never-exempts-an-administrator =
    mkEvalCheck "chise-arr-visibility-reconcile-never-exempts-an-administrator"
      reconcileNeverExemptsAnAdministrator
      "the visibility reconcile must apply to administrators as well; reintroducing an is_administrator skip there would leave the owner's admin account permanently able to see the private libraries no matter what the allowlist declares";

  chise-arr-no-request-waits-on-an-approval =
    mkEvalCheck "chise-arr-no-request-waits-on-an-approval" everyAccountHoldsTheSamePermissionsAsAFriend
      "the permissions pinned onto every non-administrator account must be the very friend bitmask rather than a second literal spelling of it; the two would otherwise drift and an account left without auto-approve would sit pending forever, because the only accounts that could approve it are the ones this reconcile is demoting";

  chise-arr-jellyseerr-keeps-a-declared-administrator =
    mkEvalCheck "chise-arr-jellyseerr-keeps-a-declared-administrator"
      jellyseerrKeepsADeclaredAdministrator
      "the permission reconcile must refuse to run when it would leave no declared administrator; demoting the last one is unrecoverable through the web UI, because granting admin back is itself an admin-gated action and no remaining account could perform it";

  chise-arr-jellyfin-mounts-media-root-read-only =
    mkEvalCheck "chise-arr-jellyfin-mounts-media-root-read-only" jellyfinMountsTheWholeMediaRootReadOnly
      "jellyfin must keep mounting the whole media root read-only at /media, so a newly declared private library needs no compose change to be served and no Jellyfin client can ever write into the library";
}
