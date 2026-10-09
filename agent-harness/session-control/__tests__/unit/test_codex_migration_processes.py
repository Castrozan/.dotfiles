import pytest

from agent_session import codex_migration_processes as processes
from codex_migration_process_fixture import inspect_runtime


def test_replacement_proves_pane_session_separate_backend_group_and_descriptors(
    process_inspection,
):
    result = inspect_runtime(process_inspection)
    assert result["session_id"] == 70
    assert result["process_groups"] == {"launcher": 30, "client": 30, "server": 31}
    assert result["births"]["server"] == {
        "start_ticks": 310,
        "state": "S",
        "parent": 30,
    }
    assert result["server_stderr"] == "pipe:[900]"
    assert result["diagnostic_sizes"] == {
        "server-stderr.log": 0,
        "server-stderr.previous.log": 0,
    }


@pytest.mark.parametrize("identifier", [30, 31, 32])
def test_detached_replacement_session_is_refused(process_inspection, identifier):
    process_inspection.sessions[identifier] = 999
    with pytest.raises(ValueError, match="session"):
        inspect_runtime(process_inspection)


@pytest.mark.parametrize("identifier, group", [(30, 999), (31, 30), (32, 32)])
def test_changed_foreground_or_backend_group_is_refused(
    process_inspection, identifier, group
):
    process_inspection.groups[identifier] = group
    with pytest.raises(ValueError, match="group|foreground"):
        inspect_runtime(process_inspection)


def test_orphaned_child_is_refused(process_inspection):
    path = process_inspection.directory / "proc/31/stat"
    path.write_text(path.read_text().replace(" S 30 ", " S 1815 "))
    with pytest.raises(ValueError, match="ownership"):
        inspect_runtime(process_inspection)


def test_changed_upstream_executable_is_refused(process_inspection):
    path = process_inspection.directory / "proc/31/exe"
    path.unlink()
    path.symlink_to(process_inspection.package["python"])
    with pytest.raises(ValueError, match="executable"):
        inspect_runtime(process_inspection)


def test_backend_stderr_must_remain_a_pipe(process_inspection):
    process_inspection.descriptors["/proc/31/fd/2"] = "/dev/pts/999"
    with pytest.raises(ValueError, match="pipe"):
        inspect_runtime(process_inspection)


def test_client_descriptors_must_share_the_terminal(process_inspection):
    process_inspection.descriptors["/proc/32/fd/0"] = "pipe:[900]"
    with pytest.raises(ValueError, match="descriptors"):
        inspect_runtime(process_inspection)


def test_diagnostic_limit_is_enforced(process_inspection):
    with (process_inspection.socket_directory / "server-stderr.log").open(
        "wb"
    ) as stream:
        stream.truncate(1024 * 1024 + 1)
    with pytest.raises(ValueError, match="1 MiB"):
        inspect_runtime(process_inspection)


def test_changed_birth_during_inspection_is_refused(process_inspection, monkeypatch):
    original = processes.process_birth
    inspections = 0

    def changing_birth(identifier):
        nonlocal inspections
        inspections += 1
        birth = original(identifier)
        return {**birth, "start_ticks": 999} if inspections > 3 else birth

    monkeypatch.setattr(processes, "process_birth", changing_birth)
    with pytest.raises(ValueError, match="birth changed"):
        inspect_runtime(process_inspection)
