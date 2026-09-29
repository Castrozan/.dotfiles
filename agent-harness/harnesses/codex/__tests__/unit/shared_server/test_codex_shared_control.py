import pytest

from codex_client_control import control_directory


@pytest.mark.parametrize("replacement", ["public_permissions", "symlink"])
def test_proxy_rejects_unsafe_socket_directories(tmp_path, replacement):
    directory = control_directory(tmp_path)
    assert directory.stat().st_mode & 0o777 == 0o700
    try:
        if replacement == "symlink":
            directory.rmdir()
            directory.symlink_to(tmp_path, target_is_directory=True)
        else:
            directory.chmod(0o777)
        with pytest.raises(RuntimeError, match="private and owned"):
            control_directory(tmp_path)
    finally:
        if directory.is_symlink():
            directory.unlink()
        else:
            directory.rmdir()
