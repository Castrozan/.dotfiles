{
  helpers,
  lib,
  pkgs,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  extensionRepositoriesModule = import ../suwayomi-extension-repositories-nixos.nix {
    inherit lib pkgs;
  };
  provisionerUnit = extensionRepositoriesModule.systemd.services.suwayomi-extension-repositories;
  environmentText = lib.concatStringsSep " " (
    lib.mapAttrsToList (name: value: "${name}=${value}") provisionerUnit.environment
  );

  serverModuleText = builtins.readFile ../../suwayomi-server-nixos.nix;
  provisionerModuleText = builtins.readFile ../suwayomi-extension-repositories-nixos.nix;
  clientText = builtins.readFile ../scripts/suwayomi_extension_repositories/suwayomi_graphql_client.py;
  miwayomiClientText = builtins.readFile ../scripts/suwayomi_extension_repositories/miwayomi_rest_client.py;
  miwayomiReconcileText = builtins.readFile ../scripts/suwayomi_extension_repositories/miwayomi_extension_synchronization.py;
  commandText = builtins.readFile ../scripts/suwayomi_extension_repositories/__main__.py;
  reconcileText = builtins.readFile ../scripts/suwayomi_extension_repositories/extension_repository_synchronization.py;
  declarationText = builtins.readFile ../scripts/suwayomi_extension_repositories/runtime_configuration.py;
  secretDeclarationText = builtins.readFile ../../../../../secrets/secrets.nix;

  synchronizationTestText = builtins.readFile ./unit/test_extension_repository_synchronization.py;

  publicRepositoryNamesNoRepositoryUrl =
    builtins.all (trackedText: !(lib.hasInfix "index.min.json" trackedText))
      [
        provisionerModuleText
        serverModuleText
        declarationText
        reconcileText
        clientText
        miwayomiClientText
        miwayomiReconcileText
        commandText
        synchronizationTestText
      ];

  declaredRepositoryListDigest = builtins.hashFile "sha256" ../../../../../secrets/credentials/suwayomi-extension-repositories.age;

  aChangedListReachesTheRunningServer = lib.hasInfix "SUWAYOMI_EXTENSION_REPOSITORIES_DECLARATION_DIGEST=${declaredRepositoryListDigest}" environmentText;

  theListComesFromAnEncryptedFile =
    lib.hasInfix "SUWAYOMI_EXTENSION_REPOSITORIES_FILE=/run/agenix/" environmentText
    && lib.hasInfix "suwayomi-extension-repositories.age" secretDeclarationText;

  theRepositoriesAreNeverForcedAsAJvmProperty = !(lib.hasInfix "extensionRepos" serverModuleText);

  theProvisionerFollowsTheServerItConfigures =
    provisionerUnit.after == [ "suwayomi-server.service" ]
    && provisionerUnit.requires == [ "suwayomi-server.service" ]
    && provisionerUnit.wantedBy == [ "multi-user.target" ]
    && provisionerUnit.serviceConfig.RemainAfterExit
    && provisionerUnit.serviceConfig.User == "zanoni";

  theProvisionerShipsWithEveryServer = lib.hasInfix "./extension-repositories/suwayomi-extension-repositories-nixos.nix" serverModuleText;

  theProvisionerReachesTheAddressTheServerBindsTo =
    lib.hasInfix "import ../../tailnet-bind-address.nix" provisionerModuleText
    && lib.hasInfix "import ../tailnet-bind-address.nix" serverModuleText;

  aHostWithoutTheSecretLeavesSuwayomiAlone =
    lib.hasInfix "if not list_file_path.is_file()" declarationText
    && lib.hasInfix "return None" declarationText
    && lib.hasInfix "if declared_repository_urls is None" reconcileText;

  anEmptyDeclarationRefusesToRun =
    lib.hasInfix "leave the server unable" declarationText
    && lib.hasInfix "raise SystemExit(1)" declarationText;

  aWriteThatDoesNotStickIsCaught =
    lib.hasInfix "if written_repository_urls != declared_repository_urls" reconcileText
    && lib.hasInfix "raise ValueError" reconcileText;

  anUnchangedListIsNeverRewritten = lib.hasInfix "if current_repository_urls == declared_repository_urls" reconcileText;

  aFailedIndexNeverFailsTheStoredDeclaration =
    lib.hasInfix "def count_extensions_offered" clientText
    && lib.hasInfix "except (ValueError, urllib.error.URLError, OSError)" clientText;

  theErrorMessageDropsTheJavaStackTrace = lib.hasInfix "def first_line_of" clientText;

  theDeclarationNeverSecondGuessesWhichHostsSuwayomiAccepts =
    !(lib.hasInfix "startswith" declarationText) && !(lib.hasInfix "githubusercontent" declarationText);
in
{
  suwayomi-the-public-repo-names-no-extension-repository =
    mkEvalCheck "suwayomi-the-public-repo-names-no-extension-repository"
      publicRepositoryNamesNoRepositoryUrl
      "no module or script in this public repository may spell an extension repository URL; the list says which sources this machine reads and belongs in the encrypted file, so a URL landing back in a tracked nix file would publish it in every future clone of the history";

  suwayomi-the-repository-list-comes-from-an-encrypted-file =
    mkEvalCheck "suwayomi-the-repository-list-comes-from-an-encrypted-file"
      theListComesFromAnEncryptedFile
      "the unit must read the list from an agenix path and the secret must be declared with its recipients; pointing at an undeclared path would leave the file absent after a rebuild and the provisioner would silently skip on every boot";

  suwayomi-a-changed-list-reaches-the-running-server =
    mkEvalCheck "suwayomi-a-changed-list-reaches-the-running-server" aChangedListReachesTheRunningServer
      "the unit must carry a digest of the encrypted list, computed from the file rather than written down, because nothing else in the unit changes when the list does: the decrypted path is a fixed string, so a rebuild that only re-encrypts the list gives the switch no reason to restart the provisioner and Suwayomi keeps serving the previous repositories until the next reboot, with the declaration and the running server disagreeing and both looking healthy";

  suwayomi-extension-repositories-are-never-forced-as-a-jvm-property =
    mkEvalCheck "suwayomi-extension-repositories-are-never-forced-as-a-jvm-property"
      theRepositoriesAreNeverForcedAsAJvmProperty
      "extensionRepos must never join the forced JVM settings; a system property is always a string to typesafe config, so Suwayomi reads a forced list as STRING rather than LIST and then fails every settings query with a WrongType exception";

  suwayomi-extension-repositories-follow-the-server =
    mkEvalCheck "suwayomi-extension-repositories-follow-the-server"
      theProvisionerFollowsTheServerItConfigures
      "the provisioner must remain active as the secret-owning user, require and follow the system Suwayomi container, and start with the machine, or it would race startup, lose secret access, or evade restart when the declaration changes";

  suwayomi-extension-repositories-ship-with-every-server =
    mkEvalCheck "suwayomi-extension-repositories-ship-with-every-server"
      theProvisionerShipsWithEveryServer
      "the server module must import the provisioner itself, so a host that gains Suwayomi cannot get the server without the repository declaration and end up serving an instance that can install nothing";

  suwayomi-extension-repositories-reach-the-bound-address =
    mkEvalCheck "suwayomi-extension-repositories-reach-the-bound-address"
      theProvisionerReachesTheAddressTheServerBindsTo
      "both modules must derive the bind address from the same file; Suwayomi listens only on the tailnet address, so a provisioner that guessed loopback instead would never connect and the declared list would silently never be applied";

  suwayomi-a-host-without-the-secret-leaves-suwayomi-alone =
    mkEvalCheck "suwayomi-a-host-without-the-secret-leaves-suwayomi-alone"
      aHostWithoutTheSecretLeavesSuwayomiAlone
      "an absent list file must skip the reconcile rather than fail it; the server module is imported by hosts that hold no such secret, and failing there would turn every one of their rebuilds red over a file they are not meant to have";

  suwayomi-the-declaration-never-second-guesses-which-hosts-suwayomi-accepts =
    mkEvalCheck "suwayomi-the-declaration-never-second-guesses-which-hosts-suwayomi-accepts"
      theDeclarationNeverSecondGuessesWhichHostsSuwayomiAccepts
      "the declaration must not filter entries by host prefix: which URLs Suwayomi accepts is a property of the server release and widened between 2.1 and 2.3, so a copy of that rule here goes stale silently and starts dropping repositories the running server would have taken; the echo-back comparison is what catches a rejected list, and it needs no guess about why";

  suwayomi-an-empty-declaration-refuses-to-run =
    mkEvalCheck "suwayomi-an-empty-declaration-refuses-to-run" anEmptyDeclarationRefusesToRun
      "a decrypted but empty list must abort rather than be written; writing it would clear every repository and leave the server unable to install or update any source, with nothing in the config left to say what was lost";

  suwayomi-a-write-that-does-not-stick-is-caught =
    mkEvalCheck "suwayomi-a-write-that-does-not-stick-is-caught" aWriteThatDoesNotStickIsCaught
      "the reconcile must compare what Suwayomi echoes back against what was declared; the settings mutation reports success while silently keeping the old list when it rejects a value, and it validates the whole list at once so one unacceptable entry takes every other repository down with it, which makes this comparison the only thing standing between a rejected list and a rebuild that reports the repositories as configured";

  suwayomi-an-unchanged-list-is-never-rewritten =
    mkEvalCheck "suwayomi-an-unchanged-list-is-never-rewritten" anUnchangedListIsNeverRewritten
      "an unchanged list must skip the write, so an ordinary rebuild does not trigger a fresh index of every repository and the unit stays quiet and fast when nothing changed";

  suwayomi-a-failed-index-never-fails-the-declaration =
    mkEvalCheck "suwayomi-a-failed-index-never-fails-the-declaration"
      aFailedIndexNeverFailsTheStoredDeclaration
      "indexing the repositories must be allowed to fail without failing the unit; one slow or unreachable repository is ordinary and the declared list is already stored by then, so treating it as fatal would report a correct configuration as a broken rebuild";

  suwayomi-the-error-message-drops-the-java-stack-trace =
    mkEvalCheck "suwayomi-the-error-message-drops-the-java-stack-trace"
      theErrorMessageDropsTheJavaStackTrace
      "a GraphQL error must be reduced to its first line before it is printed, because Suwayomi returns a full Kotlin stack trace in the message and the journal entry becomes unreadable at exactly the moment someone is trying to read it";
}
