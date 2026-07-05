def test_orphan_when_parent_is_pid_one(orphan_reaper_module):
    assert orphan_reaper_module.is_orphaned_by_parent(1, "systemd") is True


def test_orphan_when_reparented_to_user_systemd_manager(orphan_reaper_module):
    assert orphan_reaper_module.is_orphaned_by_parent(1703, "systemd") is True


def test_orphan_when_parent_missing(orphan_reaper_module):
    assert orphan_reaper_module.is_orphaned_by_parent(None, "") is True


def test_orphan_when_parent_named_init(orphan_reaper_module):
    assert orphan_reaper_module.is_orphaned_by_parent(4242, "init") is True


def test_not_orphan_when_parent_is_live_node_client(orphan_reaper_module):
    assert orphan_reaper_module.is_orphaned_by_parent(4242, "node") is False


def test_not_orphan_when_parent_is_live_claude_client(orphan_reaper_module):
    assert orphan_reaper_module.is_orphaned_by_parent(5555, "claude") is False
