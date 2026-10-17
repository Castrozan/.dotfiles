import sys
import tempfile
from pathlib import Path

from session import BtopSession, MemoryTotals
from system_process_group import verify_system_process_group


def verify(binary):
    with tempfile.TemporaryDirectory(prefix="btop-memory-totals-") as directory:
        session = BtopSession(binary, Path(directory))
        try:
            visible, all_processes, system_used = session.read_summary()
            assert 0 < visible <= all_processes
            assert 0 < system_used <= 100
            session.send(b"f")
            session.send(b"z")
            session.send(b"z")
            session.send(b"z")
            session.send(b"z")
            session.send(b"z")
            session.send(b"\n")
            filtered = session.read_summary()
            assert filtered == MemoryTotals(0.0, all_processes, system_used), filtered
            session.send(b"\x1b[3~")
            restored = session.read_summary()
            assert restored == MemoryTotals(visible, all_processes, system_used), (
                restored
            )
            session.send(b"e")
            tree = session.read_summary()
            assert 0 <= tree.visible_process_percent
            assert 0 < tree.all_process_percent
            assert 0 < tree.system_used_percent <= 100
            session.send(b"f")
            for character in b"zzzzz":
                session.send(bytes([character]))
            session.send(b"\n")
            filtered_tree = session.read_summary()
            expected_tree = MemoryTotals(
                0.0, tree.all_process_percent, tree.system_used_percent
            )
            assert filtered_tree == expected_tree, (filtered_tree, expected_tree)
            session.send(b"2")
            hidden_memory = session.read_summary()
            assert hidden_memory.visible_process_percent == 0.0
            assert hidden_memory.system_used_percent > 0
        finally:
            session.close()
        verify_system_process_group(binary, Path(directory))
        session = BtopSession(binary, Path(directory), shown_boxes="proc", columns=44)
        try:
            narrow = session.read_summary()
            assert 0 < narrow.visible_process_percent <= narrow.all_process_percent
            assert 0 < narrow.system_used_percent <= 100
        finally:
            session.close()
    print(
        "Verified visible, global, filtered, tree, hidden-panel, and narrow memory totals"
    )


if __name__ == "__main__":
    verify(sys.argv[1])
