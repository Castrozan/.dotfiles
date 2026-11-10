import importlib.util
import json
from pathlib import Path
import subprocess

SCRIPT = Path(__file__).resolve().parents[3] / "nix-checks/retain-check-dependencies.py"
specification = importlib.util.spec_from_file_location(
    "retain_check_dependencies", SCRIPT
)
retainer = importlib.util.module_from_spec(specification)
specification.loader.exec_module(retainer)

CHECK_DERIVATION = "/nix/store/aaaa-check-format.drv"
CHECK_OUTPUT = "/nix/store/aaaa-check-format"
BUILT_DEPENDENCY = "/nix/store/bbbb-hermes-agent-1.0.0"
SUBSTITUTED_DEPENDENCY = "/nix/store/cccc-glibc-2.42"
FLAKE_SOURCE = "/nix/store/dddd-source"


class FakeStore:
    def __init__(self):
        self.rooted = None

    def check_derivations(self, system):
        assert system == "x86_64-linux"
        return [CHECK_DERIVATION]

    def outputs(self, derivations):
        assert derivations == [CHECK_DERIVATION]
        return [CHECK_OUTPUT]

    def closure_with_outputs(self, derivations):
        return [
            CHECK_DERIVATION,
            "/nix/store/bbbb-hermes-agent-1.0.0.drv",
            CHECK_OUTPUT,
            BUILT_DEPENDENCY,
            SUBSTITUTED_DEPENDENCY,
            FLAKE_SOURCE,
            BUILT_DEPENDENCY,
        ]

    def derivers(self, paths):
        known = {
            CHECK_OUTPUT: CHECK_DERIVATION,
            BUILT_DEPENDENCY: "/nix/store/bbbb-hermes-agent-1.0.0.drv",
            SUBSTITUTED_DEPENDENCY: "/nix/store/cccc-glibc-2.42.drv",
        }
        return [known.get(path, "unknown-deriver") for path in paths]

    def signatures(self, paths):
        signed = {SUBSTITUTED_DEPENDENCY: "cache.nixos.org-1:c2lnbmF0dXJl"}
        return [f"{path}  \t{signed.get(path, 'ultimate')}" for path in paths]

    def add_roots(self, paths, root_directory):
        self.rooted = (paths, root_directory)


def test_only_locally_built_dependencies_of_the_checks_are_rooted(tmp_path, capsys):
    store = FakeStore()
    retained = retainer.retain_check_dependencies(store, "x86_64-linux", tmp_path)
    assert retained == [BUILT_DEPENDENCY]
    assert store.rooted == ([BUILT_DEPENDENCY], tmp_path)
    assert "Rooted 1 locally built dependencies of 1 checks out of 4 closure paths" in (
        capsys.readouterr().out
    )


def test_a_check_output_is_never_rooted_so_the_check_still_rebuilds():
    assert (
        retainer.select_retained_paths(
            [CHECK_OUTPUT],
            [CHECK_OUTPUT],
            [CHECK_DERIVATION],
            [f"{CHECK_OUTPUT}\tultimate"],
        )
        == []
    )


def test_a_path_signed_by_a_binary_cache_is_left_to_garbage_collection():
    assert (
        retainer.select_retained_paths(
            [SUBSTITUTED_DEPENDENCY],
            [],
            ["/nix/store/cccc-glibc-2.42.drv"],
            [f"{SUBSTITUTED_DEPENDENCY}\tcache.nixos.org-1:c2lnbmF0dXJl"],
        )
        == []
    )


def test_a_source_added_without_a_derivation_is_left_to_garbage_collection():
    assert (
        retainer.select_retained_paths(
            [FLAKE_SOURCE], [], ["unknown-deriver"], [f"{FLAKE_SOURCE}\tultimate"]
        )
        == []
    )


def test_store_queries_batch_paths_and_pass_flake_arguments(monkeypatch, tmp_path):
    commands = []

    def fake_run(command, **options):
        commands.append(command)
        assert options["check"] is True
        if command[:2] == ["nix", "eval"]:
            stdout = json.dumps([CHECK_DERIVATION])
        else:
            stdout = "\n".join(
                argument for argument in command if argument.startswith("/nix/store/")
            )
        return subprocess.CompletedProcess(command, 0, stdout=stdout)

    monkeypatch.setattr(retainer, "QUERY_BATCH_SIZE", 2)
    monkeypatch.setattr(retainer.subprocess, "run", fake_run)
    store = retainer.NixStore(
        ["--override-input", "dependencies/arr-stack", "path:/stub"]
    )
    paths = ["/nix/store/a", "/nix/store/b", "/nix/store/c"]

    assert store.check_derivations("x86_64-linux") == [CHECK_DERIVATION]
    assert commands[0][:6] == [
        "nix",
        "eval",
        "--json",
        "--override-input",
        "dependencies/arr-stack",
        "path:/stub",
    ]
    assert commands[0][6] == ".#checks.x86_64-linux"
    assert store.outputs(paths) == paths
    assert store.closure_with_outputs(paths) == paths
    assert store.derivers(paths) == paths
    assert [len(command) for command in commands[1:]] == [5, 4, 6, 5, 5, 4]

    commands.clear()
    store.signatures(paths)
    store.add_roots(paths, tmp_path / "roots")
    assert commands[0][:3] == ["nix", "path-info", "--sigs"]
    assert [command[3] for command in commands[2:]] == [
        str(tmp_path / "roots/batch-0"),
        str(tmp_path / "roots/batch-1"),
    ]
    assert (tmp_path / "roots").is_dir()
