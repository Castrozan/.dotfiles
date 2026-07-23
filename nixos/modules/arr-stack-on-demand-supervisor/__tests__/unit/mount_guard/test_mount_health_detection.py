import mount_health_guard


def test_data_mount_is_healthy_true_only_for_live_mountpoint(monkeypatch):
    monkeypatch.setattr(mount_health_guard.os.path, "ismount", lambda path: True)
    monkeypatch.setattr(mount_health_guard.os, "statvfs", lambda path: object())
    monkeypatch.setattr(mount_health_guard.os, "listdir", lambda path: [])
    assert mount_health_guard.data_mount_is_healthy("/data") is True


def test_data_mount_unhealthy_when_not_a_mountpoint(monkeypatch):
    monkeypatch.setattr(mount_health_guard.os.path, "ismount", lambda path: False)
    assert mount_health_guard.data_mount_is_healthy("/data") is False


def test_data_mount_unhealthy_when_stale_mount_raises_oserror(monkeypatch):
    monkeypatch.setattr(mount_health_guard.os.path, "ismount", lambda path: True)

    def raise_io(path):
        raise OSError("stale mount")

    monkeypatch.setattr(mount_health_guard.os, "statvfs", raise_io)
    assert mount_health_guard.data_mount_is_healthy("/data") is False
