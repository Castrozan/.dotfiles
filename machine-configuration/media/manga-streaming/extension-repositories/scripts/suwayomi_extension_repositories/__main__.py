import sys
import urllib.error

import extension_repository_synchronization
import miwayomi_extension_synchronization
import miwayomi_rest_client
import runtime_configuration


def command_target():
    if not sys.argv[1:]:
        return extension_repository_synchronization.suwayomi_server()
    if sys.argv[1:] == ["miwayomi"]:
        return extension_repository_synchronization.RepositoryServer(
            name="Miwayomi",
            url=runtime_configuration.miwayomi_base_url(),
            client=miwayomi_rest_client,
            repository_file_variable=runtime_configuration.MIWAYOMI_REPOSITORY_LIST_FILE_VARIABLE,
            reports_extension_count=False,
        )
    print("expected no target or the miwayomi target", file=sys.stderr)
    raise SystemExit(2)


def report_repository_synchronization(server, synchronized):
    if synchronized["repositories"] is None:
        print(
            f"no declared repository list at {runtime_configuration.declared_repository_list_file(server.repository_file_variable)}, "
            f"so {server.name}'s own repositories were left alone"
        )
    elif not synchronized["rewritten"]:
        print("already declared, nothing rewritten")
    elif not server.reports_extension_count:
        print("repositories rewritten and echo verified")
    elif synchronized["extensions_offered"] is None:
        print(
            f"repositories rewritten, but {server.name} could not index them right now; "
            "it retries on its own and the declared list is already stored"
        )
    else:
        print(f"extensions now offered: {synchronized['extensions_offered']}")


def main():
    server = command_target()
    try:
        synchronized_repositories = (
            extension_repository_synchronization.synchronize_extension_repositories(
                server
            )
        )
        synchronized_extensions = None
        if sys.argv[1:] == ["miwayomi"]:
            synchronized_extensions = miwayomi_extension_synchronization.synchronize_extensions(
                server.url,
                miwayomi_extension_synchronization.ExtensionPolicy(
                    removed_packages=runtime_configuration.removed_miwayomi_extension_packages()
                ),
                miwayomi_rest_client,
            )
    except ValueError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from error
    except urllib.error.URLError as error:
        print(f"cannot reach {server.name}: {error.reason}", file=sys.stderr)
        raise SystemExit(1) from error
    report_repository_synchronization(server, synchronized_repositories)
    if synchronized_extensions is not None:
        removed_packages = synchronized_extensions["removed_packages"]
        if removed_packages:
            print(f"extensions removed: {', '.join(removed_packages)}")
        else:
            print("extension package policy already declared")


if __name__ == "__main__":
    main()
