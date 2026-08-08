{
  helpers,
  lib,
  self,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  nixosCfg = self.nixosConfigurations.chise.config;
  provisionerConfig = nixosCfg.custom.kavitaLibraryAccessProvisioner;
  provisionerUnit = nixosCfg.systemd.services.kavita-library-access-provisioner;

  declarationText = builtins.readFile ../../users/scripts/arr_users/kavita_library_declaration.py;
  accountPolicyText = builtins.readFile ../../users/scripts/arr_users/kavita_account_policy.py;
  reconcileText = builtins.readFile ../../users/scripts/arr_users/kavita_access_synchronization.py;
  sourceFolderText = builtins.readFile ../../users/scripts/arr_users/kavita_library_source_folders.py;
  moduleText = builtins.readFile ../kavita-library-access-provisioner-nixos.nix;
  composeText = builtins.readFile ../../stack/docker-compose.yml;

  friendAccessIsAnExplicitAllowlist =
    lib.hasInfix "def resolve_public_library_ids" declarationText
    && lib.hasInfix "refusing to write a Kavita account policy" declarationText
    && lib.hasInfix "raise ValueError" declarationText;

  privilegeIsANamedAllowlistNotARoleTest =
    lib.hasInfix "def account_sees_every_library" declarationText
    && !(lib.hasInfix "Admin" declarationText);

  everyAccountIsRewrittenOnEveryRun =
    lib.hasInfix "for kavita_user in kavita_users" reconcileText
    && !(lib.hasInfix "continue" (
      lib.last (lib.splitString "def reconcile_account_library_access" reconcileText)
    ));

  aFriendNeverKeepsAPrivilegedRole =
    lib.hasInfix ''"Admin",'' accountPolicyText
    && lib.hasInfix ''"Promote",'' accountPolicyText
    && lib.hasInfix ''"ChangeRestriction",'' accountPolicyText
    && lib.hasInfix "if role_name not in PRIVILEGED_KAVITA_ROLES" accountPolicyText;

  theWriteAlwaysCarriesAnExplicitLibraryList = lib.hasInfix ''"libraries": list(visible_library_ids)'' accountPolicyText;

  sourceFoldersAreNeverBlankedByAnEmptyRoot =
    lib.hasInfix "if not host_root.is_dir()" sourceFolderText
    && lib.hasInfix "if not reconciled_library_name or not source_library_folders" reconcileText;

  sourceFoldersComeFromTheDeclaredRoot =
    lib.hasInfix "runtime_credentials.kavita_source_root_host_path()" sourceFolderText
    && lib.hasInfix "runtime_credentials.kavita_source_root_container_path()" sourceFolderText
    && !(lib.hasInfix "/manga" sourceFolderText);

  theAllowlistIsDeclaredRatherThanHardcoded =
    lib.hasInfix "runtime_credentials.kavita_public_library_names()" declarationText
    && lib.hasInfix "builtins.toJSON kavitaLibraryAccessProvisionerConfig.publicLibraryNames" moduleText;

  chiseDeclaresAPublicLibraryAndAnOwner =
    provisionerConfig.enable
    && provisionerConfig.publicLibraryNames != [ ]
    && provisionerConfig.privilegedAccountUsernames != [ ];

  chiseKeepsTheAdminKeyOnLoopback =
    provisionerConfig.kavitaBaseUrl == "http://127.0.0.1:5000"
    && lib.hasInfix "kavita-admin-api-key" provisionerUnit.environment.ARR_USERS_KAVITA_API_KEY_FILE;

  chiseRunsTheReconcileOnEveryBoot =
    builtins.elem "multi-user.target" provisionerUnit.wantedBy
    && provisionerUnit.serviceConfig.Type == "oneshot"
    && lib.hasInfix "sync-kavita-access" provisionerUnit.serviceConfig.ExecStart;

  chiseSourceRootMatchesTheKavitaMount =
    lib.hasInfix "\${ARR_DATA_ROOT}/manga/mangas:${provisionerConfig.sourceRootContainerPath}:ro" composeText
    && lib.hasSuffix "manga/mangas" provisionerConfig.sourceRootHostPath;

  chiseNeverDeclaresTheOwnerAsAFriend =
    lib.intersectLists provisionerConfig.privilegedAccountUsernames provisionerConfig.friendAccountUsernames
    == [ ];
in
{
  chise-kavita-friend-access-is-an-explicit-allowlist =
    mkEvalCheck "chise-kavita-friend-access-is-an-explicit-allowlist" friendAccessIsAnExplicitAllowlist
      "which Kavita libraries a friend reads must resolve from the declared allowlist and refuse the write when a declared library is missing; without that refusal a renamed library would resolve to no id and the reconcile would hand every friend an empty list or, worse, fall through to whatever ids Kavita happened to return";

  chise-kavita-privilege-is-a-named-allowlist =
    mkEvalCheck "chise-kavita-privilege-is-a-named-allowlist" privilegeIsANamedAllowlistNotARoleTest
      "who reads every Kavita library must stay a named account allowlist rather than a test for the Admin role; Kavita's registration flow is open on this host, so a role test would promote anyone who ever acquired Admin into seeing the withheld libraries, and the reconcile is the very thing that strips Admin";

  chise-kavita-every-account-is-rewritten-on-every-run =
    mkEvalCheck "chise-kavita-every-account-is-rewritten-on-every-run" everyAccountIsRewrittenOnEveryRun
      "the reconcile must walk every Kavita account without skipping any, because a friend picks their own username when they accept an invite; skipping unknown accounts would leave a self-registered reader holding whatever libraries Kavita granted them at signup";

  chise-kavita-a-friend-never-keeps-a-privileged-role =
    mkEvalCheck "chise-kavita-a-friend-never-keeps-a-privileged-role" aFriendNeverKeepsAPrivilegedRole
      "Admin, Promote and ChangeRestriction must all be stripped from every non-privileged account; any one of them left in place lets a friend grant themselves the withheld libraries through the Kavita UI, which makes the whole allowlist advisory";

  chise-kavita-the-write-always-carries-an-explicit-library-list =
    mkEvalCheck "chise-kavita-the-write-always-carries-an-explicit-library-list"
      theWriteAlwaysCarriesAnExplicitLibraryList
      "the account update must always name the full library list it intends; Kavita replaces an account's libraries with exactly what the payload carries, so omitting the key on a partial update would leave the previous grant untouched and the reconcile would silently do nothing";

  chise-kavita-source-folders-are-never-blanked-by-an-empty-root =
    mkEvalCheck "chise-kavita-source-folders-are-never-blanked-by-an-empty-root"
      sourceFoldersAreNeverBlankedByAnEmptyRoot
      "an absent or empty source root must leave the library folders alone; writing the empty list it would otherwise produce would unpoint the manga library entirely and Kavita would drop every series on the next scan";

  chise-kavita-source-folders-come-from-the-declared-root =
    mkEvalCheck "chise-kavita-source-folders-come-from-the-declared-root"
      sourceFoldersComeFromTheDeclaredRoot
      "the source directories must be enumerated from the declared root rather than from a path spelled into the script, so the host path and the container path stay the module's to change and cannot drift from the compose mount";

  chise-kavita-the-allowlist-is-declared-rather-than-hardcoded =
    mkEvalCheck "chise-kavita-the-allowlist-is-declared-rather-than-hardcoded"
      theAllowlistIsDeclaredRatherThanHardcoded
      "the public library allowlist must travel from the nix option into the reconcile, so the boundary is reviewable in the host configuration instead of buried in a script the rebuild copies into the store";

  chise-kavita-declares-a-public-library-and-an-owner =
    mkEvalCheck "chise-kavita-declares-a-public-library-and-an-owner"
      chiseDeclaresAPublicLibraryAndAnOwner
      "chise must declare both a public library and a privileged account; with no public library every friend loses access on the next rebuild, and with no privileged account the reconcile would strip Admin from the owner and leave nobody able to administer Kavita";

  chise-kavita-admin-key-stays-on-loopback =
    mkEvalCheck "chise-kavita-admin-key-stays-on-loopback" chiseKeepsTheAdminKeyOnLoopback
      "the provisioner must reach Kavita over loopback with the agenix-held admin key; pointing it at the tailnet or the funnel would put a key that can rewrite every account's library access onto the wire";

  chise-kavita-reconcile-runs-on-every-boot =
    mkEvalCheck "chise-kavita-reconcile-runs-on-every-boot" chiseRunsTheReconcileOnEveryBoot
      "the reconcile must be a oneshot wanted by multi-user.target running the sync-kavita-access command, so a friend who changed their own access through the UI loses it again at the next rebuild or boot rather than keeping it until someone notices";

  chise-kavita-source-root-matches-the-container-mount =
    mkEvalCheck "chise-kavita-source-root-matches-the-container-mount"
      chiseSourceRootMatchesTheKavitaMount
      "the declared source root must be the same directory the compose file mounts into Kavita, host side and container side; a mismatch would write folder paths Kavita cannot see and the library would come back empty after the rescan the repoint triggers";

  chise-kavita-never-declares-the-owner-as-a-friend =
    mkEvalCheck "chise-kavita-never-declares-the-owner-as-a-friend" chiseNeverDeclaresTheOwnerAsAFriend
      "no account may appear in both the privileged list and the friend roster, because the two carry opposite intents and the overlap reads as though the owner were scoped to the public libraries while the code silently grants them everything";
}
