{
  helpers,
  lib,
  pkgs,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  extensionRepositoriesModule = import ../suwayomi-extension-repositories-home-manager.nix {
    inherit lib pkgs;
  };
  provisionerUnit = extensionRepositoriesModule.systemd.user.services.suwayomi-extension-repositories;
  environmentText = lib.concatStringsSep " " provisionerUnit.Service.Environment;

  serverModuleText = builtins.readFile ../../suwayomi-server-home-manager.nix;
  provisionerModuleText = builtins.readFile ../suwayomi-extension-repositories-home-manager.nix;
  clientText = builtins.readFile ../scripts/suwayomi_extension_repositories/suwayomi_graphql_client.py;
  reconcileText = builtins.readFile ../scripts/suwayomi_extension_repositories/extension_repository_synchronization.py;
  declarationText = builtins.readFile ../scripts/suwayomi_extension_repositories/runtime_configuration.py;
  secretDeclarationText = builtins.readFile ../../../../../secrets/secrets.nix;

  publicRepositoryNamesNoRepositoryUrl =
    builtins.all (moduleText: !(lib.hasInfix "index.min.json" moduleText))
      [
        provisionerModuleText
        serverModuleText
        declarationText
        reconcileText
      ];

  theListComesFromAnEncryptedFile =
    lib.hasInfix "SUWAYOMI_EXTENSION_REPOSITORIES_FILE=/run/agenix/" environmentText
    && lib.hasInfix "suwayomi-extension-repositories.age" secretDeclarationText;

  theRepositoriesAreNeverForcedAsAJvmProperty = !(lib.hasInfix "extensionRepos" serverModuleText);

  theProvisionerFollowsTheServerItConfigures =
    provisionerUnit.Unit.After == [ "suwayomi-server.service" ]
    && provisionerUnit.Unit.Requires == [ "suwayomi-server.service" ]
    && provisionerUnit.Install.WantedBy == [ "default.target" ];

  theProvisionerShipsWithEveryServer = lib.hasInfix "./extension-repositories/suwayomi-extension-repositories-home-manager.nix" serverModuleText;

  theProvisionerReachesTheAddressTheServerBindsTo =
    lib.hasInfix "import ../tailnet-bind-address.nix" provisionerModuleText
    && lib.hasInfix "import ./tailnet-bind-address.nix" serverModuleText;

  aHostWithoutTheSecretLeavesSuwayomiAlone =
    lib.hasInfix "if not list_file_path.is_file()" declarationText
    && lib.hasInfix "return None" declarationText
    && lib.hasInfix "if declared_repository_urls is None" reconcileText;

  anEmptyDeclarationRefusesToRun =
    lib.hasInfix "leave Suwayomi " declarationText
    && lib.hasInfix "raise SystemExit(1)" declarationText;

  aWriteThatDoesNotStickIsCaught =
    lib.hasInfix "if written_repository_urls != declared_repository_urls" reconcileText
    && lib.hasInfix "raise ValueError" reconcileText;

  anUnchangedListIsNeverRewritten = lib.hasInfix "if current_repository_urls == declared_repository_urls" reconcileText;

  aFailedIndexNeverFailsTheStoredDeclaration =
    lib.hasInfix "def count_extensions_offered" clientText
    && lib.hasInfix "except (ValueError, urllib.error.URLError, OSError)" clientText;

  theErrorMessageDropsTheJavaStackTrace = lib.hasInfix "def first_line_of" clientText;
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

  suwayomi-extension-repositories-are-never-forced-as-a-jvm-property =
    mkEvalCheck "suwayomi-extension-repositories-are-never-forced-as-a-jvm-property"
      theRepositoriesAreNeverForcedAsAJvmProperty
      "extensionRepos must never join the forced JVM settings; a system property is always a string to typesafe config, so Suwayomi reads a forced list as STRING rather than LIST and then fails every settings query with a WrongType exception";

  suwayomi-extension-repositories-follow-the-server =
    mkEvalCheck "suwayomi-extension-repositories-follow-the-server"
      theProvisionerFollowsTheServerItConfigures
      "the provisioner must require and follow suwayomi-server and start with the user session, or it would race the server's startup and write settings the server then overwrites from its own stored config";

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

  suwayomi-an-empty-declaration-refuses-to-run =
    mkEvalCheck "suwayomi-an-empty-declaration-refuses-to-run" anEmptyDeclarationRefusesToRun
      "a decrypted but empty list must abort rather than be written; writing it would clear every repository and leave the server unable to install or update any source, with nothing in the config left to say what was lost";

  suwayomi-a-write-that-does-not-stick-is-caught =
    mkEvalCheck "suwayomi-a-write-that-does-not-stick-is-caught" aWriteThatDoesNotStickIsCaught
      "the reconcile must compare what Suwayomi echoes back against what was declared; the settings mutation reports success while silently keeping the old list when it rejects a value, so trusting the response would report a repository as configured when it is not";

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
