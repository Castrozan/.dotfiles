from pathlib import Path
import sys
import subprocess


def run_rebuild(environment, *arguments):
    program = """source "$TEST_REBUILD_ENTRYPOINT"
detect_backend_name() { echo "$TEST_REBUILD_PLATFORM"; }
ensure_nix_is_on_the_path() { echo nix-ready >> "$TEST_EVENTS"; }
initialize_git_submodules() { echo git-ready >> "$TEST_EVENTS"; }
nudge_clawde_agents_to_redeploy_on_continued_sessions() { echo fleet >> "$TEST_EVENTS"; }
main "$@"
"""
    return subprocess.run(
        ["bash", "-c", program, "rebuild-test", *arguments],
        env=environment,
        capture_output=True,
        text=True,
        timeout=5,
    )


def build_rebuild_boot_environment(managed_rebuild_environment, tmp_path):
    scripts = Path(__file__).resolve().parents[2] / "scripts"
    backends = tmp_path / "backends"
    backends.mkdir()
    home = tmp_path / "home"
    (home / ".dotfiles").mkdir(parents=True)
    private_entrypoint = home / "zanoni-system"
    private_entrypoint.mkdir()
    (private_entrypoint / "flake.nix").touch()
    entrypoint = tmp_path / "rebuild"
    reporter = tmp_path / "memory-reporter"
    reporter.write_text(
        f'#!/usr/bin/env bash\nexec "{sys.executable}" "{scripts}/nixos-staged-rebuild/memory_report.py" "$@"\n'
    )
    reporter.chmod(0o755)
    substitutions = {
        "@machineAlias@": "chise",
        "@backendsDirectory@": str(backends),
        "@exclusiveRunLockHelper@": managed_rebuild_environment[
            "EXCLUSIVE_RUN_LOCK_HELPER"
        ],
        "@exclusiveRunScopePython@": managed_rebuild_environment[
            "EXCLUSIVE_RUN_SCOPE_PYTHON"
        ],
        "@nixosRebuildPrefetch@": str(tmp_path / "prefetch"),
        "@nixosStagedRebuild@": str(scripts / "nixos-rebuild-guard"),
        "@memoryReporter@": str(reporter),
        "@memorySystem@": "x86_64-linux",
    }
    source = (scripts / "rebuild/rebuild").read_text()
    for placeholder, value in substitutions.items():
        source = source.replace(placeholder, value)
    entrypoint.write_text(source)
    events = tmp_path / "events"
    (backends / "nixos").write_text(
        f'''source "{scripts}/rebuild/backends/nixos"
run_privileged() {{
    echo privileged >> "{events}"
    printf '%s\\n' "$@" > "{tmp_path}/privileged-arguments"
    while [[ "$1" != "{scripts}/nixos-rebuild-guard" ]]; do
        if [[ "$1" == DOTFILES_REBUILD_WRAPPER=1 ]]; then export DOTFILES_REBUILD_WRAPPER=1; fi
        shift
    done
    shift
    "{scripts}/nixos-rebuild-guard" "$@"
}}
backend_verify_switch_landed() {{ echo verify >> "{events}"; }}
backend_after_switch() {{ echo desktop >> "{events}"; }}
'''
    )
    native = tmp_path / "native"
    native.write_text(
        f'''#!/usr/bin/env bash
[[ -f "$2" ]] || exit 1
cp "{tmp_path}/prefetch-arguments" "{tmp_path}/native-arguments"
[[ "${{TEST_NATIVE_STATUS:-0}}" == 0 ]] || exit "$TEST_NATIVE_STATUS"
case "$1" in
boot) echo staged > "{tmp_path}/next-generation" ;;
switch) echo active > "{tmp_path}/current-generation"; touch "{tmp_path}/activated" ;;
esac
'''
    )
    native.chmod(0o755)
    prefetch = tmp_path / "prefetch"
    prefetch.write_text(
        f'''#!/usr/bin/env bash
echo prefetch >> "{events}"
[[ "${{TEST_PREFETCH_STATUS:-0}}" == 0 ]] || exit "$TEST_PREFETCH_STATUS"
request="$1"
shift 2
printf '%s\\n' "$@" > "{tmp_path}/prefetch-arguments"
echo '{{}}' > "$request"
'''
    )
    prefetch.chmod(0o755)
    (tmp_path / "current-generation").write_text("previous\n")
    return {
        **managed_rebuild_environment,
        "BASH_ENV": "/dev/null",
        "HOME": str(home),
        "MACHINE_LOCAL_ENTRYPOINT_DIRECTORY": str(private_entrypoint),
        "REAL_NIXOS_REBUILD": str(native),
        "TEST_REBUILD_ENTRYPOINT": str(entrypoint),
        "TEST_REBUILD_PLATFORM": "nixos",
        "TEST_EVENTS": str(events),
    }
