import json
from pathlib import Path
import subprocess
import sys

QUERY_BATCH_SIZE = 500
QUERY_TIMEOUT_SECONDS = 300
EVALUATION_TIMEOUT_SECONDS = 900
CHECK_DERIVATIONS_EXPRESSION = (
    "checks: map (check: check.drvPath) (builtins.attrValues checks)"
)


class NixStore:
    def __init__(self, flake_arguments):
        self.flake_arguments = flake_arguments

    def _lines(self, command):
        completed = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
            timeout=QUERY_TIMEOUT_SECONDS,
        )
        return completed.stdout.splitlines()

    def _batched_lines(self, command, paths):
        lines = []
        for start in range(0, len(paths), QUERY_BATCH_SIZE):
            lines.extend(
                self._lines([*command, *paths[start : start + QUERY_BATCH_SIZE]])
            )
        return lines

    def check_derivations(self, system):
        completed = subprocess.run(
            [
                "nix",
                "eval",
                "--json",
                *self.flake_arguments,
                f".#checks.{system}",
                "--apply",
                CHECK_DERIVATIONS_EXPRESSION,
            ],
            check=True,
            stdout=subprocess.PIPE,
            text=True,
            timeout=EVALUATION_TIMEOUT_SECONDS,
        )
        return json.loads(completed.stdout)

    def outputs(self, derivations):
        return self._batched_lines(["nix-store", "--query", "--outputs"], derivations)

    def closure_with_outputs(self, derivations):
        return self._batched_lines(
            ["nix-store", "--query", "--requisites", "--include-outputs"], derivations
        )

    def derivers(self, paths):
        return self._batched_lines(["nix-store", "--query", "--deriver"], paths)

    def signatures(self, paths):
        return self._batched_lines(["nix", "path-info", "--sigs"], paths)

    def add_roots(self, paths, root_directory):
        root_directory.mkdir(parents=True, exist_ok=True)
        for start in range(0, len(paths), QUERY_BATCH_SIZE):
            self._lines(
                [
                    "nix-store",
                    "--realise",
                    "--add-root",
                    str(root_directory / f"batch-{start // QUERY_BATCH_SIZE}"),
                    *paths[start : start + QUERY_BATCH_SIZE],
                ]
            )


def locally_built_paths(signature_lines):
    built = set()
    for line in signature_lines:
        path, _, signatures = line.partition("\t")
        if "ultimate" in signatures.split():
            built.add(path.strip())
    return built


def select_retained_paths(closure, check_outputs, derivers, signature_lines):
    built = locally_built_paths(signature_lines)
    excluded = set(check_outputs)
    return sorted(
        path
        for path, deriver in zip(closure, derivers, strict=True)
        if path in built and path not in excluded and deriver != "unknown-deriver"
    )


def retain_check_dependencies(store, system, root_directory):
    check_derivations = store.check_derivations(system)
    check_outputs = store.outputs(check_derivations)
    closure = list(
        dict.fromkeys(
            path
            for path in store.closure_with_outputs(check_derivations)
            if not path.endswith(".drv")
        )
    )
    retained = select_retained_paths(
        closure, check_outputs, store.derivers(closure), store.signatures(closure)
    )
    store.add_roots(retained, root_directory)
    print(
        f"Rooted {len(retained)} locally built dependencies of "
        f"{len(check_derivations)} checks out of {len(closure)} closure paths"
    )
    return retained


if __name__ == "__main__":
    retain_check_dependencies(NixStore(sys.argv[3:]), sys.argv[1], Path(sys.argv[2]))
