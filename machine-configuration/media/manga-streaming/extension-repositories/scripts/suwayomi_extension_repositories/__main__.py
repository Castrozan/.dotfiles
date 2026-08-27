import sys
import urllib.error

import extension_repository_synchronization
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


def main():
    server = command_target()
    try:
        synchronized = (
            extension_repository_synchronization.synchronize_extension_repositories(
                server
            )
        )
    except ValueError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from error
    except urllib.error.URLError as error:
        print(f"cannot reach {server.name}: {error.reason}", file=sys.stderr)
        raise SystemExit(1) from error
    if synchronized["repositories"] is None:
        print(
            f"no declared repository list at {runtime_configuration.declared_repository_list_file(server.repository_file_variable)}, "
            f"so {server.name}'s own repositories were left alone"
        )
        return
    if not synchronized["rewritten"]:
        print("already declared, nothing rewritten")
        return
    if not server.reports_extension_count:
        print("repositories rewritten and echo verified")
        return
    extensions_offered = synchronized["extensions_offered"]
    if extensions_offered is None:
        print(
            f"repositories rewritten, but {server.name} could not index them right now; "
            "it retries on its own and the declared list is already stored"
        )
        return
    print(f"extensions now offered: {extensions_offered}")


if __name__ == "__main__":
    main()
