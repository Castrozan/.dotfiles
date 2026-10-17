import re
from pathlib import Path

from session import BtopSession


def verify_system_process_group(binary, directory):
    if not Path("/proc").is_dir():
        return
    service_pid = None
    root_application_pid = None
    for process in Path("/proc").iterdir():
        if not process.name.isdigit():
            continue
        try:
            name = (process / "comm").read_text().strip()
            group = (process / "cgroup").read_text()
            status = (process / "status").read_text()
        except OSError:
            continue
        if name in {
            "systemd-journal",
            "systemd-logind",
            "dbus-daemon",
        } and group.startswith("0::/system.slice/"):
            service_pid = process.name
        if name == "python" and re.search(r"(?m)^Uid:\s+0\s", status):
            if "0::/media.slice/" in group:
                root_application_pid = process.name
    if service_pid is None:
        print("Service-group UI fixture unavailable in this process namespace")
        return
    session = BtopSession(binary, directory, shown_boxes="proc")
    try:
        initial = session.read_summary()
        session.send(b"f")
        for character in f"!^{service_pid}$".encode():
            session.send(bytes([character]))
        session.send(b"\n")
        collapsed = session.read_summary()
        assert "System [+]" in session.plain_output, session.plain_output
        assert collapsed.all_process_percent == initial.all_process_percent
        session.send(b"\x1b[B")
        session.read_summary()
        session.send(b"\n")
        expanded = session.read_summary()
        assert "System [-]" in session.plain_output, session.plain_output
        assert service_pid in session.plain_output
        assert expanded[:2] == collapsed[:2], (expanded, collapsed)
        assert 0 < expanded.system_used_percent <= 100
        for key in (b"t", b"k", b"s"):
            session.send(key)
            session.send(b"r")
            session.read_summary()
            assert "System [-]" in session.plain_output
        session.send(b" ")
        session.read_summary()
        assert "System [+]" in session.plain_output
        session.send(b"\x1b[<0;20;3M")
        session.read_summary()
        assert "System [-]" in session.plain_output
        session.send(b"\x1b[<0;20;3M")
        session.read_summary()
        assert "System [+]" in session.plain_output
        if root_application_pid is not None:
            session.send(b"\x1b[3~")
            session.read_summary()
            session.send(b"f")
            for character in f"!^{root_application_pid}$".encode():
                session.send(bytes([character]))
            session.send(b"\n")
            application = session.read_summary()
            assert "System [+]" not in session.plain_output
            assert root_application_pid in session.plain_output
            assert application.all_process_percent == initial.all_process_percent
    finally:
        session.close()
    print(
        "Verified service grouping, expansion, process controls, and root application separation"
    )
