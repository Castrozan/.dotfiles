import sys


def _current_fake_psutil():
    return sys.modules["psutil"]


class FakeParentProcess:
    def __init__(self, pid, name_value=None, name_exception=None):
        self.pid = pid
        self._name_value = name_value
        self._name_exception = name_exception

    def name(self):
        if self._name_exception is not None:
            raise self._name_exception
        return self._name_value


class FakeProcessWithParent:
    def __init__(self, parent_value=None, parent_exception=None):
        self._parent_value = parent_value
        self._parent_exception = parent_exception

    def parent(self):
        if self._parent_exception is not None:
            raise self._parent_exception
        return self._parent_value


def test_orphan_when_parent_is_pid_one(orphan_reaper_module):
    assert orphan_reaper_module.is_orphaned_by_parent(1, "systemd") is True


def test_orphan_when_reparented_to_user_systemd_manager(orphan_reaper_module):
    assert orphan_reaper_module.is_orphaned_by_parent(1703, "systemd") is True


def test_orphan_when_parent_missing(orphan_reaper_module):
    assert orphan_reaper_module.is_orphaned_by_parent(None, "") is True


def test_orphan_when_parent_named_init(orphan_reaper_module):
    assert orphan_reaper_module.is_orphaned_by_parent(4242, "init") is True


def test_orphan_when_reparented_to_darwin_launchd(orphan_reaper_module):
    assert orphan_reaper_module.is_orphaned_by_parent(100, "launchd") is True


def test_not_orphan_when_parent_is_live_node_client(orphan_reaper_module):
    assert orphan_reaper_module.is_orphaned_by_parent(4242, "node") is False


def test_not_orphan_when_parent_is_live_claude_client(orphan_reaper_module):
    assert orphan_reaper_module.is_orphaned_by_parent(5555, "claude") is False


def test_read_parent_identity_when_parent_lookup_raises_no_such_process(
    orphan_reaper_module,
):
    process = FakeProcessWithParent(
        parent_exception=_current_fake_psutil().NoSuchProcess()
    )
    assert orphan_reaper_module.read_parent_identity(process) == (None, "")


def test_read_parent_identity_when_parent_is_none(orphan_reaper_module):
    process = FakeProcessWithParent(parent_value=None)
    assert orphan_reaper_module.read_parent_identity(process) == (None, "")


def test_read_parent_identity_when_parent_name_raises_access_denied(
    orphan_reaper_module,
):
    parent = FakeParentProcess(
        pid=4242, name_exception=_current_fake_psutil().AccessDenied()
    )
    process = FakeProcessWithParent(parent_value=parent)
    assert orphan_reaper_module.read_parent_identity(process) == (4242, "")


def test_read_parent_identity_returns_pid_and_name_for_live_parent(
    orphan_reaper_module,
):
    parent = FakeParentProcess(pid=4242, name_value="node")
    process = FakeProcessWithParent(parent_value=parent)
    assert orphan_reaper_module.read_parent_identity(process) == (4242, "node")
